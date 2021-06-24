"""
Data store helper functions.

Author: Adrian Herrera
"""


from pathlib import Path

from tqdm import tqdm
import requests


CHUNK_SIZE = 1024
_URL = 'https://datacommons.anu.edu.au/DataCommons/rest/records/anudc:6106/data/'


def get_file(path: Path, progbar: bool = False) -> bytes:
    """Download a file from the data store."""
    content = bytearray()

    with requests.get(f'{_URL}/{path}', stream=True) as r:
        if r.status_code != 200:
            raise Exception('Failed to download %s from datastore' % path)

        total_kb = int(r.headers.get('content-length', 0)) // CHUNK_SIZE
        for data in tqdm(r.iter_content(CHUNK_SIZE), total=total_kb, unit='kB',
                         disable=not progbar):
            content.extend(data)

    return bytes(content)
