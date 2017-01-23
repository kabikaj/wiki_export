#!/usr/bin/python3.4
#
#    wiki_to_tsv_converter.py  @DEPRECATED - Main to export transcriptions from the wiki and convert them to tsv
#
#    Copyright (C) 2016  Alicia González Martínez, aliciagm85+code@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################### 
#
# dependencies:
#   * exporthandler.py
#   * wikiparser.py
#   * tsvconverter.py
#   * util.py
#   * config.ini
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
from tsvconverter2.tsvconverter import TSVConverter

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

# append current directory to sys.path
sys.path.insert(0, CURRENT_PATH)

from exporthandler.exporthandler import ExportHandler

config = ConfigParser(inline_comment_prefixes=('#'))
config.read(os.path.join(CURRENT_PATH, 'config.ini'))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Download scan transliterations from the wiki and convert to tsv2.')
    parser.add_argument('--title', help='download only the texts belonging to this title')
    parser.add_argument('--outpath', help='path to save output tsv files')
    args = parser.parse_args()

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

        with open(os.path.join(args.outpath, fname+'.tsv'), 'w') as fp:
            fp.write(tsvout)
