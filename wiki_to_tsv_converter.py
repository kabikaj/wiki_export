#!/usr/bin/python3.4
#
#     wiki_to_tsv_converter.py
#
# Main to export transcriptions from the wiki and convert them to tsv
#
# dependencies:
#   * exporthandler.py
#   * wikiparser.py
#   * tsvconverter.py
#                                         +------------------+        +---------------+
#   +--------------------------+          |                  | -----> |               |
#   |                          | -------> | exporthandler.py |   str  | wikiparser.py |
#   |                          | <------- |                  | <----- |               |
#   |                          |   json   +------------------+  json  +---------------+
#   | wiki_to_tsv_converter.py |          
#   |                          |          +-----------------+
#   |                          | -------> |                 |
#   |                          |  json    | tsvconverter.py | -------> tsv output file
#   +--------------------------+          |                 |
#                                         +-----------------+
# usage:
#   $ python wiki_to_tsv_converter.py
#
#######################################################################################

import os
import sys
import json
import argparse
from configparser import ConfigParser

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

# append current directory to sys.path
sys.path.insert(0, CURRENT_PATH)

from exporthandler.exporthandler import ExportHandler

config = ConfigParser(inline_comment_prefixes=('#'))
config.read(os.path.join(CURRENT_PATH, 'config.ini'))

OUT_PATH = os.path.join(CURRENT_PATH, config.get('tsv output', 'path'))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Download scan transliterations from the wiki.')
    parser.add_argument('--title', help='download only the texts belonging to this title')
    outformat = parser.add_mutually_exclusive_group(required=True)
    outformat.add_argument('--tsv2', action='store_true', help='Generate output in TSV2 format')
    outformat.add_argument('--tsv3', action='store_true', help='Generate output in TSV3 format')
    args = parser.parse_args()

    if args.tsv2:
        from tsvconverter2.tsvconverter import TSVConverter
    elif args.tsv3:
        from tsvconverter3.tsvconverter import TSVConverter

    handler = ExportHandler()
    
    try:
        data = handler.export(args.title)  # calls WikiParser
    except Exception as e:
        print('Fatal error in ExportHandler: %s' % e, file=sys.stderr)
        sys.exit(1)

    for scan in json.loads(data):

        title = scan['title']
        
        try:
            tsv = TSVConverter(json.dumps(scan, ensure_ascii=False))
            tsvout = tsv.convert()

        except Exception as e:
            print('Fatal error in TSVConverter: %s' % e, file=sys.stderr)
            sys.exit(1)

        fname, fext = os.path.splitext(title)

        with open(os.path.join(OUT_PATH, fname+'.tsv'), 'w') as fp:
            fp.write(tsvout)
