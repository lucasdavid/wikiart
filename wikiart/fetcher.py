"""WikiArt Retriever.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""
import json
import os
import shutil
import time
import urllib.error
import urllib.request

import requests

from . import settings, base
from .base import Logger


class WikiArtFetcher:
    """WikiArt Fetcher.

    Fetcher for data in WikiArt.org.
    """

    def __init__(self, commit=True, override=False, padder=None):
        self.commit = commit
        self.override = override

        self.padder = padder or base.RequestPadder()

        self.artists = None
        self.painting_groups = None

    def prepare(self):
        """Prepare for data extraction."""
        os.makedirs(settings.BASE_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(settings.BASE_FOLDER, 'meta'), exist_ok=True)
        os.makedirs(os.path.join(settings.BASE_FOLDER, 'images'), exist_ok=True)
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
                    Logger.warning('%s\'s paintings file is missing.'
                                   % artist['url'])

            # Check for paintings copies.
            for group in self.painting_groups:
                for painting in group:
                    filename = os.path.join(imgs_dir,
                                            str(painting['contentId']) +
                                            settings.SAVE_IMAGES_IN_FORMAT)
                    if not os.path.exists(filename):
                        Logger.warning('painting %i is missing.'
                                       % painting['contentId'])

        return self

    def getauthentication(self):
        """fetch a session key from WikiArt"""
        params = {}
        params['accessCode'] = input('Please enter the Access code from https://www.wikiart.org/en/App/GetApi :')
        params['secretCode'] = input("Enter the Secret code :")
        url = 'https://www.wikiart.org/en/Api/2/login'

        try:
            response = requests.get(url,
                                   params=params,
                                   timeout=settings.METADATA_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data['SessionKey']

        except Exception as error:
            Logger.write('Error %s' % str(error))

    def fetch_all(self):
        """Fetch Everything from WikiArt."""
        return (self.fetch_artists()
                    .fetch_all_paintings()
                    .copy_everything())

    def fetch_artists(self):
        """Retrieve Artists from WikiArt."""
        Logger.info('Fetching artists...', end=' ', flush=True)

        path = os.path.join(settings.BASE_FOLDER, 'meta', 'artists.json')
        if os.path.exists(path) and not self.override:
            with open(path, encoding='utf-8') as f:
                self.artists = json.load(f)

            Logger.info('skipped')
            return self

        elapsed = time.time()

        try:
            url = '/'.join((settings.BASE_URL, 'Artist/AlphabetJson'))
            params = {'v' : 'new', 'inPublicDomain' : 'true'}
            response = requests.get(url,
                                    timeout=settings.METADATA_REQUEST_TIMEOUT,
                                    params=params)
            response.raise_for_status()
            self.artists = response.json()

            if self.commit:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.artists, f, indent=4, ensure_ascii=False)

            Logger.write('Done (%.2f sec)' % (time.time() - elapsed))

        except Exception as error:
            Logger.write('Error %s' % str(error))

        return self

    def fetch_all_paintings(self):
        """Fetch Paintings Metadata for Every Artist"""
        Logger.write('\nFetching paintings for every artist:')
        if not self.artists:
            raise RuntimeError('No artists defined. Cannot continue.')

        self.painting_groups = []
        show_progress_at = max(1, int(.1 * len(self.artists)))

        # Retrieve paintings' metadata for every artist.
        for i, artist in enumerate(self.artists):
            self.painting_groups.append(self.fetch_paintings(artist))

            if i % show_progress_at == 0:
                Logger.info('%i%% done' % (100 * (i + 1) // len(self.artists)))
        return self

    def fetch_paintings(self, artist):
        """Retrieve and Save Paintings Info from WikiArt.

        :param artist: dict, artist who should have their paintings retrieved.
        """
        Logger.write('|- %s\'s paintings'
                     % artist['artistName'], end='', flush=True)
        elapsed = time.time()

        meta_folder = os.path.join(settings.BASE_FOLDER, 'meta')
        url = '/'.join((settings.BASE_URL, 'Painting', 'PaintingsByArtist'))
        params = {'artistUrl': artist['url'], 'json': 2}
        filename = os.path.join(meta_folder, artist['url'] + '.json')

        if os.path.exists(filename) and not self.override:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            Logger.write(' (s)')
            return data

        try:
            response = requests.get(
                url, params=params,
                timeout=settings.METADATA_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            for painting in data:
                # We have some info about the images,
                # but we're also after their details.
                url = '/'.join((settings.BASE_URL, 'Painting', 'ImageJson',
                                str(painting['contentId'])))

                self.padder.request_start()
                response = requests.get(
                    url, timeout=settings.METADATA_REQUEST_TIMEOUT)
                self.padder.request_finished()

                if response.ok:
                    # Update paintings with its details.
                    painting.update(response.json())

                Logger.write('.', end='', flush=True)

            if self.commit:
                # Save the json file with images details.
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

            Logger.write(' Done (%.2f sec)' % (time.time() - elapsed))
            return data

        except (IOError, urllib.error.HTTPError) as e:
            Logger.write(' Failed (%s)' % str(e))
            return []

    def copy_everything(self):
        """Download A Copy of Every Single Painting."""
        Logger.write('\nCopying paintings:')
        if not self.painting_groups:
            raise RuntimeError('Painting groups not found. Cannot continue.')

        show_progress_at = max(1, int(.1 * len(self.painting_groups)))

        # Retrieve copies of every artist's painting.
        for i, group in enumerate(self.painting_groups):
            for painting in group:
                self.download_hard_copy(painting)

            if i % show_progress_at == 0:
                Logger.info('%i%% done' % (100 * (i + 1) // len(self.painting_groups)))

        return self

    def download_hard_copy(self, painting):
        """Download A Copy of A Painting."""
        Logger.write('|- %s' % painting.get('url', painting.get('contentId')),
                     end=' ', flush=True)
        elapsed = time.time()
        url = painting['image']
        # Remove label "!Large.jpg".
        url = ''.join(url.split('!')[:-1])
        filename = os.path.join(settings.BASE_FOLDER,
                                'images',
                                painting['artistUrl'],
                                str(painting['completitionYear']) if painting['completitionYear'] else 'unknown-year',
                                str(painting['contentId']) +
                                settings.SAVE_IMAGES_IN_FORMAT)

        if os.path.exists(filename) and not self.override:
            Logger.write('(s)')
            return self

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        try:
            # Save image.
            self.padder.request_start()
            response = requests.get(url, stream=True,
                                    timeout=settings.PAINTINGS_REQUEST_TIMEOUT)
            self.padder.request_finished()

            response.raise_for_status()

            with open(filename, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)

            Logger.write('(%.2f sec)' % (time.time() - elapsed))

        except Exception as error:
            Logger.write('%s' % str(error))
            if os.path.exists(filename): os.remove(filename)

        return self
