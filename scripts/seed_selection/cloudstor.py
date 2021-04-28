"""
Cloudstor helper functions.

Author: Adrian Herrera
"""


from webdav3.client import Client


_URL = 'https://cloudstor.aarnet.edu.au/plus/public.php/webdav'
_LOGIN = '7i8vPklNDO5RL5g'


def connect():
    """Connect to cloudstor (over webdav)."""
    return Client(dict(webdav_hostname=_URL, webdav_login=_LOGIN))
