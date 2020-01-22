from hashlib import sha1
from pathlib import Path
from tempfile import mkdtemp
from unittest import mock
import errno
import filecmp
import os
import shutil

import hecto
import pytest
import six


@pytest.fixture(scope="session")
def PROJECT_TEMPLATE():
    return Path(__file__).parent / "demo"


@pytest.fixture(scope="session")
def DATA():
    return {
        "py3": True,
        "make_secret": lambda: sha1(os.urandom(48)).hexdigest(),
        "myvar": "awesome",
        "what": "world",
        "project_name": "Hecto",
        "version": "1.0.0",
        "description": "A library for rendering projects templates",
    }


@pytest.fixture(scope="session")
def render(PROJECT_TEMPLATE, DATA):
    def render(dst, **kwargs):
        kwargs.setdefault("quiet", True)
        hecto.copy(PROJECT_TEMPLATE, dst, data=DATA, **kwargs)
    return render


@pytest.fixture(scope="session")
def assert_file(PROJECT_TEMPLATE):
    def assert_file(dst, *path):
        p1 = os.path.join(str(dst), *path)
        p2 = os.path.join(str(PROJECT_TEMPLATE), *path)
        assert filecmp.cmp(p1, p2)
    return assert_file


@pytest.fixture(scope="session")
def make_folder():
    def make_folder(folder):
        if not folder.exists():
            try:
                os.makedirs(str(folder))
            except OSError as e:  # pragma: no cover
                if e.errno != errno.EEXIST:
                    raise
    return make_folder


@pytest.fixture()
def dst(request):
    """Return a real temporary folder path which is unique to each test
    function invocation. This folder is deleted after the test has finished.
    """
    dst = mkdtemp()
    dst = Path(dst).resolve()
    request.addfinalizer(lambda: shutil.rmtree(str(dst), ignore_errors=True))
    return dst


class AppendableStringIO(six.StringIO):
    def append(self, text):
        pos = self.tell()
        self.seek(0, os.SEEK_END)
        self.write(text)
        self.seek(pos)


@pytest.fixture()
def stdin():
    buffer = AppendableStringIO()
    with mock.patch("sys.stdin", buffer):
        yield buffer
