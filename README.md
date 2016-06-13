# Wiki to TSV converter

Package for exporting transcriptions from the COBHUNI wiki, parsing texts for errors, and converting to TSV format.

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
