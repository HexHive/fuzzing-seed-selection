"""
Extract coverage from HDF5 files.

Author: Adrian Herrera
"""


from functools import partial
from itertools import repeat
from pathlib import Path
from typing import Optional, Set
import multiprocessing.pool as mpp

from h5py import File
from tqdm import tqdm

# pylint: disable=unused-import
from . import istarmap


def _get_seed_cov(h5_path: Path, seed: str, out_dir: Path,
                  seeds: Optional[Set[str]] = None) -> str:
    """Extract the given seed from the HDF5 file specified at `h5_path`."""
    if seeds and seed not in seeds:
        return None

    with File(h5_path, 'r') as h5f, open(out_dir / seed, 'w') as outf:
        for edge, count in h5f[seed]:
            outf.write('%d:%d\n' % (edge, count))

    return seed


def expand_hdf5(h5f: File, out_dir: Path, seeds: Optional[Set[str]] = None,
                jobs: int = 1, progress: bool = False):
    """
    Expand an HDF5 containing code coverage.

    Args:
        h5f: h5py file object.
        out_dir: Directory to extract seed coverage to.
        seeds: An optional seed set. If provided, only these seeds will be
               extracted.
        jobs: Number of parallel jobs to run.
        progress: Set to `True` for progress bar.

    Returns:
        Yields each extracted seed.
    """
    h5_filename = h5f.filename

    with mpp.Pool(processes=jobs) as pool:
        get_cov = partial(_get_seed_cov, out_dir=out_dir, seeds=seeds)
        h5_iter = zip(repeat(h5_filename), h5f.keys())
        num_seeds = len(seeds) if seeds else len(list(h5f.keys()))
        print('%d seeds to extract' % num_seeds)
        iter_func = partial(tqdm, desc='Expanding %s' % h5_filename,
                            total=num_seeds, unit='seeds') if progress else id
        for seed in iter_func(pool.istarmap(get_cov, h5_iter)):
            if seed:
                yield seed
