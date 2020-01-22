import re


def test_output(capsys, dst, render):
    render(dst, quiet=False)
    out, err = capsys.readouterr()
    print(out)
    assert re.search(r"created[^\s]*  config\.py", out)
    assert re.search(r"created[^\s]*  pyproject\.toml", out)
    assert re.search(r"created[^\s]*  doc/images/nslogo\.gif", out)


def test_output_pretend(capsys, dst, render):
    render(dst, quiet=False, pretend=True)
    out, err = capsys.readouterr()

    assert re.search(r"created[^\s]*  config\.py", out)
    assert re.search(r"created[^\s]*  pyproject\.toml", out)
    assert re.search(r"created[^\s]*  doc/images/nslogo\.gif", out)


def test_output_force(capsys, dst, render):
    render(dst)
    out, err = capsys.readouterr()
    render(dst, quiet=False, force=True)
    out, err = capsys.readouterr()
    print(out)

    assert re.search(r"updated[^\s]*  config\.py", out)
    assert re.search(r"identical[^\s]*  pyproject\.toml", out)
    assert re.search(r"identical[^\s]*  doc/images/nslogo\.gif", out)


def test_output_skip(capsys, dst, render):
    render(dst)
    out, err = capsys.readouterr()
    render(dst, quiet=False, skip=True)
    out, err = capsys.readouterr()
    print(out)

    assert re.search(r"skipped[^\s]*  config\.py", out)
    assert re.search(r"identical[^\s]*  pyproject\.toml", out)
    assert re.search(r"identical[^\s]*  doc/images/nslogo\.gif", out)


def test_output_quiet(capsys, dst, render):
    render(dst, quiet=True)
    out, err = capsys.readouterr()
    assert out == ""
