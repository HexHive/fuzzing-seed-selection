#!/usr/bin/env python3

"""
Compute AUC for AFL coverage files.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TextIO
import os

from sklearn import metrics
import bootstrapped.bootstrap as bs
import bootstrapped.stats_functions as bs_stats
import numpy as np
import pandas as pd


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Calculate AUC of AFL coverage')
    parser.add_argument('-p', '--percentile', type=float, default=1.0,
                        help='Coverage percentile (as fraction 0 < p <= 1')
    parser.add_argument('plot_data', nargs='+', type=Path,
                        help='Path to AFL plot_data file(s)')
    return parser.parse_args()


def read_plot_data(in_file: TextIO) -> pd.DataFrame:
    """Read an AFL `plot_data` file."""
    def fix_map_size(x):
        if isinstance(x, str):
            return float(x.split('%')[0])
        return x

    # Skip the opening '# ' (if it exists)
    pos = in_file.tell()
    first_chars = in_file.read(2)
    if first_chars != '# ':
        in_file.seek(pos)

    # Read the data
    df = pd.read_csv(in_file, index_col=False, skipinitialspace=True)
    df.map_size = df.map_size.apply(fix_map_size)

    return df


def main():
    """The main function."""
    args = parse_args()
    plot_data_paths = args.plot_data
    num_plot_datas = len(plot_data_paths)

    aucs = []

    for plot_data_path in plot_data_paths:
        if plot_data_path.stat().st_size == 0:
            continue

        with plot_data_path.open() as inf:
            df = read_plot_data(inf)
            if df.empty:
                continue

        df['unix_time'] = df.unix_time - df.unix_time.iloc[0]

        total_cov = df.map_size.iloc[-1]
        percentile_cov = total_cov * args.percentile
        df_percentile = df[df.map_size <= percentile_cov]
        if len(df_percentile) < 2:
            df_percentile = df[0:2]

        auc = metrics.auc(df_percentile.unix_time, df_percentile.map_size)
        aucs.append(auc)

    # Compute the mean AUC and confidence intervals
    auc_ci = bs.bootstrap(np.array(aucs), stat_func=bs_stats.mean)
    print(f'mean AUC ({num_plot_datas} plot_data files)')
    print(f'  {auc_ci.value:.02f} +/- {auc_ci.error_width() / 2:.02f}')


if __name__ == '__main__':
    main()
