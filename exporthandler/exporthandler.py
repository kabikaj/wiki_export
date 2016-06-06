#!/usr/bin/python3.4
#
#     exporthandler.py
#
# Export transcriptions of scans from the COBHUNI wiki
#
#   +---------------------------------------+
#   | ExportHandler                         |
#   +.......................................|
#   | _url: str                             |
#   | _login_action: str                    |
#   | _login_query: str                     |
#   |.......................................|
#   | _POST_request(params, session): dict  |
#   | _login(params, session): None         |
#   | _get_titles_scan(data): list          |
#   | _export_title(title, session): dict   |
#   | export(title): list                   |           #
#   +---------------------------------------+            #   ﺎﺤﻔﻇ ﺎﻟﺮﻣﺯ ﻱﺍ ﻚﺒﻴﻜﺟ
#                                                         #
# Json Output:
#     [ { "title" : str ,
#         "content" : [ { "section" : str|null,
#                         "text"    : str 
#                       }, ...
#                     ]
#       }, ...
#     ]
# 
# Doc mediawiki doc references:
#   * login: https://www.mediawiki.org/wiki/API:Login
#   * formats: https://www.mediawiki.org/wiki/API:Data_formats
#   * queries: https://www.mediawiki.org/wiki/API:Query
# 
# Example:
#     # export all scan transliteration
#   $ python exporthandler.py
#     # export transliteration of only one title
#   $ python exporthandler.py --title Example_for_DjVu_manual_cz-book_color.djvu
#                                                                            
#########################################################################################

import re
import sys
import os
import json
import requests
import argparse
from configparser import ConfigParser
from bs4 import BeautifulSoup
import logging
from pprint import pprint

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

try:
    from wikiparser.wikiparser import WikiParser

except ImportError:
    # append parent directory to path
    sys.path.insert(0, os.path.join(CURRENT_PATH, '..'))
    from wikiparser.wikiparser import WikiParser

config = ConfigParser(inline_comment_prefixes=('#'))
config.read(os.path.join(CURRENT_PATH, '../config.ini'))


