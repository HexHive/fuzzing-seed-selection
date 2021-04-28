#!/usr/bin/env python3

"""
Wrapper around EvalMaxSAT.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from shutil import which
from typing import Dict, Optional, List, TextIO, Tuple
import logging
import re
import subprocess
import sys

from seed_selection.argparse import log_level, path_exists, positive_int
from seed_selection.log import get_logger


WCNF_SEED_MAP_RE = re.compile(r'^c (\d+) : (.+)$')

logger = get_logger('run_maxsat')


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Run EvalMaxSAT on a corpus WCNF')
    parser.add_argument('-l', '--log', type=log_level, default=logging.WARN,
                        help='Logging level')
    parser.add_argument('-j', '--jobs', type=positive_int, default=0,
                        help='Number of minimization threads')
    parser.add_argument('input', metavar='WCNF', type=path_exists,
                        help='Path to input WCNF')
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
    in_file = args.input

    eval_max_sat = which('EvalMaxSAT_bin')
    if not eval_max_sat:
        raise Exception('Cannot find EvalMaxSAT_bin. Check PATH')

    # Intitialize logging
    logger.setLevel(args.log)

    logger.debug('Retrieving literal/seed mapping from %s', in_file)
    with open(in_file, 'r') as inf:
        seed_map = get_seed_mapping(inf)

    logger.debug('Running EvalMaxSAT on %s', in_file)
    proc = subprocess.run([eval_max_sat, in_file, '-p', '%d' % args.jobs],
                          check=True, stdout=subprocess.PIPE, encoding='utf-8')
    logger.debug('EvalMaxSAT completed')
    maxsat_out = [line.strip() for line in proc.stdout.split('\n')]

    logger.debug('Parsing EvalMaxSAT output')
    solution, exec_time = parse_maxsat_out(maxsat_out, seed_map)
    if not solution:
        raise Exception('Unable to find optimum solution for %s' % in_file)

    print('[+] Solution found for %s' % in_file, file=sys.stderr)
    print('[+] Total time: %.02f sec' % exec_time, file=sys.stderr)
    print('[+] Num. seeds: %d\n' % len(solution), file=sys.stderr)

    print('\n'.join(solution))


if __name__ == '__main__':
    main()
