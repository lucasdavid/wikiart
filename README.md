# Wikiart Retriever

Full retriever for art and metadata in http://wikiart.org/.
Please read the LICENSE file in the base directory.

## Usage
The command bellow will fetch and convert all data available at WikiArt
into a "dataset-y" representation:
```shell
$ python3 wikiart.py --datadir ./data  # saves in ./data/
```

If you had to stop the downloading process, for some reason, you can resume it by simply
`python3 wikiart.py --datadir ./output`. The program wil scan `--datadir` and only download
what's not there yet. Additionally, you can **only** download or convert the data with
`python3 wikiart.py fetch` and `python3 wikiart.py convert`, respectively.
For more information on the options available, run `python wikiart.py --help`.

### Download Paintings from Specific Artists
If you want the paintings of specific painters (instead of the entire wikiart), you could:

```
python3 wikiart.py --datadir ./wikiart-saved/ fetch --only <artist name>
```

Artist name can be any part of the artist name. You can also download multiple artists' paintings
with a single query (Eg. William)
