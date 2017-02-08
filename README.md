# Wikiart Retriever

Full retriever for art and metadata in http://wikiart.org/.
Please read the LICENSE file in the base directory.

## Installation and Usage

First, clone the repository:
```shell
git clone https://github.com/lucasdavid/wikiart
cd wikiart
```

You can either run it directly:
```shell
$ python __main__.py --datadir /datasets/wikiart
```
Or install it first and then use it:
```shell
$ pip install setup.py
$ wikiart # equivalent to wikiart fetch && wikiart convert
```

For more information on the options available, run
`python __main__.py --help` or `wikiart --help`.
