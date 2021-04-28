#!/usr/bin/env python3

"""
Generate llvm-cov coverage statistics.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from pathlib import Path
import json

from bootstrapped import bootstrap as bs
import bootstrapped.stats_functions as bs_stats
import numpy as np

from seed_selection.argparse import path_exists


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Generate llvm-cov statistics')
    parser.add_argument('jsons', metavar='JSON', nargs='+', type=path_exists,
                        help='llvm-cov-generated JSON coverage file(s)')
    return parser.parse_args()


def get_region_cov(llvm_cov_json: Path) -> float:
    """Get region coverage from the llvm-cov-generated JSON file."""
    with llvm_cov_json.open() as inf:
        root = json.load(inf)
        data = root['data'][0]['totals']['regions']
        return data['covered'] / data['count'] * 100.0


def main():
    """The main function."""
    args = parse_args()

    # Get region coverage
    regions = np.array([get_region_cov(p) for p in args.jsons])

    # Calculate mean and confidence intervals
    cov_ci = bs.bootstrap(regions, stat_func=bs_stats.mean)

    # Output
    print('mean coverage (%d trials)' % len(regions))
    print(f'{cov_ci.value:.02f} +/- {cov_ci.error_width() / 2:.02f}')


if __name__ == '__main__':
    main()
