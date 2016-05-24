"""WikiArt.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""

import argparse
import time

from . import settings, base
from .converter import WikiArtMetadataConverter
from .fetcher import WikiArtFetcher


class Console:
    def __init__(self):
        p = argparse.ArgumentParser(
            description='Process paintings from WikiArt.')

        p.add_argument('--override',
                       default=False, action='store_true',
                       help='Override existing files.')
        p.add_argument('--verbose',
                       default=True, action='store_true',
                       help='Verbose process.')
        p.add_argument('--instance',
                       default='1',
                       help='Fetching or conversion instance'
                            '(if multiple are desired).')

        # Fetch operation.
        sp = p.add_subparsers(
            title='operations',
            description='specify which operation to perform.')
        p_fetch = sp.add_parser('fetch', help='Fetch paintings from WikiArt.')
        p_fetch.add_argument('--check', type=bool, default=True,
                             help='Check downloaded files.')
        p_fetch.add_argument('--only', type=str, default='all',
                             choices=('artists', 'paintings', 'all'),
                             help='Fetch only artists list, paintings '
                                  'metadata or artists, paintings annotations '
                                  'and copies.')

        p_fetch.set_defaults(func=self.fetch)

        # Convert operation.
        p_convert = sp.add_parser('convert',
                                  help='Transform collected paintings '
                                       'metadata to data set notation.')

        p_convert.set_defaults(func=self.convert)

        self.parser = p

    def interpret(self):
        print(__doc__)
        elapsed = time.time()

        try:
            args = self.parser.parse_args()
            settings.INSTANCE_IDENTIFIER = args.instance

            # Initiate logging, if requested.
            base.Logger.active = args.verbose
            base.Logger.keep_messages = False

            if not hasattr(args, 'func'):
                return self.main(args)

            args.func(args)
        except KeyboardInterrupt:
            print('\nCanceled.')
        else:
            print('\nDone (%.2f sec).' % (time.time() - elapsed))

    def main(self, args):
        return self.fetch(args).convert(args)

    def fetch(self, args):
        fetcher = WikiArtFetcher(override=args.override)
        fetcher.prepare()

        if not hasattr(args, 'only') or args.only == 'all':
            args.only = 'all'
            fetcher.fetch_all()
        else:
            fetcher.fetch_artists()

            if args.only == 'paintings':
                fetcher.fetch_all_paintings()

        if args.check: fetcher.check(only=args.only)

        return self

    def convert(self, args):
        (WikiArtMetadataConverter(override=args.override)
         .prepare()
         .generate_images_data_set()
         .generate_labels())

        return self


def main():
    Console().interpret()
