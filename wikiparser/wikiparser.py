#!/usr/bin/python3.4
#
#     wikiparser.py
#
# Parse plain text of scan transcriptions and dump into json format.
#
#   +---------------------------------------------+
#   | WikiParser                                  |
#   +.............................................|
#   | _pagekw_input <<static>>: str               |
#   | _pagekw_out_open <<static>>: str            |
#   | _pagekw_out_close <<static>>: str           |
#   | _title_pattern <<static>>: _sre.SRE_Pattern |
#   | _title_strip <<static>>: str                |
#   | _UNICODE_CHARS <<static>>: dict             |
#   | _QUOTATION_MARKS <<static>>: tuple          |
#   | _PUNCT_PAIRS <<static>>: dict               |
#   | _PUNCT_EQUAL <<static>>: list               |
#   | rawtexts: str                               |
#   | title: str                                  |      
#   +..........................................   |      #
#   | _join_titletext(self, groups): (str,str)    |       #   ﺎﺤﻔﻇ ﺎﻟﺮﻣﺯ ﻱﺍ ﻚﺒﻴﻜﺟ
#   | _cleaner(self, groups): list                |        #
#   | parse(): list                               |      
#   +---------------------------------------------+      
#
# Note:
#   * Page info is included along with the body of the text in the format:
#     PAGE<digit>EGAP, where digit is an Arabic or Indo-arabic numeral
#     optionaly followed by "v" or "r". E.g.: PAGE٨٣EGAP.
#     This format will prevent tokenizers from splitting the number from the surrounding
#     keyword and at the same time make it distinguishable from normal text.
#                                                
# Example:
#   >>> title = 'mytitle'
#   >>> texts = ['block of text 1', '==title foo== \n block of text 2', 'صفحة 23 \n block of text 3']
#   >>> parser = wp.WikiParser(texts, title)
#   >>> parser.parse()
#   [{'section': None, 'text': 'block of text 1'},
#    {'section': 'title foo', 'text': 'block of text 2 PAGE23EGAP block of text 3'}]
#
######################################################################################################

import os
import sys
import re
import itertools as it
import operator as op
from configparser import ConfigParser

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

try:
    import util

except ImportError:
    # append parent directory to path
    sys.path.insert(0, os.path.join(CURRENT_PATH, '..'))
    import util

config = ConfigParser(inline_comment_prefixes=('#'))
config.read(os.path.join(CURRENT_PATH, '../config.ini'))


