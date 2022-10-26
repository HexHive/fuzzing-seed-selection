#!/usr/bin/env python3

"""
Download a specific seed corpus.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from io import BytesIO, StringIO
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory
from typing import Set
import logging
import shutil

from tqdm import tqdm

from seed_selection import BENCHMARKS, CORPORA, TARGET_FILE_TYPES
from seed_selection.argparse import log_level, path_exists
from seed_selection.log import get_logger
from seed_selection import datastore


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
    logger.info('Getting seed list from datastore')

    # Get the corpus file
    seed_path = Path('corpora') / benchmark / target / f'{corpus}.txt'
    seed_data = datastore.get_file(seed_path).decode('utf-8')
    logger.debug('Downloaded corpus seed file')

    # Now create the paths to the seeds
    filetype = TARGET_FILE_TYPES[benchmark][target]
    seeds = set()
    with StringIO(seed_data) as inf:
        for line in inf:
            seed = line.strip()
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

    # Download seeds
    logger.info('Downloading %s', archive_name)
    data = datastore.get_file(Path('seeds') / archive_name, progbar=True)
    with BytesIO(data) as bio:
        logger.info('Extracting seeds from %s', archive_name)
        with TarFile.open(fileobj=bio, mode='r:xz') as tf, \
                TemporaryDirectory() as td:
            logger.info('Extract all seeds to temp dir %s', td)
            
            import os
            
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tf, td)

            for seed in tqdm(seeds, desc=f'Copying seeds to {out_dir}',
                             unit='seeds'):
                shutil.copy(Path(td) / seed, out_dir)

    logger.info('Successfully created %s corpus for %s - %s at %s', corpus,
                benchmark, target, out_dir)


if __name__ == '__main__':
    main()
