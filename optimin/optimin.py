#!/usr/bin/env python3

"""
Wrapper around OptiMin.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from pathlib import Path
from shutil import which
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, TextIO, Tuple
import re
import subprocess


WCNF_SEED_MAP_RE = re.compile(r'^c (\d+) : (.+)$')


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Run OptiMin to produce a minimized corpus')
    parser.add_argument('-j', '--jobs', type=int, default=0,
                        help='Number of minimization threads')
    parser.add_argument('-e', '--edge-only', action='store_true',
                        help='Use edge coverage only, ignore hit counts')
    parser.add_argument('-w', '--weights', metavar='CSV', type=Path,
                        help='Path to weights CSV')
    parser.add_argument('corpus', type=Path, help='Path to input corpus')
    return parser.parse_args()


def get_seed_mapping(inf: TextIO) -> Dict[int, str]:
    """
    Retrieve the mapping of literal identifiers (integers) to seed names
    (strings) from the WCNF file.
    """
    mapping = {}
    for line in inf:
        # This starts the constraint listing
        if line.startswith('p wcnf '):
            break

        match = WCNF_SEED_MAP_RE.match(line.strip())
        if not match:
            continue

        mapping[int(match.group(1))] = match.group(2)

    return mapping


def parse_maxsat_out(out: List[str], mapping: Dict[int, str]) -> Tuple[Optional[List[str]], Optional[float]]:
    """
    Parse the output from EvalMaxSat.

    Returns a tuple containing:

    1. The list of seeds that make up the solution, or `None` if a solution
    could not be found.
    2. The execution time.
    """
    solution = None
    exec_time = None

    for line in out:
        # Solution status
        if line.startswith('s ') and 'OPTIMUM FOUND' not in line:
            # No optimum solution found
            break

        # Solution values
        if line.startswith('v '):
            vals = [int(v) for v in line[2:].split(' ')]
            solution = [mapping[v] for v in vals if v > 0]

        # Execution time
        if line.startswith('c Total time: '):
            toks = line.split(' ')
            exec_time = float(toks[3])
            units = toks[4]

            # TODO other units to worry about?
            if units == 'ms':
                exec_time = exec_time / 1000

    return solution, exec_time


def main():
    """The main function."""
    args = parse_args()

    # Check binaries are available
    optimin = which('afl-showmap-maxsat')
    if not optimin:
        raise Exception('Cannot find OptiMin. Check PATH')
    eval_max_sat = which('EvalMaxSAT_bin')
    if not eval_max_sat:
        raise Exception('Cannot find EvalMaxSAT. Check PATH')

    # Configure optimin
    optimin_args = [optimin, '-p']
    if args.edge_only:
        optimin_args.append('-e')
    if args.weights:
        optimin_args.extend(['-w', str(args.weights)])

    with NamedTemporaryFile() as wcnf:
        print(f'[*] Running Optimin on {args.corpus}')
        optimin_args.extend(['-o', wcnf.name, '--', str(args.corpus)])
        subprocess.run(optimin_args, check=True)

        with open(wcnf.name, 'r') as inf:
            seed_map = get_seed_mapping(inf)

        print('[*] Running EvalMaxSAT on WCNF')
        proc = subprocess.run([eval_max_sat, wcnf.name, '-p', f'{args.jobs}'],
                              check=True, stdout=subprocess.PIPE,
                              encoding='utf-8')
        print('[+] EvalMaxSAT completed')
        maxsat_out = [line.strip() for line in proc.stdout.split('\n')]

        print('[*] Parsing EvalMaxSAT output')
        solution, exec_time = parse_maxsat_out(maxsat_out, seed_map)
        if not solution:
            raise Exception(f'Unable to find optimum solution for {args.corpus}')

        print(f'[+] Solution found for {args.corpus}\n')
        print('[+] Total time: %.02f sec' % exec_time)
        print(f'[+] Num. seeds: {len(solution)}\n')

        print('\n'.join(solution))


if __name__ == '__main__':
    main()
