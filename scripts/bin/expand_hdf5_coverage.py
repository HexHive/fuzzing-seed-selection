#!/usr/bin/env python3

"""
Extract AFL coverage from an HDF5 file.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Set, TextIO
import logging

from h5py import File

from seed_selection.argparse import log_level, path_exists, positive_int
from seed_selection.coverage import expand_hdf5
from seed_selection.log import get_logger


logger = get_logger('extract_coverage')


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Create a directory of AFL coverage '
                                        'data from an HDDF5 file')
    parser.add_argument('-j', '--jobs', type=positive_int, default=1,
                        help='Number of parallel jobs')
    parser.add_argument('-i', '--input', metavar='HDF5', type=path_exists,
                        required=True, help='Input HDF5 file')
    parser.add_argument('-l', '--log', type=log_level, default=logging.WARN,
                        help='Logging level')
    parser.add_argument('-o', '--output', metavar='DIR', required=True,
                        type=Path, help='Output directory')
    parser.add_argument('-s', '--seeds', type=path_exists,
                        help='Optional text file containing a list of seeds to '
                             'extract')
    return parser.parse_args()


def get_seeds(inf: TextIO) -> Set[str]:
    """Get a list of seeds (one per line)."""
    return {line.strip() for line in inf}


def main():
    """The main function."""
    args = parse_args()
    in_file = args.input
    out_dir = args.output

    # Initialize logging
    logger.setLevel(args.log)

    # Determine the specific seeds to extract
    seeds = None
    if args.seeds:
        with open(args.seeds, 'r') as inf:
            seeds = get_seeds(inf)

    # Extract the seed coverage from the HDF5 file
    out_dir.mkdir(exist_ok=True)
    extracted_seeds = set()

    logger.info('Getting seed coverage (%d jobs)', args.jobs)
    with File(in_file, 'r') as h5f:
        for seed in expand_hdf5(h5f, out_dir, seeds, jobs=args.jobs,
                                progress=True):
            extracted_seeds.add(seed)
    logger.info('Extracted coverage for %d seeds', len(extracted_seeds))


if __name__ == '__main__':
    main()
