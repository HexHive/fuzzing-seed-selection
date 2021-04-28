"""
argparse type-checking functions.

Author: Adrian Herrera
"""


from argparse import ArgumentTypeError
from pathlib import Path
import logging
import re


MEM_LIMIT_RE = re.compile(r'''(\d+)([TGkM]?)''')


def log_level(val: str) -> int:
    """Ensure that an argument value is a valid log level."""
    numeric_level = getattr(logging, val.upper(), None)
    if not isinstance(numeric_level, int):
        raise ArgumentTypeError('%r is not a valid log level' % val)
    return numeric_level


def mem_limit(val: str) -> int:
    """Parse the memory limit (based on AFL's format)."""
    mem_limit = 0
    if val:
        match = MEM_LIMIT_RE.match(val)
        if not match:
            raise ArgumentTypeError('%r is not a valid memory limit' % val)
        mem_limit = match.group(1)
        suffix = match.group(2)
        if suffix == 'T':
            mem_limit *= 1024 * 1024
        elif suffix == 'G':
            mem_limit *= 1024
        elif suffix == 'k':
            mem_limit /= 1024
    return mem_limit


def path_exists(val: str) -> Path:
    """Ensure that the path argument exists."""
    try:
        p = Path(val)
    except Exception as e:
        raise ArgumentTypeError('%r is not a valid path' % val) from e
    if not p.exists():
        raise ArgumentTypeError('%s does not exist' % p)
    return p.resolve()


def positive_int(val: str) -> int:
    """Ensure that an argument value is a positive integer."""
    try:
        ival = int(val)
        if ival <= 0:
            raise Exception
    except Exception as e:
        raise ArgumentTypeError('%r is not a positive integer' % val) from e
    return ival
