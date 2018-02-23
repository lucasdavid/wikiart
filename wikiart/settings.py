"""WikiArt Retriever Base Settings.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""

# Base Settings

# WikiArt base url.
BASE_URL = 'https://www.wikiart.org/en/App'

# Base folder in which the files will be saved.
BASE_FOLDER = './wikiart-saved/'

# Format in which the images will be saved.
SAVE_IMAGES_IN_FORMAT = '.jpg'

# Request Settings

# WikiArt supposedly blocks users that make more than 10 requests within 5
# seconds. The following parameters are used to control the frequency of
# these same requests.
# Number of requests made before checking if the process should slow down.
REQUEST_STRIDE = 10
# Minimum delta time between two consecutive request strides.
REQUEST_PADDING_IN_SECS = 5

# Maximum time (in secs) before canceling a download.
METADATA_REQUEST_TIMEOUT = 2 * 60
PAINTINGS_REQUEST_TIMEOUT = 5 * 60

# Data Set Conversion Settings

# Set which attributes are considered when converting the paintings json files
# to a more common data set format.
PAINTING_ATTRIBUTES = (
    'contentId', 'url', 'style', 'genre', 'artistContentId', 'artistUrl')

PAINTINGS_HEADER = """
=======================
WikiArt Data Set Images
=======================

This data set was created from paintings extracted from WikiArt.org.

Please refer to https://github.com/lucasdavid/wikiart for more information
or to report a bug.

%s
""" % ','.join(PAINTING_ATTRIBUTES)

# Set which attributes are considered when converting the artists' attributes
# to a more common data set format.
ARTIST_ATTRIBUTES = (
    'contentId', 'url', 'artistName', 'lastNameFirst', 'image', 'wikipediaUrl',
    'birthDay', 'deathDay', 'birthDayAsString', 'deathDayAsString',
)

# Header of generated file labels.data.
LABELS_HEADER = """
=======================
WikiArt Data Set Labels
=======================

This data set was created from paintings extracted from WikiArt.org.

Please refer to https://github.com/lucasdavid/wikiart for more information
or to report a bug.

%s
""" % ','.join(ARTIST_ATTRIBUTES)
