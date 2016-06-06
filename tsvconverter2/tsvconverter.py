#!/usr/bin/python3.4
#
#     tsvconverter.py
#
# Converts annotated text stored in json into tsv format 2.
#
# Input must include the name of the document to parse and a division in sections.
#
# Json Input:
#     [ { "title" : str ,
#         "content" : [ { "section" : str|null,  # name of section
#                         "text"    : str        # body of text
#                       }, ...
#                     ]
#       }, ...
#     ]
#
# Optionally, the text may include delimiters indicating pages, in the format:
# 
#     PAGE<digit>EGAP
#       where digit is an Arabic or Indo-arabic numeral optionaly followed
#       by "v" or "r". E.g.: PAGE٨٣rEGAP.
#     
#     Page information must be separated by spaces from the rest of the text.
#
#     This information is converted into an annotation in the tsv.
#
# Dependencies:
#   ../tokenizer/tokenizer.groovy
#
#   +--------------------------------------------+
#   | TSVConverter                               |
#   +............................................|
#   | _page_pattern <<static>>: _sre.SRE_Pattern |
#   | _pagekw_out_open<<static>>: str            |
#   | _pagekw_out_close<<static>>: str           |
#   | _section_label<<static>>: str              |
#   | _section_feature<<static>>: str            |
#   | _page_label<<static>>: str                 |
#   | _page_feature<<static>>: str               |
#   | _page_pattern<<static>>: str               |
#   | _MAX_LEN_WORD <<static>>: int              |
#   | title: str                                 |          #    
#   | content: list                              |           #   ﺎﺤﻔﻇ ﺎﻟﺮﻣﺯ ﻱﺍ ﻚﺒﻴﻜﺟ
#   |............................................|            #   
#   | _tokenizerWrapper(self, txt): list         |      
#   | convert(): str                             |      
#   +--------------------------------------------+      
# 
# Usage:
#   $ python tsvconverter.py <infile> <outfile>
#
# TODO:
#   * check \n !!
#   * generate layer files?? NO, but explain the creation of layers in webanno in the readme
#   * put a 0 when there is no info for a tag
#                                                                            
###############################################################################

import os
import sys
import re
import json
import argparse
import itertools as it
from configparser import ConfigParser
from subprocess import Popen, PIPE

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

try:
    import util

except ImportError:
    # append parent directory to path
    sys.path.insert(0, os.path.join(CURRENT_PATH, '..'))
    import util

config = ConfigParser(inline_comment_prefixes=('#'))
config.read(os.path.join(CURRENT_PATH, '../config.ini'))

# process to segment and tokenize text
TOKENIZER = os.path.join(CURRENT_PATH, '../tokenizer/tokenizer.groovy')


