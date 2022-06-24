"""WikiArt Retriever.

License: MIT License (c) 2016

"""
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime
# https://stackoverflow.com/questions/65873428/python-requests-module-get-method-handling-pagination-token-in-params-containin
from urllib.parse import unquote

import requests

from . import base, settings
from .base import log


def load_json(file, encoding='utf-8'):
  with open(file, encoding=encoding) as f:
    return json.load(f)


def save_json(data, file, encoding='utf-8'):
  with open(file, 'w', encoding=encoding) as f:
    json.dump(data, f, indent=4, ensure_ascii=False)


class WikiArtFetcher:
  """WikiArt Fetcher.

    Fetcher for data in WikiArt.org.
    """

  def __init__(self, override=False, padder=None):
    self.override = override
    self.request_padding = padder or base.RequestPadder()

    self.session_key = None
    self.artists = None
    self.painting_groups = None

  def prepare(self):
    """Prepare for data extraction."""
    os.makedirs(settings.BASE_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(settings.BASE_FOLDER, 'meta', 'painters'), exist_ok=True)
    os.makedirs(os.path.join(settings.BASE_FOLDER, 'images'), exist_ok=True)

    self.authenticate()

    return self

  def check(self, only='all'):
    """Check if fetched data is intact."""
    log.info('Checking downloaded data...')

    base_dir = settings.BASE_FOLDER
    meta_dir = os.path.join(base_dir, 'meta')
    imgs_dir = os.path.join(base_dir, 'images')

    if only in ('artists', 'all'):
      # Check for artists file.
      if not os.path.exists(os.path.join(meta_dir, 'painters.json')):
        log.warning('painters.json is missing.')

    if only in ('paintings', 'all'):
      for artist in self.artists:
        filename = os.path.join(meta_dir, artist['url'] + '.json')
        if not os.path.exists(filename):
          log.warning('%s\'s paintings file is missing.' % artist['url'])

      # Check for paintings copies.
      for group in self.painting_groups:
        for painting in group:
          filename = painting['id'] + settings.SAVE_IMAGES_IN_FORMAT
          filename = os.path.join(imgs_dir, filename)

          if not os.path.exists(filename):
            log.warning('painting %s is missing.' % painting['id'])

    return self

  def authenticate(self):
    """fetch a session key from WikiArt"""
    """
        API Authentication
        To add authentication, you need to
        1. Obtain your api key/secret https://www.wikiart.org/en/App/GetApi
        2. Create session when your application starts:
        https://www.wikiart.org/en/Api/2/login?accessCode=[accessCode]&secretCode=[secretcode]
        3. Add session key to your request url, e.g. &authSessionKey=sessionKey
        """

    do_auth = input(
      'Want to authenticate? You will be asked for your credentials (Y/n): '
    )
    if do_auth and do_auth.lower() not in ('yes', 'y'):
      return self

    params = {}
    params['accessCode'] = input(
      'Please enter the Access code from https://www.wikiart.org/en/App/GetApi/GetKeys: '
    )
    params['secretCode'] = input("Enter the Secret code: ")

    # url = 'https://www.wikiart.org/en/Api/2/login'
    url = '/'.join((settings.BASE_URL, 'login'))
    response = requests.get(url, params=params, timeout=settings.METADATA_REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    self.session_key = data['SessionKey']
    return self

  def fetch_all(self):
    """Fetch Everything from WikiArt."""
    return (self.fetch_artists().fetch_all_paintings().copy_everything())

  def fetch_artists(self):
    log.write('Fetching list of artists:', flush=True)

    base_dir = settings.BASE_FOLDER
    painters_dir = os.path.join(base_dir, 'meta', 'painters')
    context_path = os.path.join(base_dir, '_context.json')
    painters_path = os.path.join(base_dir, 'meta', 'painters.json')

    url = '/'.join((settings.BASE_URL, 'UpdatedArtists'))
    params = {}
    elapsed = time.time()
    interrupted = False
    last_request_at = None
    self.artists = []

    # Restore context.
    self.artists = [
      load_json(os.path.join(painters_dir, p)) for p in os.listdir(painters_dir)
    ]
    if len(self.artists):
      log.info(f'{len(self.artists)} locally cached painters were loaded', flush=True)

    context = load_json(context_path) if os.path.exists(context_path) else {}
    request_id = context.get('requestId', 0)
    if self.session_key:
      params['SessionKey'] = self.session_key
    if context.get('hasMore'):
      params['paginationToken'] = unquote(params['paginationToken'])
    if context.get('fromDate'):
      params['fromDate'] = context['fromDate']

    while not interrupted:
      try:
        last_request_at = int(datetime.utcnow().timestamp() * 1000)
        response = requests.get(url, params, timeout=settings.METADATA_REQUEST_TIMEOUT)
        response.raise_for_status()
        page = response.json()
      except Exception as error:
        log.write('Error %s' % str(error))
        interrupted = True
        break

      artists = page['data']
      save_json(artists, os.path.join(painters_dir, f'{request_id}.json'))
      
      context.update(
        requestId=request_id,
        hasMore=page.get('hasMore'),
        paginationToken=page.get('paginationToken'),
      )
      save_json(context, context_path)

      request_id += 1
      self.artists += artists
      log.write(f'{len(self.artists)}...', end='', flush=True)

      if not page['hasMore']:
        break

      params['paginationToken'] = unquote(page['paginationToken'])

    log.info(f'\nTotal: {len(self.artists)}')

    # Save updated artists metadata.
    log.info(f'  caching painters list in `{painters_path}`.')
    save_json(self.artists, painters_path)

    # Save request context.
    if not interrupted:
      context['fromDate'] = last_request_at
    save_json(context, context_path)
    log.write('%d painters (%.2f sec)' % (len(self.artists), (time.time() - elapsed)))
    
    return self

  def fetch_all_paintings(self):
    """Fetch Paintings Metadata for Every Artist"""
    log.write('\nFetching painting data of every artist:')
    if not self.artists:
      raise RuntimeError('No artists defined. Cannot continue.')

    self.painting_groups = []
    show_progress_at = max(1, int(.1 * len(self.artists)))

    # Retrieve paintings' metadata for every artist.
    for i, artist in enumerate(self.artists):
      self.painting_groups.append(self.fetch_paintings(artist))

      if i % show_progress_at == 0:
        log.info('%i%% done' % (100 * (i + 1) // len(self.artists)))

    return self

  def fetch_paintings(self, artist):
    """Retrieve and Save Paintings Info from WikiArt.

        References:

        - https://docs.google.com/document/d/1T926unU7mx9Blmx3c8UE0UQTnO3MrDbXTGYVerVQFDU/edit#heading=h.cqj7koncgwqn
          Api methods with pagination:
            UpdatedArtists, DeletedArtists, ArtistsByDictionary,
            UpdatedDictionaries, DeletedDictionaries, DictionariesByGroup,
            MostViewedPaintings, PaintingsByArtist, PaintingSearch
          Response includes 2 additional fields - paginationToken and hasMore
          Artists and paintings each have unique id's.
        """

    log.write('|- %s' % artist['artistName'], end='', flush=True)
    elapsed = time.time()

    artist_id = artist['id']

    meta_folder = os.path.join(settings.BASE_FOLDER, 'meta')
    filename = os.path.join(meta_folder, artist['url'] + '.json')

    if os.path.exists(filename) and not self.override:
      log.write(' (s)')
      return load_json(filename)

    params = {'SessionKey': self.session_key, 'id': artist_id}

    try:
      group_paintings = []

      while True:
        url = '/'.join((settings.BASE_URL, 'PaintingsByArtist'))
        response = requests.get(
          url, params=params, timeout=settings.METADATA_REQUEST_TIMEOUT
        )

        response.raise_for_status()
        page = response.json()
        paintings = page['data']

        for painting in paintings:
          painting_id = painting['id']

          with self.request_padding:
            response = requests.get(
              '/'.join((settings.BASE_URL, 'Painting')),
              params={
                'SessionKey': self.session_key,
                'id': painting_id,
                'imageFormat': 'HD'
              },
              timeout=settings.METADATA_REQUEST_TIMEOUT
            )

          if response.ok:
            painting.update(response.json())

          group_paintings.append(painting)
          log.write('.', end='', flush=True)

        if not page['hasMore']:
          break

        params['paginationToken'] = unquote(page['paginationToken'])

      save_json(group_paintings, filename)
      log.write(f'{len(group_paintings)} paintings ({time.time() - elapsed:.2f} sec)')

      return group_paintings

    except (IOError, urllib.error.HTTPError) as e:
      log.write(' Failed (%s)' % str(e))
      return []

  def copy_everything(self):
    """Download A Copy of Every Single Painting."""
    log.write('\nFetching painting images:')
    if not self.painting_groups:
      raise RuntimeError('Painting groups not found. Cannot continue.')

    show_progress_at = max(1, int(.1 * len(self.painting_groups)))

    for i, group in enumerate(self.painting_groups):
      for painting in group:
        self.download_hard_copy(painting)
        log.write('.', end='', flush=True)

      if i % show_progress_at == 0:
        log.info('%i%% done' % (100 * (i + 1) // len(self.painting_groups)))

    return self

  def download_hard_copy(self, painting):
    """Download A Copy of A Painting."""
    log.write('   %s' % painting.get('url', painting.get('id')), end=' ', flush=True)
    elapsed = time.time()

    url = painting['image']
    url = re.sub(r'(?i)!large.jpg', '', url)
    filename = os.path.join(
      settings.BASE_FOLDER, 'images', painting['id'] + settings.SAVE_IMAGES_IN_FORMAT
    )
    filename = os.path.join(
      settings.BASE_FOLDER, 'images', painting['id'] + settings.SAVE_IMAGES_IN_FORMAT
    )

    if os.path.exists(filename) and not self.override:
      log.write('(s)')
      return self

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
      with self.request_padding:
        response = requests.get(
          url,
          params={'SessionKey': self.session_key},
          stream=True,
          timeout=settings.PAINTINGS_REQUEST_TIMEOUT
        )

      response.raise_for_status()

      with open(filename, 'wb') as f:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, f)

      log.write('(%.2f sec)' % (time.time() - elapsed))

    except Exception as error:
      log.write(str(error))
      if os.path.exists(filename):
        os.remove(filename)

    return self
