#!/usr/bin/env python3

"""
Wrapper around `qminset`. Only keeps the named of the files in the minimized
corpus.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from io import BytesIO
from pathlib import Path
from shutil import copytree, which
from subprocess import PIPE, run
from tarfile import TarInfo
from tempfile import TemporaryDirectory
import re
import tarfile

from seed_selection.argparse import path_exists


SEED_RE = re.compile(r'Adding \d+ instructions \((?P<seed>.+?)\)')


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Wrapper around minset')
    parser.add_argument('-i', '--input', metavar='DIR', type=path_exists,
                        required=True, help='Path to input directory of '
                                            '`afl-showmap` coverage files')
    parser.add_argument('-s', '--bitvectors', metavar='DIR', type=Path,
                        help='Save the `moonbeam-afl` bitvector traces in the '
                             'given directory')
    return parser.parse_args()


def main():
    """The main function."""
    args = parse_args()
    in_dir = args.input

    moonbeam = which('moonbeam-afl')
    if not moonbeam:
        raise Exception('`moonbeam-afl` not found. Check PATH')
    qminset = which('qminset')
    if not qminset:
        raise Exception('`qminset` not found. Check PATH')

    with TemporaryDirectory() as bv_dir, TemporaryDirectory() as mset_dir:
        # Generate bitvectors
        proc = run([moonbeam, '-i', in_dir, '-o', bv_dir], check=True)
        if proc.returncode != 0:
            raise Exception('moonbeam failed to generate bitvectors')
        print('')

        output_path = Path('output')
        bitvectors = list(Path(bv_dir).glob('*.bv'))
        num_bitvectors = len(bitvectors)

        # Save the bitvectors if requested
        if args.bitvectors:
            copytree(bv_dir, args.bitvectors)

        # Prepare the minset data
        print('Preparing minset data...')
        for bitvector in bitvectors:
            bitvector_size = bitvector.stat().st_size
            mset_bv_dir = Path(mset_dir) / bitvector.stem
            mset_bv_dir.mkdir()

            # Write size
            with open(mset_bv_dir / 'size', 'w') as outf:
                outf.write('%d\n' % bitvector_size)

            # Write output.tgz
            with tarfile.open(mset_bv_dir / 'output.tgz', 'w:gz') as tar:
                # Write imagefilemap.txt
                imagefilemap = BytesIO(b'%s,%s\n' % (in_dir.name.encode(),
                                                     bitvector.name.encode()))
                tarinfo = TarInfo(name=str(output_path / 'imagefilemap.txt'))
                tarinfo.size = len(imagefilemap.getvalue())
                tar.addfile(tarinfo=tarinfo, fileobj=imagefilemap)

                # Write info.txt
                info = BytesIO(b'0_0_0_0_0_0_0\n0_0_0_0_0_0_WEIGHT}_0\n')
                tarinfo = TarInfo(name=str(output_path / 'info.txt'))
                tarinfo.size = len(info.getvalue())
                tar.addfile(tarinfo=tarinfo, fileobj=info)

                # Write the bitvector
                with open(bitvector, 'rb') as inf:
                    tarinfo = TarInfo(name=str(output_path / bitvector.name))
                    tarinfo.size = bitvector_size
                    tar.addfile(tarinfo=tarinfo, fileobj=inf)

        # Run qminset
        print('Running minset...')
        proc = run([qminset, 'q', '%d' % num_bitvectors, str(mset_dir)],
                   stdout=PIPE, stderr=PIPE, check=True, encoding='utf8')

        # Get the seeds
        seeds = []
        for line in proc.stdout.split('\n'):
            line = line.strip()
            if line == 'DONE':
                break

            match = SEED_RE.match(line)
            if match:
                seeds.append(match.group('seed'))

        print('\nSeeds (%d):' % len(seeds))
        for seed in seeds:
            print(seed)


if __name__ == '__main__':
    main()
