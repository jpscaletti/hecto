from pathlib import Path

import hecto
import pytest

from .helpers import assert_file
from .helpers import DATA
from .helpers import filecmp
from .helpers import make_folder
from .helpers import PROJECT_TEMPLATE
from .helpers import render


def test_project_not_found(dst):
    with pytest.raises(ValueError):
        hecto.copy("foobar", dst)

    with pytest.raises(ValueError):
        hecto.copy(__file__, dst)


def test_copy(dst):
    render(dst)
    generated = (dst / "pyproject.toml").read_text()
    control = (Path(__file__).parent / "references" / "pyproject.toml").read_text()
    assert generated == control

    assert_file(dst, "doc", "mañana.txt")
    assert_file(dst, "doc", "images", "nslogo.gif")

    p1 = str(dst / "awesome" / "hello.txt")
    p2 = str(PROJECT_TEMPLATE / "[[ myvar ]]" / "hello.txt")
    assert filecmp.cmp(p1, p2)

    p1 = str(dst / "awesome.txt")
    p2 = str(PROJECT_TEMPLATE / "[[ myvar ]].txt")
    assert filecmp.cmp(p1, p2)


def test_copy_repo(dst):
    hecto.copy("gh:jpscaletti/siht.git", dst, quiet=True)
    assert (dst / "setup.py").exists()


def test_default_exclude(dst):
    render(dst)
    assert not (dst / ".svn").exists()


def test_include_file(dst):
    render(dst, include=[".svn"])
    assert_file(dst, ".svn")


def test_include_pattern(dst):
    render(dst, include=[".*"])
    assert (dst / ".svn").exists()


def test_exclude_file(dst):
    render(dst, exclude=["mañana.txt"])
    assert not (dst / "doc" / "mañana.txt").exists()


def test_exclude_folder(dst):
    render(dst, exclude=["doc", "doc/*"])
    assert not (dst / "doc").exists()


def test_skip_if_exists(dst):
    (dst / "aaaa.txt").write_text("SKIPPED aaaa.txt")
    (dst / "config.py").write_text("SKIPPED config.py")
    make_folder(dst / "awesome")
    (dst / "awesome" / "hello.txt").write_text("SKIPPED hello.txt")
    (dst / ".gitignore").write_text("SKIPPED")

    hecto.copy(
        PROJECT_TEMPLATE,
        dst,
        data=DATA,
        quiet=True,
        force=True,
        skip_if_exists=["aa*.txt", "config.py", "[[ myvar ]]/hello.txt"]
    )

    assert (dst / "aaaa.txt").read_text() == "SKIPPED aaaa.txt"
    assert (dst / "config.py").read_text() == "SKIPPED config.py"
    assert (dst / "awesome" / "hello.txt").read_text() == "SKIPPED hello.txt"
    assert (dst / ".gitignore").read_text() != "SKIPPED .gitignore"


def test_config_skip_if_exists(dst):
    (dst / "aaaa.txt").write_text("SKIPPED aaaa.txt")
    (dst / "config.py").write_text("SKIPPED config.py")
    make_folder(dst / "awesome")
    (dst / "awesome" / "hello.txt").write_text("SKIPPED hello.txt")
    (dst / ".gitignore").write_text("SKIPPED .gitignore")

    def load_fake_data(*_args, **_kw):
        return {
            "skip_if_exists": ["aa*.txt", "config.py", "[[ myvar ]]/hello.txt"]
        }

    _get_defaults = hecto.main.load_defaults
    hecto.main.load_defaults = load_fake_data

    hecto.copy(
        PROJECT_TEMPLATE,
        dst,
        data=DATA,
        quiet=True,
        force=True,
    )

    assert (dst / "aaaa.txt").read_text() == "SKIPPED aaaa.txt"
    assert (dst / "config.py").read_text() == "SKIPPED config.py"
    assert (dst / "awesome" / "hello.txt").read_text() == "SKIPPED hello.txt"
    assert (dst / ".gitignore").read_text() != "SKIPPED .gitignore"
    hecto.main.load_defaults = _get_defaults


def test_config_exclude(dst):
    def load_fake_data(*_args, **_kw):
        return {"exclude": ["*.txt"]}

    _get_defaults = hecto.main.load_defaults
    hecto.main.load_defaults = load_fake_data
    hecto.copy(PROJECT_TEMPLATE, dst, data=DATA, quiet=True)
    assert not (dst / "aaaa.txt").exists()
    hecto.main.load_defaults = _get_defaults


def test_config_exclude_overridden(dst):
    def load_fake_data(*_args, **_kw):
        return {"exclude": ["*.txt"]}

    _get_defaults = hecto.main.load_defaults
    hecto.main.load_defaults = load_fake_data
    hecto.copy(PROJECT_TEMPLATE, dst, data=DATA, quiet=True, exclude=[])
    assert (dst / "aaaa.txt").exists()
    hecto.main.load_defaults = _get_defaults


def test_config_include(dst):
    def load_fake_data(*_args, **_kw):
        return {"include": [".svn"]}

    _get_defaults = hecto.main.load_defaults
    hecto.main.load_defaults = load_fake_data
    hecto.copy(PROJECT_TEMPLATE, dst, data=DATA, quiet=True)
    assert (dst / ".svn").exists()
    hecto.main.load_defaults = _get_defaults


def test_skip_option(dst):
    render(dst)
    path = dst / "pyproject.toml"
    content = "lorem ipsum"
    path.write_text(content)
    render(dst, skip=True)
    assert path.read_text() == content


def test_force_option(dst):
    render(dst)
    path = dst / "pyproject.toml"
    content = "lorem ipsum"
    path.write_text(content)
    render(dst, force=True)
    assert path.read_text() != content


def test_pretend_option(dst):
    render(dst, pretend=True)
    assert not (dst / "doc").exists()
    assert not (dst / "config.py").exists()
    assert not (dst / "pyproject.toml").exists()
