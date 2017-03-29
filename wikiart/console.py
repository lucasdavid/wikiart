"""WikiArt.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""

import argparse
import time

from . import base, converter, fetcher, settings


class Console:
    def __init__(self):
        p = argparse.ArgumentParser(
            description='Process paintings from WikiArt.')

        p.add_argument('--override',
                       default=False, action='store_true',
                       help='override existing files')
        p.add_argument('--verbose',
                       default=True, action='store_true',
                       help='verbose process')
        p.add_argument('--datadir', default=None,
                       help='output directory for dataset')
        p.add_argument('--check', type=bool, default=True,
                       help='check downloaded files')

        # Fetch operation.
        sp = p.add_subparsers(
            title='operations',
            description='specify which operation to perform.')
        p_fetch = sp.add_parser('fetch', help='fetch paintings from WikiArt')
        p_fetch.add_argument('--only', type=str, default='all',
                             choices=('artists', 'paintings', 'all'),
                             help='fetch only artists list, paintings '
                                  'metadata or artists, paintings annotations '
                                  'and copies')

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
            if args.datadir is not None:
                settings.BASE_FOLDER = args.datadir

            # Initiate logging, if requested.
            base.Logger.active = args.verbose
            base.Logger.keep_messages = False

            if not hasattr(args, 'func'):
                return self.main(args)

            args.func(args)
        except KeyboardInterrupt:
            print('\ncanceled')
        else:
            print('\ndone (%.2f sec)' % (time.time() - elapsed))

    def main(self, args):
        return self.fetch(args).convert(args)

    def fetch(self, args):
        f = fetcher.WikiArtFetcher(override=args.override)
        f.prepare()

        if not hasattr(args, 'only') or args.only == 'all':
            args.only = 'all'
            f.fetch_all()
        else:
            f.fetch_artists()

            if args.only == 'paintings':
                f.fetch_all_paintings()

        if args.check: f.check(only=args.only)

        return self

    def convert(self, args):
        (converter.WikiArtMetadataConverter(override=args.override)
         .prepare()
         .generate_images_data_set()
         .generate_labels())

        return self


def main():
    Console().interpret()
