#!/usr/bin/env python3


from functools import partial, reduce
from itertools import product
from pathlib import Path
import json
import logging
import multiprocessing.pool as mpp

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).parent

FUZZERS = ('aflfast', 'aflplusplus', 'honggfuzz')
TRIAL_LEN = 10 # Hours
NUM_TRIALS = 5
SEEDS = ('ascii', 'singleton', 'cmin')
FORMATTER = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
NUM_JOBS = NUM_TRIALS

logger = logging.getLogger()


def get_cov(fuzzer: str, seed: str, trial: int) -> pd.DataFrame:
    cov_dir = THIS_DIR / ('readelf-%s' % fuzzer) / ('%s-trial-%d' % (seed, trial)) / 'llvm_cov'
    assert cov_dir.exists()

    count_col = 'region_count_%d' % trial
    percent_col = 'region_percent_%d' % trial

    df = pd.read_csv(cov_dir.parent / 'timestamps.csv')
    df['time'] = df.unix_time - df.unix_time.iloc[0]
    df['dir'] = df.seed.apply(lambda x: Path(x).parent.name)
    df['seed'] = df.seed.apply(lambda x: Path(x).name)
    df[count_col] = np.nan
    df[percent_col] = np.nan

    # Drop crashes
    df = df.drop(df[df.dir == 'crashes'].index)

    for cov_file in sorted(list(cov_dir.glob('*.json'))):
        with cov_file.open() as inf:
            try:
                region_data = json.load(inf)['data'][0]['totals']['regions']
            except json.JSONDecodeError:
                print('unable to read %s. Skipping' % cov_file)
                continue
            reg_covered = region_data['covered']
            reg_count = region_data['count']
        df.loc[df.seed == cov_file.stem, count_col] = reg_covered
        df.loc[df.seed == cov_file.stem, percent_col] = reg_covered * 100.0 / reg_count

    return df.set_index('time')[[count_col, percent_col]]


def main():
    """The main function."""
    # Configure logger
    handler = logging.StreamHandler()
    handler.setFormatter(FORMATTER)
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    with mpp.Pool(processes=NUM_JOBS) as pool:
        for fuzzer, seed in product(FUZZERS, SEEDS):
            # Get raw trial data
            logger.info('Getting %s-%s coverage', fuzzer, seed)
            cov_func = partial(get_cov, fuzzer, seed)
            trials = range(1, NUM_TRIALS + 1)
            cov_data = pool.map(cov_func, trials)

            # Merge trial data and extend to trial length
            logger.info('Merging coverage')
            df = reduce(lambda x,y: x.join(y, how='outer'), cov_data)
            df.loc[TRIAL_LEN * 60 * 60] = np.nan
            df = df.ffill().cummax()

            # Save merged data
            out_path = Path('%s-%s-cov.csv' % (fuzzer, seed))
            logger.info('Saving coverage data to %s', out_path)
            df.to_csv(out_path)


if __name__ == '__main__':
    main()
