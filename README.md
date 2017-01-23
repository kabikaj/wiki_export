# Wiki to json converter

Python program for exporting OCRed and post-corrected texts from the COBHUNI wiki and converting them into json format.

The file config.ini.exmaple in an example of how config.ini looks like without sensitive information.

Main:
  - wiki_to_json.py (entry point)
  - wiki_to_tsv_converter.py  @DEPRECATED

Modules:
  - exporthandler
  - wikiparser
  - tsvconverter2
  - tokenizer  @DEPRECATED

Auxiliary files:
  - util.py
  - config.ini

## Author

Alicia Gonález Martínez

The COBHUNI Project - Universität Hamburg

## Examples of usage

To export all transcriptions from the wiki to json:

```sh
$ python wiki_to_json.py
```

To export an specific trancription from the wiki to json:

```sh
$ python wiki_to_json.py --title Example_for_DjVu_manual_cz-book_color.djvu
```

To export one title to the wiki to tsv2 format (DEPRECATED):

```sh
$ python wiki_to_tsv_converter.py --title Example_for_DjVu_manual_cz-book_color.djvu --outpath ../../data/prepared/
```

## License

Copyright (C) 2016  Alicia González Martínez, aliciagm85+code@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

