#!/usr/bin/env python3

"""
Get the timestamps and sizes for all honggfuzz-generated files.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from csv import DictWriter
from pathlib import Path
import os
from typing import Dict


FIELDNAMES = ('seed', 'size', 'unix_time')


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Get timestamps and file sizes for '
                                        'fuzzer results')
    parser.add_argument('-o', '--output', type=Path, required=True,
                        help='Path to output CSV file')
    parser.add_argument('out_dir', type=Path, metavar='OUT_DIR',
                        help='honggfuzz output directory')
    return parser.parse_args()

def check_suffix(seed: Path) -> bool:
    """Check if the file suffix is one that we are interested in."""
    suffixes = seed.suffixes

    if len(suffixes) > 2 and ''.join(suffixes[-2:]) == '.honggfuzz.cov':
        return True
    if len(suffixes) > 1 and suffixes[-1] == '.fuzz':
        return True

    return False


def timestamp_results(out_dir: Path) -> Dict[str, int]:
    """Timestamp the results of honggfuzz."""
    stats = []

    for root, dirs, files in os.walk(out_dir):
        # Ignore hidden directories
        dirs[:] = [d for d in dirs if not d[0] == '.']

        for name in files:
            seed = Path(root) / name
            if not check_suffix(seed):
                continue

            ctime = seed.stat().st_ctime

            stat_dict = dict(seed=str(seed), unix_time=ctime,
                             size=seed.stat().st_size)
            stats.append(stat_dict)

    return stats


def main():
    """The main function."""
    args = parse_args()

    stats = timestamp_results(args.out_dir)
    stats.sort(key=lambda d: d['unix_time'])

    # Write the results to the output CSV file
    with open(args.output, 'w') as outf:
        writer = DictWriter(outf, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(stats)


if __name__ == '__main__':
    main()
