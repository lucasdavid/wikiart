# Wikiart Retriever

Full retriever for art and metadata in http://wikiart.org/.
Please read the LICENSE file in the base directory.

## Usage

The command bellow will fetch and convert all data available at WikiArt
into a "dataset-y" representation:
```shell
$ python3 __main__.py # saves data in ./wikiartds
$ # Or...
$ python3 __main__.py --datadir ./output
```

If you had to stop the downloading process, for some reason,
you can resume it by simply `python3 __main__.py --datadir ./output`.
 The program wil scan `--datadir` and only download what's not there yet.
 
Additionally, you can **only** download or convert the data with
`python3 __main__.py fetch` and `python3 __main__.py convert`, respectively.

For more information on the options available, run
`python __main__.py --help`.

If you install this project with `python3 setup.py install`,
you will be able to use `wikiart` as an alias for `python __main__.py`.
