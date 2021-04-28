#!/usr/bin/env python3

"""
Replay a directory of fuzzer inputs and generate coverage information. Store
this coverage (along with size and execution time metadata) in an HDF5 file.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from pathlib import Path
from shutil import copy, which
from subprocess import run
from tempfile import NamedTemporaryFile
from time import time
from typing import List, Tuple
import re

from h5py import File as H5File
from tqdm import tqdm
import numpy as np

from seed_selection.afl import replace_atat
from seed_selection.argparse import mem_limit, path_exists, positive_int


MEM_LIMIT_RE = re.compile(r'''(\d+)([TGkM]?)''')
COV_TYPE = np.dtype([('edge', np.uint32), ('count', np.uint8)])


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Generate AFL coverage from a seed '
                                        'directory')
    parser.add_argument('-i', '--input', metavar='DIR', type=path_exists,
                        required=True, help='Path to input directory')
    parser.add_argument('-o', '--output', metavar='HDF5', type=Path,
                        required=True, help='Path to output HDF5')
    parser.add_argument('-s', '--traces', metavar='DIR', type=path_exists,
                        help='Save the traces to the given directory')
    parser.add_argument('-t', '--timeout', type=positive_int, default=None,
                        help='Timeout for each run')
    parser.add_argument('-m', '--memory', type=mem_limit, default=None,
                        help='Memory limit for child process')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Sink program output')
    parser.add_argument('target', metavar='TARGET', type=path_exists,
                        help='Target program')
    parser.add_argument('target_args', metavar='ARG', nargs='+',
                        help='Target program arguments')
    return parser.parse_args()


def run_showmap(afl_showmap: Path, seed: Path, **kwargs: dict) -> (np.array, float):
    """Run afl-showmap on a given file."""
    cov = np.empty(0, dtype=COV_TYPE)
    args = [afl_showmap]

    timeout = kwargs.get('timeout')
    memory = kwargs.get('memory')

    if timeout:
        args.extend(['-t', str(timeout)])
    if memory:
        args.extend(['-m', str(memory)])
    if kwargs['quiet']:
        args.append('-q')

    target_args_w_seed, found_atat = replace_atat(kwargs['target_args'], seed)
    if not found_atat:
        raise Exception('No seed placeholder `@@` found in target arguments')

    with NamedTemporaryFile() as temp:
        args.extend(['-o', temp.name])
        args.extend(['--', kwargs['target'], *target_args_w_seed])

        start_time = time()
        run(args, check=False)
        end_time = time()

        exec_time_ms = (end_time - start_time) * 1000

        # Successfully generated coverage
        if Path(temp.name).stat().st_size != 0:
            with open(temp.name, 'r') as trace_data:
                cov = np.genfromtxt(trace_data, delimiter=':', dtype=COV_TYPE)

            # Save the seed trace if requested
            trace_dir = kwargs['traces']
            if trace_dir:
                copy(temp.name, trace_dir / seed.name)

    return cov, exec_time_ms


def main():
    """The main function."""
    args = parse_args()

    in_dir = args.input
    out_path = args.output
    num_seeds = len(list(in_dir.glob('*')))

    afl_showmap = which('afl-showmap')
    if not afl_showmap:
        raise Exception('Cannot find `afl-showmap`. Check PATH')

    with H5File(out_path, 'w') as h5f:
        for seed in tqdm(in_dir.iterdir(),
                         desc='Generating `afl-showmap` coverage',
                         total=num_seeds, unit='seeds'):
            cov, exec_time = run_showmap(afl_showmap, seed, **vars(args))
            if cov.size == 0:
                continue

            compression = 'gzip' if cov.size > 1 else None
            dset = h5f.create_dataset(str(seed.relative_to(in_dir)),
                                      data=cov, compression=compression)
            dset.attrs['time'] = exec_time
            dset.attrs['size'] = seed.stat().st_size


if __name__ == '__main__':
    main()