class WikiParser:
    """Convert wiki string into json.

    Class attributes:
        _pagekw_input (str): Keyword introducing page information in the wiki.
        _pagekw_out_open (str): Opening keyword for indicating page info in the output.
        _pagekw_out_close (str): Closing keyword for indicating page info in the output.

        _page_pattern (_sre.SRE_Pattern): Allowed format of page info.
        _title_pattern (_sre.SRE_Pattern): Format of titles in wiki.
        _title_strip (str): Character belonging to circumfix used to mark a title in the wiki.
        
        _UNICODE_CHARS (dict): Unicode values of characters to be checked in the text.
        _QUOTATION_MARKS (tuple): List of possible quotation marks that can be found in the texts.
        _PUNCT_PAIRS (dict): Punctuation marks that delimit a text with opening and closing chars.
        _PUNCT_EQUAL (list): Punctuation marks that delimit a text with a char.

    """
    _pagekw_input = config.get('wiki format', 'page keyword input')
    _pagekw_out_open = config.get('json format', 'opening page keyword output')
    _pagekw_out_close = config.get('json format', 'closing page keyword output')
                     
    _page_pattern = re.compile(r'^%s$' % config.get('json format', 'page allowed'))
    _title_pattern = re.compile(r'^%s$' % config.get('wiki format', 'title pattern'))
    _title_strip = config.get('wiki format', 'char to strip')
                          
    _UNICODE_CHARS = dict((k,util.tochar(v)[0]) for k,v in config['unicode'].items())
    _QUOTATION_MARKS = tuple(config['quotation marks'].values())
    _PUNCT_PAIRS = dict(util.tochar(*x) for x in config['punctuation delimiters pairs'].items())
    _PUNCT_EQUAL = list(config['punctuation delimiters equal'].values())

    def __init__(self, rawtexts, title):
        """ Constructor.

        Args:
            rawtexts (list): Texts of transcriptions from the wiki.
            title (str): Name of scan texts being parsed.

        Raises:
            ValueError: If either rawtexts or title are None or empty.

        """
        if not rawtexts:
            raise ValueError('Error in WikiParser constructor: rawtext is None or empty.')
        if not title:
            raise ValueError('Error in WikiParser constructor: title is None or empty.')

        self.rawtexts = rawtexts
        self.title = title

    def _join_titletext(self, groups):
        """ Group section titles with its corresponding texts.
        
            If Texts don't have a title, section is set as None.
            If title is the last line, its text is set as an empty string.
        
        Args:
            groups (list): two-element tuples with result of the regex and
                the list of lines grouped.
        
        Yields:
            str, str: title of section and texts included.
                Title string may be None.
        
        """
        size = len(groups)
        i = 0

        while i<size:
            k,g = groups[i]

            # g contains plain texts, and there is no section
            if not k:
                yield None, g

            # g contains the name of a section
            else:
                section = g[0].strip('%s ' % WikiParser._title_strip)
                i+=1
                if i == size:
                    print('Warning parsing %s: No text in section "%s"' % (self.title, section), file=sys.stderr)
                    yield section, ''
                else:
                    # get corresponding text
                    k,g = groups[i]
                    yield section, g
            i+=1

    def _cleaner(self, groups):
        """ Parse all lines of transcriptions, check for errors and sanitize texts.

        Args:
            groups (list): Lines grouped by wiki pages. Structure:
                [(i,[str, str]), (i,[...]), ...]
        Return:
            list: Modified and checked lines grouped by wiki pages. Structure:
                [(i,[str, str]), (i,[...]), ...]

        """
        CLOSING = WikiParser._PUNCT_PAIRS.values()
        stack = []  # to store opening chars of punctuation and check balanceness

        out = []
        for i,lines in groups:

            aux = []
            for li in lines:

                # skip lines that only contain directionality marks
                if li == WikiParser._UNICODE_CHARS['rtl'] or li == WikiParser._UNICODE_CHARS['ltr']:
                    continue

                # add empty lines directly (they correspond to newlines)
                if not li:
                    aux.append(li)
                    continue

                # add lines containing page info directly
                if li.startswith(WikiParser._pagekw_input):
                    pageinfo = li[len(WikiParser._pagekw_input):].strip()

                    if not WikiParser._page_pattern.match(pageinfo):
                        raise ValueError('Error in first line of page %d of scan %s: page number can only '
                                         'contain digits 0-9/٠-٩ and r or v for manuscripts' % (i, self.title))

                    aux.append(''.join((WikiParser._pagekw_out_open, pageinfo, WikiParser._pagekw_out_close)))
                    continue

                # check for malformed titles
                if '=' in li and not li.startswith('=='): #FIXME take from wiki format -> char to strip ??
                    print('Warning in page %d of scan %s: there may be a malformed title. '
                          'Expected format of titles is "== TITLE ==".' % (i, self.title), file=sys.stderr)

                # remove BOM
                if WikiParser._UNICODE_CHARS['bom'] in li:
                    print('Modification in page %d of scan %s: BOM character found and removed.' % (i, self.title), file=sys.stderr)
                    li = li.replace(WikiParser._UNICODE_CHARS['bom'], '')

                #DEPREPATED it's not only used for justification, it is also used as a punctuation mark
                # remove tatweel
                #if WikiParser._UNICODE_CHARS['tatweel'] in li:
                #    print('Modification in page %d of scan %s: tatweel character found and removed.'
                #          % (i, self.title), file=sys.stderr)
                #    li = li.replace(WikiParser._UNICODE_CHARS['tatweel'], '')

                # convert double prime char into tanween fatha (probably, error from the OCR)
                if WikiParser._UNICODE_CHARS['double prime'] in li:
                    print('Modification in page %d of scan %s: Double prime character (U+2033) found '
                          'and changed to tanwin hamza (U+06b4).' % (i, self.title), file=sys.stderr)
                    li = li.replace(WikiParser._UNICODE_CHARS['double prime'], WikiParser._UNICODE_CHARS['tanwin fatha'])

                # normalise quotation marks
                li_modif = re.sub('[%s]' % ''.join(WikiParser._QUOTATION_MARKS), '"', li)
                if li_modif != li:
                    print('Modification in page %d of scan %s: All Quotation marks except "«»" normalised to (").'
                           % (i, self.title), file=sys.stderr)
                    li = li_modif

                # split waw from quoted word, eg: (و"المصدوق) into (و "المصدوق)
                # so that tokenization process works well
                if ' و"' in li:
                    print('Modification in page %d of scan %s: waw separated from quoted word.' % (i, self.title), file=sys.stderr)
                    li = li.replace(' و"', 'و "')

                # warning arabic zero
                #DEPRECATED
                #possible_dots = re.findall(r'\b([^٠-٩ ]+?٠)\b', li)
                if '٠' in li:
                    print('Warning in page %d of scan %s: Arabic zero "٠" may be in position of a dot "."'
                          % (i, self.title), file=sys.stderr) 
                
                # normalise spaces and add line to output
                aux.append(re.sub(r'[\t ]+', ' ', li))

                # check there are no unbalanced punctuation pairs
                for current in li:

                    if current not in WikiParser._PUNCT_EQUAL and \
                       current not in WikiParser._PUNCT_PAIRS and \
                       current not in WikiParser._PUNCT_PAIRS.values():
                        continue
                    if current in CLOSING:
                        if not stack:
                            print('Warning in page %d of scan %s: opening character missing for char %s'
                                   % (i, self.title, current), file=sys.stderr)
                            continue
                        i_prev, prev = stack.pop()
                        if prev in WikiParser._PUNCT_EQUAL:
                            print('Warning in page %d of scan %s: opening character missing for char %s'
                                   % (i_prev, self.title, prev), file=sys.stderr)
                        elif prev in CLOSING:
                            print('Warning in page %d of scan %s: opening character missing for char %s'
                                   % (i_prev, self.title, prev), file=sys.stderr)
                        else:
                            if WikiParser._PUNCT_PAIRS[prev] != current:
                                print('Warning in page %d of scan %s: char %s and char %s don\'t match'
                                   % (i, self.title, prev, current), file=sys.stderr)
                        continue
                    if current in WikiParser._PUNCT_EQUAL:
                        if not stack:
                            stack.append((i, current))
                            continue
                        i_prev, prev = stack.pop()
                        if current == prev:
                            continue
                        else:
                            stack.append((i_prev, prev))
                            stack.append((i, current))
                        continue
                    # current is opening
                    stack.append((i, current))

            out.append((i,aux))

        # check if there are isolated opening punct left
        if stack:
            for i,char in stack:
                print('Warning in page %d of scan %s: closing character missing for char %s'
                      % (i, self.title, char), file=sys.stderr)
        
        return out


    def parse(self):
        """ Get information of page, title and text from rawtexts and yield into json.

        Returns:
            list: Filtered and formatted data, format:
                [ { "section" : str|None, "text" : str }, ... ]

        """
        # split lines in groups and add page number : [(i,[str, str]), (i,[...]), ...]
        # empty strings correspond to newlines
        groupslines = list(enumerate((txt.splitlines() for txt in self.rawtexts), 1))

        try:
            groupslines = self._cleaner(groupslines)
        except Exception:
            raise

        # strip all lines and remove blank lines only at the beginning and at the end
        grlines = [(i,list(util.striplines(lines))) for i,lines in groupslines]

        # remove wiki page counter from rest of lines
        grlines = (lines for i,lines in grlines)

        # join all lines in one list: [str, str, ...]
        lines = list(it.chain(*grlines))
        
        # group lines by titles
        gr_titles = [(k,list(g)) for k,g in it.groupby(lines, WikiParser._title_pattern.match)]
        
        return [{'section': title,
                 'text'   : ' '.join(t if t else '\n' for t in util.striplines(txts))}
                 for title, txts in self._join_titletext(gr_titles)]