class ExportHandler:
    """Export and filter transcriptions from the wiki. """

    def __init__(self):
        """ Constructor.

        Attributes:
            _url (str): Url of the API.
            _login_action (dict): Parameters for login action.
            _query_action (dict): Parameters for query action.

        """
        self._url = config.get('wiki api', 'endpoint')
        self._login_action = dict(config['wiki login'].items())
        self._query_action = dict(config['wiki query'].items())

    def _POST_request(self, params, session, debug):
        """Do a HTTP POST request to url passing params.
        
        Args:
            url (str): Url to send the request.
            params (dict): Variables to pass for the request.
            session (str): Current session.
        
        Return:
            dict: Response of the request.

        Raises:
            RequestException: If POST request fails.
            ValueError: If request status code is not ok.
                If POST request fails and it's not catched by the requests module.
        
        """
        try:
            req = session.post(self._url, data=params)
        except requests.exceptions.RequestException:
            if debug: print('debug:POST request failed', file=sys.stderr)
            raise
        except Exception:
            raise ValueError('Error in POST request not catched by requests module.')

        if debug: print('debug:POST request success', file=sys.stderr)
        
        if req.status_code != requests.codes.ok:
            raise ValueError('Error 403')
        
        return json.loads(req.text)

    def _login(self, params, session, debug):
        """Authenticate in the wiki to start querying.
        
        Args:
            url (str): Url to send the request.
            params (dict): Variables to pass for the request.
            session (str): Current session.
            debug (bool): Debug mode.

        Raises:
            Exception: Reraises Exceptions catched by _POST_request.
            ValueError: When username or password are incorrect.
        
        """
        # login with credentials
        try:
            r = self._POST_request(self._login_action, session, debug)
        except Exception:
            if debug: print('debug:credentials failed', file=sys.stderr)
            raise

        if debug: print('debug:credentials verified', file=sys.stderr)
        
        # update login parameters with token
        self._login_action['lgtoken'] = r['login']['token']
        
        # confirm login token
        try:
            r = self._POST_request(self._login_action, session, debug)
        except Exception:
            if debug: print('debug:token confirmation failed', file=sys.stderr)
            raise

        if debug: print('debug:token confirmation success', file=sys.stderr)

        if r['login']['result'] != 'Success':
            raise ValueError('Login failed. Check username and password in config files, and json response.')

    def _get_titles_scans(self, session, debug):
        """ Retrieves the list of scan names.

        This query is the default one included in the config file,
        because if requested it's expected to be the first one.

        Args:
            session (str): current session for the http requests.
            debug (bool): Debug mode.
                
        Return:
            list: names of pages containing scans.

        Raises:
            Exception: Reraises Exceptions catched by _POST_request.
            ValueError: If json of http query response has different format than expected.
        
        """
        try:
            r = self._POST_request(self._query_action, session, debug)
        except Exception:
            raise

        try:
            table = r['query']['pages'][0]['revisions'][0]['content']
        except KeyError as e:
            raise ValueError('Not expected json structure: Unknown key %s' % e)

        titles = re.findall(r':([^:]+?\.djvu)', table)

        if not titles:
            print('Warning: No djvu files found in Scans page on the wiki.', file=sys.stderr)

        if debug: print('debug:scan titles retrieved. List: %s' % ', '.join(titles), file=sys.stderr)
        
        return titles

    def _export_title(self, title, session, debug):
        """ Export all pages of a given title from the wiki.

        Args:
            title (str): Title of scan to download transcription from.
            session (str): Current session for the http requests.
            debug (bool): Debug mode.

        Returns:
            dict: Transliteration in json format corresponding to title. Format:

              {"title" : str, "content" : [{"section" : str|None, "text":str}, ...]}

        Raises:
            Exception: Reraises Exceptions catched by _POST_request,
                BeautifulSoup constructor and WikiParser constructor.
            ValueError: If no text is found either in the whole scan or in one of its pages.
            AttributeError: If the retrieved xml structure inside json is not the one expected.
            LookupError: If the retrieved json structure is not the one expected.

        """
        npage = 0
        texts = []

        while True:
            npage += 1

            # update query with new page
            self._query_action['titles'] = 'Page:%s/%d' % (title, npage)

            # get content of new page
            try:
                r = self._POST_request(self._query_action, session, debug)
            except Exception:
                raise

            try:
                info = r['query']['pages'][0]
            except LookupError as e:
                raise LookupError('Unrecognised key %s in json' % e)

            if 'missing' in info:
                if npage == 1:
                    raise ValueError('No text found in title %s. '
                                     'Make sure the query is correct.' % title)
                break

            try:
                data = info['revisions'][0]['content']
            except LookupError as e:
                raise LookupError('Unrecognised key %s in json' % e)

            try:
                soup = BeautifulSoup(data, 'xml')
            except Exception:
                raise

            try:
                plaintext = soup.noinclude.text
            except AttributeError as e:
                raise AttributeError('Unrecognised xml structure. %s' % e)

            if plaintext is None or not plaintext.strip():
                raise ValueError('Page %d of scan title "%s" is empty.' % (npage,title))

            texts.append(plaintext)

            if debug: print('debug:text from page %d title %s exported' % (npage, title),
                            file=sys.stderr)

        

        parser = WikiParser(texts, title)

        try:
            outjson = parser.parse()
            
        except Exception as e:
            raise ValueError('Error in WikiParser: %s' % e)

        return {'title' : title, "content" :  outjson}

    def export(self, title=None, debug=False):
        """ Export all transcriptions of scans from wiki or only the title if it is not None.

        Args:
            title (str): Title of transcription to retrieve in case only one is required.
            debug (bool): Debug mode.

        Returns:
            str: Transliteration in json format corresponding to title or of all titles
                 if title is None. Format of structure:

                 [{"title":str, "content":[{"section" : str|null, "text":str}, ...]}, ...]

        Raises:
            Exception: Reraises Exceptions catched by _login, _export_title and _get_titles_scans.

        Example:
            >>> e = ExportHandler()
            >>> e.export("Attaiyin.djvu")
            ('[ { "title"   : "Attaiyin.djvu",'
             '    "content" : [ { "section" : "الحديث الرابع",'
             '                    "text"    : "PAGE٥٤EGAP عن أبي عبدالرحمن ... "'
             '                  },'
             '                  ...'
             '                 ]'
             '  }'
             ']')

        """
        with requests.Session() as session:

            try:
                self._login(self._login_action, session, debug)
            except Exception:
                raise 

            # process only one title and finish
            if title is not None:
                out = [self._export_title(title, session, debug)]
                return json.dumps(out, ensure_ascii=False)
        
            # get list of scan pages from wiki index page
            try:
                pages = self._get_titles_scans(session, debug)
            except Exception:
                raise

            # get transcription of all pages
            out = [self._export_title(title, session, debug) for title in pages]

            return json.dumps(out, ensure_ascii=False)

#=============================
#            main             
#=============================

if __name__ == '__main__':

    # parse args
    parser = argparse.ArgumentParser(description='Download scan transliterations from the wiki.')
    parser.add_argument('--title', help='download only the texts belonging to this title')
    parser.add_argument('--debug', action='store_true', help='debug mode')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)

    handler = ExportHandler()
    
    try:
        data = handler.export(args.title, args.debug)
    except Exception as e:

        if args.debug:
            logger.exception(e)

        print('Fatal error in ExportHandler: %s' % e, file=sys.stderr)
        print('Export aborted.', file=sys.stderr)
        sys.exit(1)

    pprint(data)
