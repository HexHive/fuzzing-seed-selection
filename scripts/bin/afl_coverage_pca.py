#!/usr/bin/env python3

"""
Generate PCA plot for the given coverage HDF5 file.

Author: Adrian Herrera
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys

from h5py import File as H5File
from matplotlib import rc
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from seed_selection.argparse import path_exists


# From afl/config.h
MAP_SIZE_POW2 = 16
MAP_SIZE = 1 << MAP_SIZE_POW2


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='PCA plots of coverage data')
    parser.add_argument('-i', '--input', metavar='HDF5', type=path_exists,
                        required=True, help='Input HDF5 file')
    parser.add_argument('-o', '--output', metavar='PDF', type=Path,
                        required=True, help='Path to output PDF')
    return parser.parse_args()


def main():
    """The main function."""
    args = parse_args()

    in_hdf5 = args.input
    out_pdf = args.output

    print('Reading %s...' % in_hdf5)
    cov_data = {}
    with H5File(in_hdf5, 'r') as h5_file:
        for cov_file, cov in h5_file.items():
            df_cov = np.zeros(MAP_SIZE, dtype=np.uint8)
            if len(cov.shape) == 0:
                edge, count = cov[()]
                df_cov[edge] = count
            else:
                for edge, count in cov:
                    df_cov[edge] = count
            cov_data[cov_file] = list(df_cov)

    df = pd.DataFrame.from_dict(cov_data, orient='index')
    x = StandardScaler().fit_transform(df)
    if len(df) <= 1:
        sys.stderr.write('Not enough seeds to perform PCA')
        sys.exit(1)

    # Compute PCA
    # TODO determine the number of components
    print('Computing PCA...')
    pca = PCA(n_components=2)
    pca_scores = pd.DataFrame(pca.fit_transform(x),
                              columns=['PCA 1', 'PCA 2']).set_index(df.index)

    # Configure plot
    rc('pdf', fonttype=42)
    rc('ps', fonttype=42)
    plt.style.use('ggplot')

    # Plot PCA
    print('Plotting...')
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter(pca_scores['PCA 1'], pca_scores['PCA 2'], marker='x', alpha=0.5)
    ax.set_xlabel('Component 1')
    ax.set_ylabel('Component 2')

    fig.savefig(out_pdf, bbox_inches='tight')
    print('%s coverage plotted at %s' % (in_hdf5, out_pdf))


if __name__ == '__main__':
    main()
