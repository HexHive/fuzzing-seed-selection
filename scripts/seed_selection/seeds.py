"""
Seed size utilities.

Author: Adrian Herrera
"""


from io import TextIOWrapper
from pathlib import Path
from typing import Dict, Optional, Set, TextIO
import csv

from . import datastore


def _download_seed_size_csv():
    content = datastore.get_file(Path('seeds') / 'filesizes.csv')
    return TextIOWrapper(content, encoding='utf-8')


def get_seed_sizes(seeds: Set[str],
                   csv_file: Optional[TextIO] = None) -> Dict[str, int]:
    """
    Get the file sizes for the given seed set.

    If the seed size CSV is provided, use it. Otherwise, download it from the
    datastore.
    """
    # Download the seed sizes CSV if it was not provided
    if not csv_file:
        csv_file = _download_seed_size_csv()

    num_seeds = len(seeds)
    num_sizes = 0
    sizes = dict()

    reader = csv.DictReader(csv_file, fieldnames=('filetype', 'file', 'size'))
    for row in reader:
        if num_sizes == num_seeds:
            break
        if row['file'] in seeds:
            sizes[row['file']] = int(row['size'])
            num_sizes += 1
    return sizes
