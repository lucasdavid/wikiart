# Wikiart Retriever

Full retriever for art and metadata in http://wikiart.org/.
Please read the LICENSE file in the base directory.

## Usage

The command bellow will fetch and convert all data available at WikiArt
into a "dataset-y" representation:
```shell
$ python3 wikiart.py # saves in ./wikiart-saved/
$ # Or...
$ python3 wikiart.py --datadir /datasets/wa  # saves in /datasets/wa/
```

If you had to stop the downloading process, for some reason,
you can resume it by simply `python3 wikiart.py --datadir ./output`.
 The program wil scan `--datadir` and only download what's not there yet.

Additionally, you can **only** download or convert the data with
`python3 wikiart.py fetch` and `python3 wikiart.py convert`, respectively.

For more information on the options available, run
`python wikiart.py --help`.

If you install this project with `python3 setup.py install`,
you will be able to use the `wikiart` command as an alias for
`python wikiart.py`:
```shell
$ wikiart --datadir /datasets/wa
```

### Download Paintings from Specific Artists

If you want the paintings of specific painters (instead of the entire wikiart), you could:

1. Run the command `python3 wikiart.py --datadir ./wikiart-saved/ fetch --only artists`. This will download `./wikiart-saved/meta/artists.json`, a small file containing a list of all painters in wikiart.
2. Open `./wikiart-saved/meta/artists.json` and remove the entries of the artists that you DO NOT wish to download.
3. Run `python3 wikiart.py --datadir ./wikiart-saved/ fetch`. This will download the paintings from the artists that weren't removed from the list.
