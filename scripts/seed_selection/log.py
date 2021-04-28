"""
Logging utilities.

Author: Adrian Herrera
"""


import logging


FORMATTER = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')


def get_logger(name: str):
    """Get a formatted logger."""
    handler = logging.StreamHandler()
    handler.setFormatter(FORMATTER)

    logger = logging.getLogger(name)
    logger.addHandler(handler)

    return logger
