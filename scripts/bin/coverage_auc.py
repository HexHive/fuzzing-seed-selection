#!/usr/bin/env python3

"""
Compute AUC for AFL coverage files.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from pathlib import Path
import os

from sklearn import metrics
import bootstrapped.bootstrap as bs
import bootstrapped.stats_functions as bs_stats
import numpy as np
import pandas as pd

from fuzz_analysis.fuzzers.afl.plot_data import PlotData


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Calculate AUC of AFL coverage')
    parser.add_argument('plot_data', nargs='+', type=Path,
                        help='Path to AFL plot_data file(s)')
    return parser.parse_args()


def main():
    """The main function."""
    args = parse_args()
    plot_data_paths = args.plot_data
    num_plot_datas = len(plot_data_paths)

    common_dir = Path(*os.path.commonprefix([p.parts for p in plot_data_paths]))
    aucs = []

    for plot_data_path in plot_data_paths:
        if plot_data_path.stat().st_size == 0:
            continue

        with plot_data_path.open() as inf:
            df = PlotData.read(inf)
            if df.empty:
                continue

            df['unix_time'] = df.unix_time - df.unix_time.iloc[0]

            auc = metrics.auc(df.unix_time, df.map_size)
            aucs.append(auc)

    # Compute the mean AUC and confidence intervals
    auc_ci = bs.bootstrap(np.array(aucs), stat_func=bs_stats.mean)
    print(f'mean AUC ({num_plot_datas} plot_data files)')
    print(f'  {auc_ci.value:.02f} +/- {auc_ci.error_width() / 2:.02f}')


if __name__ == '__main__':
    main()
