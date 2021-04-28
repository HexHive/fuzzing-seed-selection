#!/usr/bin/env python3

"""
Download a specific seed corpus.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from io import BytesIO
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory, TemporaryFile
from typing import Set
import logging
import shutil

from tqdm import tqdm

from seed_selection import BENCHMARKS, CORPORA, TARGET_FILE_TYPES
from seed_selection.argparse import log_level, path_exists
from seed_selection.log import get_logger
from seed_selection import cloudstor, osf


logger = get_logger('get_corpus')


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Create a corpus for a given '
                                        'benchmark\'s target')
    parser.add_argument('-b', '--benchmark', choices=BENCHMARKS, required=True,
                        help='The benchmark')
    parser.add_argument('-c', '--corpus', choices=CORPORA, default='full',
                        help='The corpus type to download')
    parser.add_argument('-l', '--log', type=log_level, default=logging.WARN,
                        help='Logging level')
    parser.add_argument('-t', '--target', type=str, required=True,
                        help='The benchmark target')
    parser.add_argument('output', metavar='DIR', type=path_exists,
                        help='Path to output directory')
    return parser.parse_args()


def get_seeds(benchmark: str, target: str, corpus: str) -> Set[Path]:
    """Get the list of seeds for the given corpus."""
    logger.info('Getting seed list from OSF')
    store = osf.connect()

    # Get the corpus file
    seed_path = Path('corpora') / benchmark / target / f'{corpus}.txt'
    seed_file = osf.get_file(store, seed_path)
    logger.debug('Found corpus file `%s`', seed_file.path)

    # Now create the paths to the seeds (which are stored in cloudstor)
    filetype = TARGET_FILE_TYPES[benchmark][target]
    seeds = set()
    with TemporaryFile('r+b') as outf:
        seed_file.write_to(outf)

        outf.seek(0)
        for line in outf:
            seed = line.strip().decode('utf-8')
            seeds.add(Path(filetype) / seed)
    logger.info('Read %d seeds from seed list', len(seeds))

    return seeds


def main():
    """The main function."""
    args = parse_args()
    benchmark = args.benchmark
    corpus = args.corpus
    target = args.target
    out_dir = args.output

    # Validate that the target is in the benchmark
    if target not in TARGET_FILE_TYPES[benchmark]:
        raise Exception('Target `%s` is not valid for the `%s` benchmark' %
                        (target, benchmark))
    filetype = TARGET_FILE_TYPES[benchmark][target]

    # Initialize logging
    logger.setLevel(args.log)

    # Get the list of seeds for the given benchmark target. Need special
    # handling for the empty corpus :(
    if corpus == 'empty':
        seeds = [Path('empty') / f'empty.{filetype}']
        archive_name = 'empty.tar.xz'
    else:
        seeds = get_seeds(benchmark, target, corpus)
        archive_name = '%s.tar.xz' % filetype

    # Connect to cloudstor and download seeds
    client = cloudstor.connect()
    with BytesIO() as bio:
        logger.info('Downloading %s', archive_name)
        client.download_from(bio, archive_name)
        bio.seek(0)

        logger.info('Extracting seeds from %s', archive_name)
        with TarFile.open(fileobj=bio, mode='r:xz') as tf, \
                TemporaryDirectory() as td:
            logger.info('Extract all seeds to temp dir %s', td)
            tf.extractall(td)

            for seed in tqdm(seeds, desc=f'Copying seeds to {out_dir}',
                             unit='seeds'):
                shutil.copy(Path(td) / seed, out_dir)

    logger.info('Successfully created %s corpus for %s - %s at %s', corpus,
                benchmark, target, out_dir)


if __name__ == '__main__':
    main()
