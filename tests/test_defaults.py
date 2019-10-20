from pathlib import Path
import re

import hecto


ROOT_PATH = Path(__file__).parent


def test_invalid_yaml(capsys):
    src = ROOT_PATH / "demo_invalid_defaults"
    assert {} == hecto.load_defaults(src)
    out, err = capsys.readouterr()
    assert re.search(r"INVALID.*demo_invalid_defaults/hecto\.yaml", out)


def test_invalid_quiet(capsys):
    src = ROOT_PATH / "demo_invalid_defaults"
    assert {} == hecto.load_defaults(src, quiet=True)
    out, err = capsys.readouterr()
    assert out == ""


def test_load_yml(capsys):
    src = ROOT_PATH / "demo_yml"
    assert {"foo": "bar"} == hecto.load_defaults(src)
    out, err = capsys.readouterr()
    assert out == ""


def test_no_defaults(capsys):
    src = ROOT_PATH / "references"
    assert {} == hecto.load_defaults(src)
    out, err = capsys.readouterr()
    assert out == ""
