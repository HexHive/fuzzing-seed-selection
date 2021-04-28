#!/usr/bin/env python3

"""
Extract the shared library dependencies for a given binary.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from pathlib import Path
from shutil import copyfile
from typing import Set
import re
import subprocess

from elftools.elf.elffile import ELFFile
from elftools.elf.segments import InterpSegment

LDD_RE = re.compile(r'.*.so.* => (/.*\.so[^ ]*)')
LDD_NOT_FOUND_RE = re.compile(r'(.*.so.*) => not found')


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Extract a binary\'s library '
                                        'dependencies')
    parser.add_argument('-o', '--output', metavar='DIR', type=Path,
                        required=True, help='Output directory')
    parser.add_argument('binary', metavar='FILE', nargs='+', type=Path,
                        help='Path to binary')
    return parser.parse_args()


def get_interpreter(prog: Path) -> Path:
    """Extract the binary's interpreter."""
    with open(prog, 'rb') as inf:
        elf = ELFFile(inf)
        for seg in elf.iter_segments():
            if isinstance(seg, InterpSegment):
                return Path(seg.get_interp_name())

    raise Exception('Could not find binary interpreter in %s' % prog)


def get_library_deps(prog: Path) -> Set[Path]:
    """Use `ldd` to determine the given program's library dependencies."""
    deps = set()

    ldd = subprocess.run(['ldd', str(prog)], check=True, encoding='utf-8',
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in ldd.stdout.split('\n'):
        match = LDD_NOT_FOUND_RE.search(line)
        if match:
            missing_lib = match.group(1).strip()
            raise Exception('Could not find %s - check LD_LIBRARY_PATH' %
                            missing_lib)
        match = LDD_RE.search(line)
        if not match:
            continue
        deps.add(Path(match.group(1)))

    return deps


def main():
    """The main function."""
    args = parse_args()

    progs = args.binary
    out_dir = args.output

    libs = set()

    for prog in progs:
        if not prog.exists():
            print('WARN: %s does not exist. Skipping...' % prog)
            continue

        # Get loader
        libs.add(get_interpreter(prog))

        # Determine all library dependencies
        libs.update(get_library_deps(prog))

    if not out_dir.exists():
        out_dir.mkdir(exist_ok=True)

    for lib in libs:
        # Skip if they are the same file
        if lib.parent.samefile(out_dir):
            print('WARN: %s already exists in %s. Skipping...' % (lib.name, out_dir))
            continue
        copyfile(lib, out_dir / lib.name)


if __name__ == '__main__':
    main()
