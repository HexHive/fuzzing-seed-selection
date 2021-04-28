#!/usr/bin/env python3


from itertools import product
from pathlib import Path

from matplotlib import rc
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


TRIAL_LEN = 10 # Hours
NUM_TRIALS = 5
TIME_INC = 0.5 # Number of seconds between each x-axis point
NUM_BOOTS = 10000
FUZZERS = ('aflfast', 'aflplusplus', 'honggfuzz')
SEEDS = ('ascii', 'singleton', 'cmin')

FUZZER_LABELS = dict(aflfast='AFLFast',
                     aflplusplus='AFL++',
                     honggfuzz='honggfuzz')
SEED_LABELS = dict(ascii='Uninformed',
                   singleton='Valid',
                   cmin='Corpus')

rc('pdf', fonttype=42)
rc('ps', fonttype=42)


def gen_plot_data() -> pd.DataFrame:
    "Generate the data to plot."""
    dfs = []
    trials = range(1, NUM_TRIALS + 1)
    cols = ['region_percent_%d' % trial for trial in trials]

    for fuzzer, seed in product(FUZZERS, SEEDS):
        csv_path = f'{fuzzer}-{seed}-cov.csv'

        print(f'Parsing {csv_path}...')
        df = pd.read_csv(csv_path)
        df = df.loc[~df.time.duplicated(keep='first')]
        df = df.loc[df.time.mod(TIME_INC).between(0, 0.01, inclusive=True)]
        df['time'] = df.time / 60 / 60
        df = df.melt(id_vars='time',
                     value_name='region_percent',
                     value_vars=cols)
        df['Fuzzer'] = FUZZER_LABELS[fuzzer]
        df['Seed'] = SEED_LABELS[seed]

        dfs.append(df)

    return pd.concat(dfs)


def main():
    """The main function."""

    print('Generating plot data...')
    plot_data = gen_plot_data()

    # Do the actual plotting
    print('plotting results...')
    sns.set_theme(style='ticks')
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax = sns.lineplot(ax=ax, data=plot_data, x='time', y='region_percent',
                      hue='Seed', style='Fuzzer', ci=95, n_boot=NUM_BOOTS)

    # Tidy up plot
    xticks = [0, 1, 2, 5, 10] # Hours
    ax.set(xlabel='Time (h)',
           ylabel='Regions (%)',
           xscale='symlog',
           xticks=xticks,
           xticklabels=[f'{x}' for x in xticks])
    ax.set_ylim(bottom=0)
    ax.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.3))
    sns.despine()

    # Save plot
    fig.savefig('readelf-experiment.pdf', bbox_inches='tight')


if __name__ == '__main__':
    main()