class TSVConverter:
    """Converts json into tsv.
    
    Class attributes:
        _page_pattern (_sre.SRE_Pattern): Allowed format of page info.
        _pagekw_out_open (str): Opening keyword for indicating page info within the text.
        _pagekw_out_close (str): Closing keyword for indicating page info within the text.

        _section_label (str): Name of section custom layer in webanno.
        _section_feature (str): Name of feature of section custom layer in webanno.
        _page_label (str): Name of page custom layer in webanno.
        _page_feature (str): Name of feature of page custom layer in webanno.
        
        _page_pattern (str): Pattern of page info within input text.

        _MAX_LEN_WORD (int): Maximum number of characters an Arabic word is expected to have.
    
    """
    _page_pattern = config.get('json format', 'page allowed')
    _pagekw_out_open = config.get('json format', 'opening page keyword output')
    _pagekw_out_close = config.get('json format', 'closing page keyword output')
                      
    _section_label = config.get('webanno', 'section layer name').replace(' ','').capitalize()
    _section_feature = config.get('webanno', 'section layer feature').replace(' ','')
    _page_label = config.get('webanno', 'page layer name').replace(' ','').capitalize()
    _page_feature = config.get('webanno', 'page layer feature').replace(' ','')
                           
    _page_pattern = '%s(%s)%s' % (_pagekw_out_open,
                                  _page_pattern,
                                  _pagekw_out_close)

    _MAX_LEN_WORD = config.getint('arabic words', 'max length')


    def __init__(self, data):
        """ Constructor.

        Args:
            data (str): Json containing title of scan together with sections
                and texts to parse and convert into tsv.

        Instance attributes:
            title (): Name of the document.
            content (list): chunks of text from the document separated by sections.
                Format: [{"section" : str|null, "text" : str}, ...]
                Page delimiters are inserted within the text.

        """
        data = json.loads(data)
        self.title = data['title']
        self.content = data['content']

    def _tokenizerWrapper(self, plain_text, tokenizer_path=TOKENIZER):
        """ Sends plain_text to process tokenizer_path and collect the output - a json struct
            containing a list of sentences splitted from plain_text and a list of tokens
            for each sentence.

        Args:
            plain_text (str): Text to split in sentences and tokenize.
            tokenizer_path (str): Path of tokenizer process to call.

        Returns:
            list: Json object containing splitted and tokenized text.
                [{'sentence'=str, 'tokens'=[str,str,...]}, ...]

        Raises:
            OSError: If process call fails.

        """
        if not os.path.isfile(tokenizer_path):
            print('Fatal error: Script "%s" not found.' % tokenizer_path, file=sys.stderr)
            sys.exit(1)

        # segment and tokenize text
        #FIXME inefficient shit
        try:
            tokenizer_proc = Popen(['groovy', tokenizer_path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            out, err = tokenizer_proc.communicate(plain_text.encode('utf-8'))
        except OSError as err:
            print('Error opening tokenizer process: %s' % err, file=sys.stderr)
            sys.exit(1)

        if err.strip():
            print('Fatal error trying to execute %s:\n\n%s.' % (tokenizer_path, err), file=sys.stderr)
            sys.exit(1)

        return json.loads(out.decode('utf8'))

                 
    def convert(self):
        """ Parse json with section, page and text info and dumps all in tsv format.

        Returns:
            str: Sequence of lines corresponding to the tsv.

        Raise:
            Exception: Reraises Exceptions catched by _tokenizerWrapper.
            ValueError: If page info is not parsed correctly.

        Example:
            >>> input = {"title": "Nabrawi.djvu", "content": [{"section": "section 1", "text": \
            ... "PAGE٥٤EGAP \n الطائعين بغير الايمان"}, {"section": "section 2", "text": \
            ... "نااش حخن شحخسي ش حرة ودقيق PAGE٥٥EGAP ة ومتكاملة ومتنوعة ومحايدة، PAGE٤٤EGAP يستطيع الجميع المساهمة في"}]}
            >>> tsv = TSVConverter(json.dumps(input))
            >>> tsvout = tsv.convert()
            >>> for t in tsvout.splitlines(): print(t)
            ... 
             # webanno.custom.section | sectionname # webanno.custom.page | sectionpage
            
            #id=1
            #text= 
             الطائعين بغير الايمان
            1-1 الطائعين    B-section 1 B-٥٤
            1-2 بغير    I-section 1 I-٥٤
            1-3 الايمان I-section 1 I-٥٤
            
            #id=2
            #text=نااش حخن شحخسي ش حرة ودقيق  ة ومتكاملة ومتنوعة ومحايدة،  يستطيع الجميع المساهمة في
            2-1 نااش    B-section 2 I-٥٤
            2-2 حخن I-section 2 I-٥٤
            (...)

        """
        out = []
        cnt_sentence = 0

        pageinfo = sectioninfo = ''
        newpage = False

        for chunk in self.content:

            newsection = True
            
            section = chunk['section']
            text = chunk['text']

            if section:
                sectioninfo = 'B-%s' % section

            try:
                tokenized = self._tokenizerWrapper(text)
            except Exception:
                raise

            for item in tokenized:
                cnt_sentence+=1
                
                sentence = item['sentence'] # str
                tokens = item['tokens'] # list of strings

                cleantxt = re.sub(r'%s' % TSVConverter._page_pattern, '', sentence)

                if TSVConverter._pagekw_out_open in cleantxt:
                    raise ValueError('Bad format for page info in scan "%s" '
                                     'Call the administrator.' % self.title)

                out.append('\n#id=%d' % cnt_sentence)
                out.append('#text=%s' % cleantxt)
                
                cnt_token = 0
                for token in tokens:

                    #
                    # check possible typos in token
                    #

                    if not re.match(r'%s' % TSVConverter._page_pattern, token):

                        # word with non arabic char in an arabic alphabetic word
                        if any(util.isArabicalpha(c) for c in token) and \
                           any(not util.isArabicalpha(c) for c in token):
                            print('Warning in section "%s" of scan %s: word "%s" may contain a typo.'
                                   % (section, self.title, token), file=sys.stderr)
                        
                        # exceeds max length
                        if len(token) > TSVConverter._MAX_LEN_WORD:
                            print('Warning in section "%s" of scan %s: word "%s" may contain a typo.'
                                   % (section, self.title, token), file=sys.stderr)

                        # if ta marbuta (U+0629) in the middle
                        if len(token)>2:
                            if 'ة' in token[1:-1]:
                                print('Warning in section "%s" of scan %s: word "%s" may contain a typo.'
                                     % (section, self.title, token), file=sys.stderr)                          

                    
                    # new page found, start B tag
                    if TSVConverter._pagekw_out_open in token:

                        pagefound = re.match('^%s$' % TSVConverter._page_pattern, token)

                        if not pagefound:
                            raise ValueError('Page information not well formated in scan "%s".' % self.title)

                        if len(pagefound.groups()) != 1:
                            raise ValueError('Page information not well formated in scan "%s".' % self.title)

                        pageinfo = 'B-%s' % pagefound.groups(0)
                        newpage = True

                        continue

                    # do not count a new token if page info is found                        
                    else:
                        cnt_token += 1

                    if sectioninfo and not newsection:
                        sectioninfo = 'I-%s' % section

                    if pageinfo and not newpage:
                        pageinfo = 'I' + pageinfo[1:]
                    
                    newpage = False
                    newsection = False

                    entry = '%d-%d\t%s\t%s\t%s' % (cnt_sentence, cnt_token, token,
                                                   sectioninfo, pageinfo)
                        
                    out.append(re.sub('\t+', '\t', entry))

        header = ''
        
        if sectioninfo:
            header+=' # webanno.custom.%s | %s' % (TSVConverter._section_label,
                                                   TSVConverter._section_feature)
     
        if pageinfo:
            header+=' # webanno.custom.%s | %s' % (TSVConverter._page_label,
                                                   TSVConverter._page_feature)

        out.insert(0, header)
        return '\n'.join(out)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Convert json into tsv')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                                  help='input file to parse [DEFAULT stdin]', metavar='infile.json')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                                   help='output file to create [DEFAULT stdout]', metavar='outfile.tsv')
    args = parser.parse_args()

    tsv = TSVConverter(args.infile.read())
    try:
        tsvout = tsv.convert()
    except Exception as e:
        print('Fatal error in TSVConverter: %s' % e, file=sys.stderr)
        sys.exit(1)

    print(tsvout, file=args.outfile)
