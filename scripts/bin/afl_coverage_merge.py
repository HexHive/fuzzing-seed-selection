#!/usr/bin/env python3

"""
Merge AFL coverage across multiple parallel nodes.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace

from seed_selection.argparse import path_exists


# Taken from AFL's config.h
MAP_SIZE_POW2 = 16
MAP_SIZE = 1 << MAP_SIZE_POW2


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Merge AFL coverage')
    parser.add_argument('output', metavar='AFL_OUT', nargs='+', type=path_exists,
                        help='AFL output directory')
    return parser.parse_args()


def main():
    """The main function."""
    args = parse_args()

    # Read and merge bitmaps. The merged bitmap only indicates (via a boolean)
    # whether an edge tuple was hit or not (i.e., edge counts are discarded)
    merged_bitmap = [False] * MAP_SIZE
    for out in args.output:
        with open(out / 'fuzz_bitmap', 'rb') as inf:
            bitmap = inf.read()
            for i, byte in enumerate(bitmap):
                if byte != 255:
                    merged_bitmap[i] = True

    # Calculate merged coverage
    bitmap_cvg = (sum(merged_bitmap) * 100.0) / MAP_SIZE
    print('bitmap_cvg: %.02f%%' % bitmap_cvg)


if __name__ == '__main__':
    main()
