from os.path import exists, join
import shutil

from hecto import vcs


def test_get_repo():
    get = vcs.get_repo

    assert get("git@git.myproject.org:MyProject") == "git@git.myproject.org:MyProject"
    assert (
        get("git://git.myproject.org/MyProject") == "git://git.myproject.org/MyProject"
    )
    assert (
        get("https://github.com/jpscaletti/hecto.git")
        == "https://github.com/jpscaletti/hecto.git"
    )

    assert get("gh:/jpscaletti/hecto.git") == "https://github.com/jpscaletti/hecto.git"
    assert get("gh:jpscaletti/hecto.git") == "https://github.com/jpscaletti/hecto.git"

    assert get("gl:jpscaletti/hecto.git") == "https://gitlab.com/jpscaletti/hecto.git"

    assert (
        get("git+https://git.myproject.org/MyProject")
        == "https://git.myproject.org/MyProject"
    )
    assert (
        get("git+ssh://git.myproject.org/MyProject")
        == "ssh://git.myproject.org/MyProject"
    )

    assert get("git://git.myproject.org/MyProject.git@master")
    assert get("git://git.myproject.org/MyProject.git@v1.0")
    assert get("git://git.myproject.org/MyProject.git@da39a3ee5e6b4b0d3255bfef956018")

    assert get("http://google.com") is None
    assert get("git.myproject.org/MyProject") is None


def test_clone():
    tmp = vcs.clone("https://github.com/jpscaletti/siht.git")
    assert tmp
    assert exists(join(tmp, "setup.py"))
    shutil.rmtree(tmp)
