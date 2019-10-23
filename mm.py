#!/usr/bin/env python
"""
This file generates all the necessary files for packaging for the project.
Read more about it at https://github.com/jpscaletti/mastermold/
"""
data = {
    "title": "Hecto",
    "name": "hecto",
    "pypi_name": "hecto",
    "version": "1.191024",
    "author": "Juan-Pablo Scaletti",
    "author_email": "juanpablo@jpscaletti.com",
    "description": "(graph).",
    "copyright": "2011",
    "repo_name": "jpscaletti/hecto",
    "home_url": "",
    "project_urls": {},
    "development_status": "5 - Production/Stable",
    "minimal_python": 3.6,
    "install_requires": [
        "jinja2 ~= 2.10",
        "colorama ~= 0.4",
        "pyyaml ~= 5.1.2",
    ],
    "testing_requires": [
        "pytest",
        "pytest-cov",
    ],
    "development_requires": [
        "flake8",
        "ipdb",
        "tox",
    ],
    "coverage_omit": [],
}


def do_the_thing():
    import hecto

    hecto.copy(
        # "gh:jpscaletti/mastermold.git",
        "../mastermold",  # Path to the local copy of Master Mold
        ".",
        data=data,
        force=False,
        exclude=[
            ".*",
            ".*/*",
            "README.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
        ],
    )


if __name__ == "__main__":
    do_the_thing()
