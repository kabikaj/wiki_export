#!/usr/bin/python3.4
#
#     offsetbuilder.py
#
# Converts texts segmented in sections into offsets from a unified text.
#
#   +-----------------------------------+
#   | OffsetsBuilder                    |
#   +...................................|
#   | _page_allowed <<static>>: str     |
#   | _pagekw_out_open <<static>>: str  |
#   | _pagekw_out_close <<static>>: str |
#   | _page_pattern <<static>>: str     |
#   | _data: str                        |
#   | alltext: str                      |
#   | sections: list                    |        #
#   | pages: list                       |       #   ﺎﺤﻔﻇ ﺎﻟﺮﻣﺯ ﻱﺍ ﻚﺒﻴﻜﺟ
#   |...................................|      #
#   | _calculate()                      |
#   | _adjust_borders()                 |
#   | build(): str                      |      
#   +-----------------------------------+      
#                                              
# Json Input:
#     
#     [ { "section" : str|null,
#         "text"    : str PAGE$digitEGAP str ...
#       },
#       ...
#     ]
#
# Json Output:
#
#     { "text" : str,
#       "sections" : [ { "name" : str,
#                        "start" : int,
#                        "end" : int
#                      } ,
#                      ...
#                    ],
#       "pages" : [ { "name" : str,
#                     "start" : int,
#                     "end" : int
#                   } ,
#                   ...
#                 ]
#     }
#  
# Example:
#   $ python offsetbuilder.py Example_for_DjVu_manual_cz-book_color.json
#                                                                            
##################################################################################

import sys
import os
import re
import json
import argparse
from configparser import ConfigParser

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser(inline_comment_prefixes=('#'))
config.read(os.path.join(CURRENT_PATH, '../config.ini'))


class OffsetsBuilder:
    """Calculates offsets of annotation and merge text in one unit.

    Class attributes:
        _page_allowed (str): Allowed format of page info.
        _pagekw_out_open (str): Opening keyword for indicating page info within the text.
        _pagekw_out_close (str): Closing keyword for indicating page info within the text.
        _page_pattern (str): Pattern of page info within input text.

    """
    _page_allowed = config.get('json format', 'page allowed')
    _pagekw_out_open = config.get('json format', 'opening page keyword output')
    _pagekw_out_close = config.get('json format', 'closing page keyword output')
                                                 
    _page_pattern = r'%s(%s)%s' % (_pagekw_out_open,
                                   _page_allowed,
                                   _pagekw_out_close)

    def __init__(self, data):
        """ Constructor.

        Attributes:
            _data (str): Json containing list of section and texts.
            alltext (str): 
            sections (list): Dictionaries containing start and end offsets of the annotated segments.
                [ { "start" : int, "end" : int }, ...]
            pages (list): Dictionaries containing start and end offsets of the annotated segments.
                [ { "start" : int, "end" : int }, ...]

        """
        self._data = json.loads(data)
        self.alltext = ''
        self.sections = []
        self.pages = []

    def _calculate(self):
        """ Calculates the values of alltext, sections and pages.

        Remove the PAGE$digitEGAP keywords from the texts and converts it
        into annotation offsets. Merges the modified texts into one block
        and saves it into alltexts. Converts also the section information
        into annotation offsets.

        """
        pivot = 0  # absolute index of first char of current chunk of text
        page_start_abs = -1
        current_page_info = None
        remove_gaps = 0

        for chunk in self._data:

            current = 0 # current char in chunk

            for m in re.finditer(r'%s *' % OffsetsBuilder._page_pattern, chunk['text']):
                
                page_info = m.group(1)
                pagekw_start, pagekw_end = m.span()

                if page_start_abs != -1:
                    my_last_end = pivot + pagekw_start - remove_gaps - 1
                    self.pages.append({
                        'name' : current_page_info,
                        'start' : page_start_abs,
                        'end' : my_last_end})

                    remove_gaps += pagekw_end - pagekw_start

                page_start_abs = pivot + pagekw_start
                current_page_info = page_info

                self.alltext += chunk['text'][current:pagekw_start]
                current = pagekw_end

            self.alltext += chunk['text'][current:]

            if chunk['section']:

                self.alltext += '\n' # add newline at the end of each section
                
                self.sections.append({
                    'name' : chunk['section'],
                    'start' : pivot,
                    'end' : len(self.alltext)-1})

            pivot = len(self.alltext)

        if page_start_abs != -1:
            self.pages.append({
                'name' : page_info,
                'start' : my_last_end + 1,
                'end' : pivot - 1})

    def _adjust_borders(self):
        """ Move index borders that point to newlines to non-newline char.

            Start ofsset is set forward and end offset is put back.

        """
        for annotation in (self.sections, self.pages):

            for entry in annotation:

                while self.alltext[entry['start']] == '\n':
                    entry['start'] += 1

                while self.alltext[entry['end']] == '\n':
                    entry['end'] -= 1
        
    
    def build(self):
        """ Perform offset calculations and build and merges the text.

        Return:
            str: Json object with the info of texts and annotation offsets.
                {"text" : str,
                 "sections" : [{"name":str, "start":int, "end":int}, ...],
                 "pages" : [{"name":str, "start":int, "end":int}, ...]}

        """
        self._calculate()
        self._adjust_borders()

        return json.dumps({'text' : self.alltext,
                           'sections' : self.sections,
                           'pages' : self.pages}, ensure_ascii=False)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Calculate offsets of annotation and dumps into json.')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                         help='input file to parse [DEFAULT stdin]', metavar='infile.json')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                         help='output file to create [DEFAULT stdout]', metavar='outfile.json')
    args = parser.parse_args()

    offbr = OffsetsBuilder(args.infile.read())
    out = offbr.build()
    args.outfile.write(out)
