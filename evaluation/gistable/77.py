# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import argparse
from sys import version_info


python2 = version_info[0] == 2
python3 = version_info[0] == 3

if python2:
    from codecs import open
elif python3:
    from io import open


def parse_args():
    """Parse options and arguments to main."""
    parser = argparse.ArgumentParser(
            description="Description of this program.",
            epilog="Text to be added after usage information."
    )
    parser.add_argument('--long_arg',
                        '-l',
                        dest='var_name',
                        metavar='TYPE',
                        default='default',
                        help='Help message for option.')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    example = args.var_name
    return None


if __name__ == '__main__':
    main()
