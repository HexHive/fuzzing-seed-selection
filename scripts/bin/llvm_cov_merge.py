#!/usr/bin/env python3

"""
Generate and merge llvm-cov coverage from an AFL trial.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from functools import partial
from pathlib import Path
from random import randint
from tempfile import TemporaryDirectory, gettempdir
from typing import List, Optional
import json
import logging
import multiprocessing.pool as mpp
import os
import subprocess

from seed_selection.afl import replace_atat
from seed_selection.argparse import log_level, path_exists, positive_int
from seed_selection.log import get_logger


logger = get_logger('llvm_cov_merge')


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Generate and merge llvm-cov coverage')
    parser.add_argument('-j', '--jobs', type=positive_int, default=1,
                        help='Number of parallel jobs')
    parser.add_argument('-i', '--input', metavar='DIR', type=path_exists,
                        required=True, help='AFL output directory')
    parser.add_argument('-o', '--output', metavar='JSON', type=Path,
                        help='Output JSON')
    parser.add_argument('-l', '--log', type=log_level, default=logging.WARN,
                        help='Logging level')
    parser.add_argument('-t', '--timeout', type=positive_int, default=None,
                        help='Timeout (seconds)')
    parser.add_argument('--summary-only', action='store_true',
                        help='Export only summary information for each source file')
    parser.add_argument('target', metavar='TARGET', type=path_exists,
                        help='LLVM SanitizerCoverage-intrumented target program')
    parser.add_argument('target_args', metavar='ARG', nargs='+',
                        help='Target program arguments')
    return parser.parse_args()


def get_seed_profraw(seed: Path, outdir: Path, target: Path,
                     target_args: List[str], timeout:Optional[int] = None) -> Path:
    """
    Generate the raw coverage profile by replaying the seed through a
    SanitizerCoverage-instrumented target.
    """
    if seed.stat().st_size == 0:
        logger.warning('%s is empty', seed)

    rand_id = randint(0, 99999)
    profraw = outdir / f'{rand_id}-{seed.stem}.profraw'

    env = os.environ.copy()
    env['LLVM_PROFILE_FILE'] = profraw

    target_args_w_seed, found_atat = replace_atat(target_args, seed)
    if not found_atat:
        raise Exception('No seed placeholder `@@` found in target arguments')

    stderr = ''
    try:
        proc = subprocess.run([str(target), *target_args_w_seed], check=False,
                              env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stderr = proc.stderr
        if proc.returncode:
            logger.debug('%s error: %s', seed, stderr.strip())
    except subprocess.TimeoutExpired:
        logger.warning('%s timed out', seed)
    if not profraw.exists():
        raise Exception('Failed to create raw coverage profile for `%s`: %s' %
                        (seed, stderr.strip()))

    return profraw


def merge_profraw(seed_list: Path, profdata: Path, jobs : int = 1) -> None:
    """
    Run llvm-profdata to merge raw coverage profiles (listed in `seed_list`).
    """
    # Find appropriate llvm-profdata
    llvm_profdata = 'llvm-profdata'
    if 'LLVM_PROFDATA' in os.environ:
        llvm_profdata = os.environ['LLVM_PROFDATA']

    llvm_profdata_args = [llvm_profdata, 'merge', '-sparse',
                          '-num-threads', '%d' % jobs,
                          '-f', str(seed_list), '-o', str(profdata)]
    proc = subprocess.run(llvm_profdata_args, check=False, encoding='utf-8',
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise Exception('Failed to merge profile data: %s' %
                        proc.stderr.strip())


def export_json(target: Path, profdata: Path,
                summary_only: bool = False) -> dict:
    """Run llvm-cov to export coverage as JSON."""
    # Find appropriate llvm-cov
    llvm_cov = 'llvm-cov'
    if 'LLVM_COV' in os.environ:
        llvm_cov = os.environ['LLVM_COV']

    llvm_cov_args = [llvm_cov, 'export']
    if summary_only:
        llvm_cov_args.append('-summary-only')
    llvm_cov_args.extend([str(target), '-instr-profile', str(profdata),
                          '-format', 'text'])
    proc = subprocess.run(llvm_cov_args, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    return json.loads(proc.stdout)


def get_temp_dir() -> Path:
    """Determine temporary directory location. Prefer tmpfs if available."""
    root = Path('/')
    preferred_dirs = (root / 'dev' / 'shm', root / 'run' / 'shm')
    for dir_ in preferred_dirs:
        if dir_.exists():
            return dir_

    return Path(gettempdir())


def main():
    """The main function."""
    args = parse_args()
    in_dir = args.input
    output = args.output
    target = args.target

    # Initialize logging
    logger.setLevel(args.log)

    seeds = (seed for queue in in_dir.glob('**/queue') \
             for seed in queue.iterdir() if seed.is_file())

    with TemporaryDirectory(dir=get_temp_dir()) as temp_dir:
        # Generate raw coverage files
        with mpp.Pool(processes=args.jobs) as pool:
            logger.info('Generating raw coverage profiles from %s...', in_dir)
            get_profraw = partial(get_seed_profraw, outdir=Path(temp_dir),
                                  target=target, target_args=args.target_args,
                                  timeout=args.timeout)
            profraws = pool.map(get_profraw, seeds)
            logger.info('Generated %d coverage profiles', len(profraws))

        if not profraws:
            logger.warning('No coverage profiles generated')
            return

        # Create list of seeds for merging
        logger.info('Generating seeds.txt...')
        seed_list = Path(temp_dir) / 'seeds.txt'
        with open(seed_list, 'w') as outf:
            for profraw in profraws:
                outf.write('1,%s\n' % profraw)

        # Merge raw coverage
        logger.info('Merging raw coverage profiles...')
        profdata_file = Path(temp_dir) / 'merged.profdata'
        merge_profraw(seed_list, profdata_file, jobs=args.jobs)

        # Generate JSON
        logger.info('Generating JSON coverage report...')
        summary_only = not(output is not None and not args.summary_only)
        prof_data = export_json(target, profdata_file, summary_only)

    # Save/print JSON
    if output:
        logger.info('Saving JSON report to %s', output)
        with open(output, 'w') as outf:
            json.dump(prof_data, outf)

    region_data = prof_data['data'][0]['totals']['regions']
    region_cvg = region_data['covered'] / region_data['count'] * 100.0
    print('region coverage: %.02f%%' % region_cvg)


if __name__ == '__main__':
    main()
