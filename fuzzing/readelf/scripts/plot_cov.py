#!/usr/bin/env python3


from itertools import product
from pathlib import Path
import gzip

from matplotlib import rc, rcParams
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


DATA_DIR = Path(__file__).parent.parent / 'data'


TRIAL_LEN = 10 # Hours
PLOT_STEP = 10 # Seconds
NUM_TRIALS = 5
NUM_BOOTS = 2000
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

rc_fonts = {
    'font.family': 'serif',
    'text.usetex': True,
    'text.latex.preamble':
        r"""
        \RequirePackage[T1]{fontenc}
        \RequirePackage[tt=false, type1=true]{libertine}
        \RequirePackage[varqu]{zi4}
        \RequirePackage[libertine]{newtxmath}
        """,
}
rcParams.update(rc_fonts)


def gen_plot_data() -> pd.DataFrame:
    "Generate the data to plot."""
    dfs = []
    trials = range(1, NUM_TRIALS + 1)
    cols = ['region_percent_%d' % trial for trial in trials]

    for fuzzer, seed in product(FUZZERS, SEEDS):
        csv_path = DATA_DIR / f'{fuzzer}-{seed}-cov.csv.gz'

        print(f'Parsing {csv_path}...')
        with gzip.open(csv_path, 'rb') as inf:
            df = pd.read_csv(inf).set_index('time')

        df = df.loc[~df.index.duplicated(keep='first')]
        new_idx = pd.RangeIndex(start=0, stop=TRIAL_LEN * 60 * 60,
                                step=PLOT_STEP)
        df = df.reindex(new_idx, method='ffill')
        df.index = df.index / 60 / 60
        df['time'] = df.index
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
           ylabel='Regions (\%)',
           xscale='symlog',
           xticks=xticks,
           xticklabels=[f'{x}' for x in xticks])
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0, right=TRIAL_LEN)
    ax.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.3))
    sns.despine()

    # Save plot
    fig.savefig('readelf-experiment.pdf', bbox_inches='tight')


if __name__ == '__main__':
    main()
