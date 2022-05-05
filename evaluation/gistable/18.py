#!/usr/bin/env python
"""Reads json lines from stdin and write csv to stdout.

Usage:
  json2csv.py -f <field>...
  json2csv.py -h | --help
  json2csv.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  -f --fields   Specify headers of the csv file.

"""
from unicodecsv import DictWriter
from docopt import docopt
import json
import sys


if __name__ == '__main__':
    arguments = docopt(__doc__, version='0.1')

    csv_wrt = DictWriter(sys.stdout, extrasaction="ignore", fieldnames=arguments['<field>'])
    csv_wrt.writeheader()
    for line in sys.stdin:
        datum = json.loads(line)
        csv_wrt.writerow(datum)
