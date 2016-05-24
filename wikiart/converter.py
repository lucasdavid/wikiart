"""WikiArt Metadata Converter.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""
import json
import os

from . import settings
from .base import Logger


class WikiArtMetadataConverter:
    """WikiArt Metadata Converter.

    Converts json files downloaded from WikiArt to a more more friendly
    data-set notation.
    """

    def __init__(self, override=False):
        self.override = override

        self.artists = None
        self.painting_groups = None

    def prepare(self):
        base_folder = os.path.join(settings.BASE_FOLDER,
                                   settings.INSTANCE_IDENTIFIER)
        if not os.path.exists(base_folder):
            os.mkdir(base_folder)

        Logger.info('Loading artists...', end=' ', flush=True)
        with open(os.path.join(base_folder, 'meta', 'artists.json'),
                  encoding='utf-8') as f:
            self.artists = json.load(f)
        Logger.write('Done.')

        Logger.info('Loading paintings...', flush=True)
        self.painting_groups = []

        for artist in self.artists:
            try:
                with open(os.path.join(base_folder, 'meta',
                                       artist['url'] + '.json'),
                          encoding='utf-8') as f:
                    self.painting_groups.append(json.load(f))

            except IOError as error:
                Logger.error('Failed: %s' % str(error))

        Logger.info('Done.')
        return self

    def generate_images_data_set(self):
        Logger.info('Generating images data set...', end=' ', flush=True)

        path = os.path.join(settings.BASE_FOLDER,
                            settings.INSTANCE_IDENTIFIER,
                            'wikiart.data')
        if os.path.exists(path) and not self.override:
            Logger.write('Skipped')
            return self

        paintings = sum(self.painting_groups, [])

        with open(path, 'w', encoding='utf-8') as f:
            f.write(settings.LABELS_HEADER)
            f.writelines(self.paintings_as_lines(paintings))

        Logger.write('Done')
        return self

    def generate_labels(self):
        Logger.info('Generating labels...', end=' ', flush=True)

        path = os.path.join(settings.BASE_FOLDER,
                            settings.INSTANCE_IDENTIFIER,
                            'labels.data')
        if os.path.exists(path) and not self.override:
            Logger.write('Skipped')
            return self

        with open(path, 'w', encoding='utf-8') as file:
            file.write(settings.LABELS_HEADER)
            file.writelines(self.artists_as_lines(self.artists))

        Logger.write('Done')
        return self

    @classmethod
    def paintings_as_lines(cls, paintings):
        return cls.convert_to_lines(paintings, settings.PAINTING_ATTRIBUTES)

    @classmethod
    def artists_as_lines(cls, artists):
        return cls.convert_to_lines(artists, settings.ARTIST_ATTRIBUTES)

    @classmethod
    def convert_to_lines(cls, iterable, attributes):
        return [','.join(str(item[attribute] or '')
                         for attribute in attributes) + '\n'
                for item in iterable]
