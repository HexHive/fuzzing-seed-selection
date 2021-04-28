"""
OSF helper functions.

Author: Adrian Herrera
"""


from pathlib import Path

from osfclient import OSF
from osfclient.models import File, Folder, Storage


_PROJECT = 'hz8em'


def connect() -> Storage:
    """Connect to the seed selection OSF project."""
    return OSF().project(_PROJECT).storage()


def get_folder(store: Storage, path: Path) -> Folder:
    """Open a connection to a folder in the given OSF store."""
    folder = store
    for part in path.parts:
        for f in folder.folders:
            if f.name == part:
                folder = f
    if folder.name != path.name:
        raise Exception('Unable to find folder %s in %s' % (path, store))

    return folder


def get_file(store: Storage, path: Path) -> File:
    """Open a connection to a file in the given OSF store."""
    # Find the folder storing the file
    folder = get_folder(store, path.parent)

    # Now find the file in the folder
    for f in folder.files:
        if f.name == path.name:
            return f

    raise Exception('Unable to find %s in OSF storage %s' % (path, store))
