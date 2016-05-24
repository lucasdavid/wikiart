# Wikiart Retriever

Full retriever for art and metadata in http://wikiart.org/.
Please read the LICENSE file in the base directory.

## Installation and Usage

First, clone the repository:
```shell
git clone https://github.com/lucasdavid/wikiart
cd wikiart
```

You need to change `settings.py` file to match
your settings.
```shell
vim wikiart/settings.py
```

Variable `BASE_FOLDER` points out to the location in which the data will be
downloaded:
```py
BASE_FOLDER = '/home/ldavid/data/wikiart'
```

Now install and run the software:
```shell
pip install setup.py
wikiart  # Fetch and convert WikiArt.org data into a data set.
# ...
# The data set is waiting for you at /home/ldavid/data/wikiart/1
```

You can also only fetch or convert, as well as executing a new
fetching/conversion instance:
```shell
wikiart fetch --instance 2
# ...
wikiart convert --instance 2
# ...
# The data set will be placed at /home/ldavid/data/wikiart/2
```
