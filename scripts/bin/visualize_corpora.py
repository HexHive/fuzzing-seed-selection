#!/usr/bin/env python3

"""
Visualize the overlap between corpora.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Set, TextIO

from matplotlib import rc, rcParams
from supervenn import supervenn
import matplotlib.pyplot as plt

from seed_selection.argparse import path_exists


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Visualize corpora overlap')
    parser.add_argument('-o', '--output', metavar='PDF', type=Path,
                        required=True)
    parser.add_argument('--cmin', metavar='CORPUS', type=path_exists,
                        default=None)
    parser.add_argument('--full', metavar='CORPUS', type=path_exists,
                        default=None)
    parser.add_argument('--minset', metavar='CORPUS', type=path_exists,
                        default=None)
    parser.add_argument('--unweighted-optimal', metavar='CORPUS',
                        type=path_exists, default=None)
    parser.add_argument('--weighted-optimal', metavar='CORPUS',
                        type=path_exists, default=None)
    parser.add_argument('--weighted-max-freq-optimal', metavar='CORPUS',
                        type=path_exists, default=None)
    return parser.parse_args()


def read_corpus(inf: TextIO) -> Set[str]:
    """Read the given corpus listing as a set of seed names."""
    return {line.strip() for line in inf}


def main():
    """The main function."""
    args = parse_args()

    # Read corpora
    corpora = dict()
    if args.cmin:
        with open(args.cmin, 'r') as inf:
            corpora['CMIN'] = read_corpus(inf)
    if args.full:
        with open(args.full, 'r') as inf:
            corpora['FULL'] = read_corpus(inf)
    if args.minset:
        with open(args.minset, 'r') as inf:
            corpora['MSET'] = read_corpus(inf)
    if args.unweighted_optimal:
        with open(args.unweighted_optimal, 'r') as inf:
            corpora['UOPT'] = read_corpus(inf)
    if args.weighted_optimal:
        with open(args.weighted_optimal, 'r') as inf:
            corpora['WOPT'] = read_corpus(inf)
    if args.weighted_max_freq_optimal:
        with open(args.weighted_max_freq_optimal, 'r') as inf:
            corpora['WMOPT'] = read_corpus(inf)

    # Represent the corpora as a set of integers, where each integer uniquely
    # maps to a seed file
    seed_map = {seed: i for i, seed in enumerate(corpora['FULL'])}

    plot_data = defaultdict(set)
    plot_data['FULL'] = set(seed_map.values())

    for corpus in set(corpora.keys()) - set(['FULL']):
        for seed in corpora[corpus]:
            if seed not in seed_map:
                print('WARN: seed `%s` is not in the FULL corpus' % seed)
                continue
            plot_data[corpus].add(seed_map[seed])

    # Configure plot
    plt.style.use('seaborn-dark')

    x_size, y_size = rcParams['figure.figsize']

    rc('pdf', fonttype=42)
    rc('ps', fonttype=42)

    # Visualize the corpora
    fig = plt.figure(figsize=(x_size, y_size * 0.666))
    ax = fig.add_subplot(1, 1, 1)

    supervenn_data = OrderedDict()
    for corpus in ('FULL', 'MSET', 'CMIN', 'UOPT', 'WOPT', 'WMOPT'):
        if corpus not in plot_data:
            continue
        supervenn_data[corpus] = plot_data[corpus]

    supervenn(list(supervenn_data.values()), list(supervenn_data.keys()),
              ax=ax, side_plots=False, widths_minmax_ratio=0.5)

    ax.set_xlabel('Seeds (#)')
    ax.set_ylabel('Corpora')

    fig.savefig(args.output, bbox_inches='tight')


if __name__ == '__main__':
    main()
