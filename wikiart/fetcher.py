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
from urllib.parse import unquote

import requests
# from tqdm import tqdm

# https://stackoverflow.com/questions/65873428/python-requests-module-get-method-handling-pagination-token-in-params-containin
from urllib.parse import unquote

from . import base, settings
from .base import Logger


class WikiArtFetcher:
  """WikiArt Fetcher.

    Fetcher for data in WikiArt.org.
    """

  def __init__(self, commit=True, override=False, padder=None):
    self.commit = commit
    self.override = override

    self.request_padding = padder or base.RequestPadder()

    self.artists = None
    self.painting_groups = None

  def prepare(self):
    """Prepare for data extraction."""
    os.makedirs(settings.BASE_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(settings.BASE_FOLDER, 'meta'), exist_ok=True)
    os.makedirs(os.path.join(settings.BASE_FOLDER, 'images'), exist_ok=True)

    self.authenticate()

    return self

  def check(self, only='all'):
    """Check if fetched data is intact."""
    Logger.info('Checking downloaded data...')

    base_dir = settings.BASE_FOLDER
    meta_dir = os.path.join(base_dir, 'meta')
    imgs_dir = os.path.join(base_dir, 'images')

    if only in ('artists', 'all'):
      # Check for artists file.
      if not os.path.exists(os.path.join(meta_dir, 'artists.json')):
        Logger.warning('artists.json is missing.')

    if only in ('paintings', 'all'):
      for artist in self.artists:
        filename = os.path.join(meta_dir, artist['url'] + '.json')
        if not os.path.exists(filename):
          Logger.warning('%s\'s paintings file is missing.' % artist['url'])

      # Check for paintings copies.
      for group in self.painting_groups:
        for painting in group:
          filename = painting['id'] + settings.SAVE_IMAGES_IN_FORMAT
          filename = os.path.join(imgs_dir, filename)

          if not os.path.exists(filename):
            Logger.warning('painting %s is missing.' % painting['id'])

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

    self.sessionKey = data['SessionKey']
    return self

  def fetch_all(self):
    """Fetch Everything from WikiArt."""
    return (self.fetch_artists().fetch_all_paintings().copy_everything())

  def fetch_artists(self):
    """Retrieve Artists from WikiArt.

        References:

        - https://docs.google.com/document/d/1T926unU7mx9Blmx3c8UE0UQTnO3MrDbXTGYVerVQFDU/edit#heading=h.cqj7koncgwqn

          Api methods with pagination:
            UpdatedArtists, DeletedArtists, ArtistsByDictionary,
            UpdatedDictionaries, DeletedDictionaries, DictionariesByGroup,
            MostViewedPaintings, PaintingsByArtist, PaintingSearch
          Response includes 2 additional fields - paginationToken and hasMore
          Artists and paintings each have unique id's: where appropriate replace 'ContentId' with 'id'
        """
    Logger.write('Fetching list of artists:', flush=True)

    path = os.path.join(settings.BASE_FOLDER, 'meta', 'artists.json')
    if os.path.exists(path) and not self.override:
      with open(path, encoding='utf-8') as f:
        self.artists = json.load(f)

      Logger.info('skipped')
      return self

    elapsed = time.time()
    self.artists = []
    params = {'SessionKey': self.sessionKey}

    try:
      self.artists = []

      while True:
        url = '/'.join((settings.BASE_URL, 'UpdatedArtists'))
        response = requests.get(url, params, timeout=settings.METADATA_REQUEST_TIMEOUT)

        response.raise_for_status()
        page = response.json()

        artists = page['data']
        self.artists += artists

        print(f'{len(self.artists)}...', end='')

        if not page['hasMore']:
          break

        params['paginationToken'] = unquote(page['paginationToken'])

      print(f'\nTotal: {len(self.artists)}')

      if self.commit:
        print(f'  caching painters list in `{path}`.')

        with open(path, 'w', encoding='utf-8') as f:
          json.dump(self.artists, f, indent=4, ensure_ascii=False)

      Logger.write('%d Artists (%.2f sec)' % (len(self.artists), (time.time() - elapsed)))

    except Exception as error:
      Logger.write('Error %s' % str(error))

    return self

  def fetch_all_paintings(self):
    """Fetch Paintings Metadata for Every Artist"""
    Logger.write('\nFetching painting data of every artist:')
    if not self.artists:
      raise RuntimeError('No artists defined. Cannot continue.')

    self.painting_groups = []
    show_progress_at = max(1, int(.1 * len(self.artists)))

    n_artists = 0

    # Retrieve paintings' metadata for every artist.
    for i, artist in enumerate(self.artists):
      self.painting_groups.append(self.fetch_paintings(artist))

      if i % show_progress_at == 0:
        Logger.info('%i%% done' % (100 * (i + 1) // len(self.artists)))
      n_artists += 1

    Logger.write(n_artists, end=' ', flush=True)

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

    Logger.write('|- %s' % artist['artistName'], end='', flush=True)
    elapsed = time.time()

    artist_id = artist['id']

    meta_folder = os.path.join(settings.BASE_FOLDER, 'meta')
    filename = os.path.join(meta_folder, artist['url'] + '.json')

    if os.path.exists(filename) and not self.override:
      with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
      Logger.write(' (s)')
      return data

    params = {'SessionKey': self.sessionKey, 'id': artist_id}

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
                'SessionKey': self.sessionKey,
                'id': painting_id,
                'imageFormat': 'HD'
              },
              timeout=settings.METADATA_REQUEST_TIMEOUT
            )

          if response.ok:
            painting.update(response.json())

          group_paintings.append(painting)

          Logger.write('.', end='', flush=True)

        if not page['hasMore']:
          break

        params['paginationToken'] = unquote(page['paginationToken'])

      if self.commit:
        with open(filename, 'w', encoding='utf-8') as f:
          json.dump(group_paintings, f, indent=4, ensure_ascii=False)

      Logger.write(
        '%d Paintings (%.2f sec)' % (len(group_paintings), (time.time() - elapsed))
      )

      return group_paintings

    except (IOError, urllib.error.HTTPError) as e:
      Logger.write(' Failed (%s)' % str(e))
      return []

  def copy_everything(self):
    """Download A Copy of Every Single Painting."""
    Logger.write('\nFetching painting images:')
    if not self.painting_groups:
      raise RuntimeError('Painting groups not found. Cannot continue.')

    show_progress_at = max(1, int(.1 * len(self.painting_groups)))

    for i, group in enumerate(self.painting_groups):
      for painting in group:
        self.download_hard_copy(painting)
        Logger.write('.', end='', flush=True)

        Logger.write(n_paintings, end=' ', flush=True)

        n_paintings += 1

      if i % show_progress_at == 0:
        Logger.info('%i%% done' % (100 * (i + 1) // len(self.painting_groups)))

    return self

  def download_hard_copy(self, painting):
    """Download A Copy of A Painting."""
    Logger.write('|- %s' % painting.get('url', painting.get('id')), end=' ', flush=True)
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
      Logger.write('(s)')
      return self

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
      with self.request_padding:
        response = requests.get(
          url,
          params={'SessionKey': self.sessionKey},
          stream=True,
          timeout=settings.PAINTINGS_REQUEST_TIMEOUT
        )

      response.raise_for_status()

      with open(filename, 'wb') as f:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, f)

      Logger.write('(%.2f sec)' % (time.time() - elapsed))

    except Exception as error:
      Logger.write('%s' % str(error))
      if os.path.exists(filename):
        os.remove(filename)

    return self
