
# Hecto

[![Coverage Status](https://coveralls.io/repos/github/jpscaletti/hecto/badge.svg?branch=master)](https://coveralls.io/github/jpscaletti/hecto?branch=master) [![Tests](https://travis-ci.org/jpscaletti/hecto.svg?branch=master)](https://travis-ci.org/jpscaletti/hecto/) [![](https://img.shields.io/pypi/pyversions/hecto.svg)](https://pypi.python.org/pypi/hecto)

A library for rendering projects templates.

* Works with **local** paths and **git URLs**.
* Your project can include any file and **Hecto** can dynamically replace values in any kind of text files.
* It generates a beautiful output and take care of not overwrite existing files, unless instructed to do so.

![Sample output](https://github.com/jpscaletti/hecto/raw/master/output.png)


## How to use

```python
from hecto import copy

# Create a project from a local path
copy('path/to/project/template', 'path/to/destination')

# Or from a git URL.
# You can also use "gh:" as a shortcut of "https://github.com/"
# Or "gl:"  as a shortcut of "https://gitlab.com/"
copy('https://github.com/jpscaletti/hecto.git', 'path/to/destination')
copy('gh:jpscaletti/hecto.git', 'path/to/destination')
copy('gl:jpscaletti/hecto.git', 'path/to/destination')

```


## How it works

The content of the files inside the project template are copied to the destination
without changes, **unless are suffixed with the extension '.tmpl'.**
In that case, the templating engine will be used to render them.

A slightly customized Jinja2 templating is used. The main difference is
that variables are referenced with ``[[ name ]]`` instead of
``{{ name }}`` and blocks are ``[% if name %]`` instead of
``{% if name %}``. To read more about templating see the [Jinja2
documentation](http://jinja.pocoo.org/docs>).

Use the `data` argument to pass whatever extra context you want to be available
in the templates. The arguments can be any valid Python value, even a
function.


## The hecto.yml file

If a `hecto.yml` file is found in the root of the project, it will be read and used for arguments defaults.

Note that they become just _the defaults_, so any explicitly-passed argument will overwrite them.

```yaml
---
# Shell-style patterns files/folders that must not be copied.
exclude:
  - "*.bar"
  - ".git"
  - ".git/*"

# Shell-style patterns files/folders that *must be* copied, even if
# they are in the exclude list
include:
  - "foo.bar"

# Commands to be executed after the copy
tasks:
  - "git init"
  - "rm [[ name_of_the_project ]]/README.md"

```

**Warning:** Use only trusted project templates as these tasks run with the
same level of access as your user.


## API

#### hecto.copy()

`hecto.copy(src_path, dst_path, data=None, *,
    exclude=DEFAULT_FILTER, include=DEFAULT_INCLUDE, envops=None,
    pretend=False, force=False, skip=False, quiet=False,
)`

Uses the template in src_path to generate a new project at dst_path.

**Arguments**:

- **src_path** (str):
    Absolute path to the project skeleton. May be a version control system URL

- **dst_path** (str):
    Absolute path to where to render the skeleton

- **data** (dict):
    Optional. Data to be passed to the templates in addtion to the user data from a `hecto.yml`.

- **exclude** (list of str):
    Optional. A list of names or shell-style patterns matching files or folders
    that mus not be copied.

- **include** (list of str):
    Optional. A list of names or shell-style patterns matching files or folders that must be included, even if its name are in the `exclude` list.
    Eg: `['.gitignore']`. The default is an empty list.

- **tasks** (list of str):
    Optional lists of commands to run in order after finishing the copy.
    Like in the templates files, you can use variables on the commands that will be replaced by the real values before running the command.
    If one of the commands fail, the rest of them will not run.

- **envops** (dict):
    Optional. Extra options for the Jinja template environment.

- **pretend** (bool):
    Optional. Run but do not make any changes

- **force** (bool):
    Optional. Overwrite files that already exist, without asking

- **skip** (bool):
    Optional. Skip files that already exist, without asking

- **quiet** (bool):
    Optional. Suppress the status output
