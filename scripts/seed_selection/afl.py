"""
AFL helper functions.

Author: Adrian Herrera
"""

from pathlib import Path
from typing import List, Tuple


def replace_atat(args: List[str], seed: Path) -> Tuple[List[str], bool]:
    """Replace the seed placeholder `@@`."""
    new_args = []
    found_atat = False

    for arg in args:
        if arg == '@@':
            new_args.append(str(seed))
            found_atat = True
        else:
            new_args.append(arg)

    return new_args, found_atat
