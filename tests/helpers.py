from hashlib import sha1
from pathlib import Path
import filecmp
import errno
import os

import hecto


PROJECT_TEMPLATE = Path(__file__).parent / "demo"

DATA = {
    "py3": True,
    "make_secret": lambda: sha1(os.urandom(48)).hexdigest(),
    "myvar": "awesome",
    "what": "world",
    "project_name": "Hecto",
    "version": "1.0.0",
    "description": "A library for rendering projects templates",
}


def render(dst, **kwargs):
    kwargs.setdefault("quiet", True)
    hecto.copy(PROJECT_TEMPLATE, dst, data=DATA, **kwargs)


def assert_file(dst, *path):
    p1 = os.path.join(str(dst), *path)
    p2 = os.path.join(str(PROJECT_TEMPLATE), *path)
    assert filecmp.cmp(p1, p2)


def make_folder(folder):
    if not folder.exists():
        try:
            os.makedirs(str(folder))
        except OSError as e:  # pragma: no cover
            if e.errno != errno.EEXIST:
                raise
