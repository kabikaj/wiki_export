# Wiki to TSV converter

Package for exporting transcriptions from the COBHUNI wiki, parsing texts for errors, and converting to TSV format.

Modules:
  - wiki_to_tsv_converter.py (entry point)
  - exporthandler
  - wikiparser
  - tsvconverter2
  - tsvconverter3
  - tokenizer

## Examples of usage

To export all transcriptions from the wiki, in tsv2 format:

```sh
$ python wiki_to_tsv_converter.py --tsv2
```

To export a specific trancription from the wiki, in tsv3 format:

```sh
$ python wiki_to_tsv_converter.py --title Example_for_DjVu_manual_cz-book_color.djvu --tsv3
```



