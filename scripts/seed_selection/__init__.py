"""
Useful constants.

Author: Adrian Herrera
"""


TARGET_FILE_TYPES = {
    'fts': {
        'freetype2': 'ttf',
        'guetzli': 'jpeg',
        'json': 'json',
        'libarchive': 'gzip',
        'libjpeg-turbo': 'jpeg',
        'libpng': 'png',
        'libxml2': 'xml',
        'pcre2': 'regex',
        're2': 'regex',
        'vorbis': 'ogg',
    },
    'magma': {
        'libpng': 'png',
        'libtiff': 'tiff',
        'libxml2': 'xml',
        'php-exif': 'jpeg',
        'php-json': 'json',
        'php-parser': 'php',
        'poppler': 'pdf',
    },
    'real-world': {
        'freetype2': 'ttf',
        'librsvg': 'svg',
        'libtiff': 'tiff',
        'libxml2': 'xml',
        'poppler': 'pdf',
        'sox-mp3': 'mp3',
        'sox-wav': 'wav',
    },
}

BENCHMARKS = list(TARGET_FILE_TYPES.keys())

MINIMIZE_TECHNIQUES = (
    'cmin',
    'minset',
    'unweighted-optimal',
    'weighted-optimal',
    'weighted-max-freq-optimal')
CORPORA = ('empty', 'full', *MINIMIZE_TECHNIQUES)
