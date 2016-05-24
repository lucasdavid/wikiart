"""Retrieve art info in WikiArt.

Author: Lucas David
License: MIT License (c) 2016

"""
import json
import os
import time
import urllib.request

import requests

from wikiart import settings


def prepare():
    """Prepare report folder structure."""
    instance = os.path.join(settings.BASE_FOLDER, settings.INSTANCE_IDENTIFIER)
    if not os.path.exists(instance):
        os.mkdir(instance)

    images = os.path.join(instance, 'images')
    if not os.path.exists(images):
        os.mkdir(images)


def retrieve_and_save_authors():
    """Retrieve and Save Authors from WikiArt.

    :return: list, authors retrieved.
    """
    print('Retrieving authors...', end=' ', flush=True)
    elapsed = time.time()

    response = requests.get(
        '/'.join((settings.BASE_URL, 'Artist/AlphabetJson')))
    response.raise_for_status()

    data = response.json()

    authors_file = os.path.join(settings.BASE_FOLDER,
                                settings.INSTANCE_IDENTIFIER, 'authors')

    with open(authors_file + '.json', 'w') as f:
        json.dump(data, f, indent=4)

    elapsed = time.time() - elapsed
    print('Done (%.2f sec).' % elapsed)

    return data


def retrieve_and_save_paintings_info(author):
    """Retrieve and Save Paintings Info from WikiArt.

    :param author: dict, author who should have their paintings retrieved.
    :return: list, `author`'s paintings information.
    """
    print('|-Retrieving paintings info from %s...' % author['artistName'],
          end=' ', flush=True)
    elapsed = time.time()

    url = '/'.join((settings.BASE_URL, 'Painting', 'PaintingsByArtist'))
    params = {'artistUrl': author['url'], 'json': 2}
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    file = os.path.join(settings.BASE_FOLDER, settings.INSTANCE_IDENTIFIER,
                        author['url'])
    with open(file + '.json', 'w') as f:
        json.dump(data, file, indent=4)

    elapsed = time.time() - elapsed
    print('Done (%.2f sec).' % elapsed)

    return data


def download_hard_copy(painting):
    print('|-|-Retrieving hard copy of "%s"...' % painting['title'],
          end=' ', flush=True)

    elapsed = time.time()

    url = painting['image']
    file = os.path.join(settings.BASE_FOLDER, settings.INSTANCE_IDENTIFIER,
                        'images', painting['contentId'])

    # Save image.
    urllib.request.urlretrieve(url, file + settings.SAVE_IMAGES_IN_FORMAT)

    elapsed = time.time() - elapsed
    print('Done (%.2f sec).' % elapsed)


def main():
    print(__doc__)

    prepare()
    authors = retrieve_and_save_authors()

    for author in authors:
        paintings = retrieve_and_save_paintings_info(author)

        for painting in paintings:
            download_hard_copy(painting)

        # Softens server load.
        time.sleep(.1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCanceled. Bye.')
