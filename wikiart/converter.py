"""WikiArt Metadata Converter.

License: MIT License (c) 2016

"""
import os

from . import settings
from .utils import load_json, load_painters_in_disk, log


class WikiArtMetadataConverter:
  """WikiArt Metadata Converter.

    Converts json files downloaded from WikiArt to a more more friendly
    data-set notation.
    """

  def __init__(self, override=False):
    self.override = override

    self.painters = None
    self.painting_groups = None

  def prepare(self):
    base_folder = settings.BASE_FOLDER
    os.makedirs(base_folder, exist_ok=True)

    log.info('Loading artists...', end=' ', flush=True)
    self.painters = load_painters_in_disk()
    log.write('done.')

    log.info('Loading paintings...', flush=True)
    self.painting_groups = []

    for p in self.painters:
      pf = os.path.join(base_folder, 'meta', p['url'] + '.json')

      try:
        self.painting_groups.append(load_json(pf))
      except IOError as error:
        log.warning(str(error))

    log.write('done.')
    return self

  def generate_images_data_set(self):
    log.info('generating images data set', end=' ', flush=True)

    path = os.path.join(settings.BASE_FOLDER, 'wikiart.data')
    if os.path.exists(path) and not self.override:
      log.write('(s)')
      return self

    paintings = sum(self.painting_groups, [])

    with open(path, 'w', encoding='utf-8') as f:
      f.write(settings.PAINTINGS_HEADER)
      f.writelines(self.paintings_as_lines(paintings))

    log.write('(d)')
    return self

  def generate_labels(self):
    log.write('generating labels', end=' ', flush=True)

    path = os.path.join(settings.BASE_FOLDER, 'labels.data')
    if os.path.exists(path) and not self.override:
      log.write('(s)')
      return self

    with open(path, 'w', encoding='utf-8') as file:
      file.write(settings.LABELS_HEADER)
      file.writelines(self.artists_as_lines(self.painters))

    log.write('(d)')
    return self

  @classmethod
  def paintings_as_lines(cls, paintings):
    return cls.convert_to_lines(paintings, settings.PAINTING_ATTRIBUTES)

  @classmethod
  def artists_as_lines(cls, artists):
    return cls.convert_to_lines(artists, settings.ARTIST_ATTRIBUTES)

  @classmethod
  def convert_to_lines(cls, iterable, attributes):
    return [
      ','.join(
        '' if item.get(attribute, None) is None else '"%s"' %
        item[attribute].replace('\n', ' ').rstrip()
        if isinstance(item[attribute], str) else str(item[attribute])
        for attribute in attributes
      ) + '\n'
      for item in iterable
    ]
