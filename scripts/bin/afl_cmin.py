#!/usr/bin/env python3

"""
Wrapper around `afl-cmin`. Only keeps the names of the files in the minimized
corpus.

Author: Adrian Herrera
"""


from getopt import getopt
from pathlib import Path
from shutil import which
from subprocess import run
from tempfile import TemporaryDirectory
import os
import sys


def main():
    """The main function."""
    opts, args = getopt(sys.argv[1:], '+i:f:m:t:eQC')

    cmin = which('afl-cmin')
    if not cmin:
        raise Exception('afl-cmin not found. Check PATH')

    env = os.environ.copy()
    env['AFL_ALLOW_TMP'] = '1'

    ret = 1

    with TemporaryDirectory() as temp_dir:
        cmin_args = [cmin, *[val for vals in opts for val in vals],
                     '-o', temp_dir, '--', *args]
        proc = run(cmin_args, check=False, env=env)

        seeds = list(Path(temp_dir).iterdir())

        print('\nSeeds (%d):' % len(seeds))
        for seed in seeds:
            print(seed.name)

        ret = proc.returncode

    sys.exit(ret)


if __name__ == '__main__':
    main()
