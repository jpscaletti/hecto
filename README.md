> **NOTE**: I'm thankful for any bug fix or report; They are more than welcome.<br>
> However, I want to keep the scope of this project very small, so any other kind of pull-requests are discouraged.

# ![Hecto(graph)](https://github.com/jpscaletti/hecto/raw/master/hecto.png)

[![Coverage Status](https://coveralls.io/repos/github/jpscaletti/hecto/badge.svg?branch=master)](https://coveralls.io/github/jpscaletti/hecto?branch=master) [![Tests](https://travis-ci.org/jpscaletti/hecto.svg?branch=master)](https://travis-ci.org/jpscaletti/hecto/)

A small and simple **library** for rendering projects templates.

* Works with **local** paths and **git URLs**.
* Your project can include any file and **Hecto** can dynamically replace values in any kind of text files.
* It generates a beautiful output and take care of not overwrite existing files, unless instructed to do so.


## How to use

```bash
pip install hecto
```

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

The content of the files inside the project template are copied to the destination without changes, **unless are suffixed with the extension '.tmpl'.** (you can customize that with the `render_as` setting). In that case, the templating engine is used to render them.

A slightly customized Jinja2 templates are used. The main difference is
that variables are referenced with ``[[ name ]]`` instead of
``{{ name }}`` and blocks are ``[% if name %]`` instead of
``{% if name %}``. To read more about templating see the [Jinja2
documentation](http://jinja.pocoo.org/docs>).

Use the `data` argument to pass whatever extra context you want to be available
in the templates. The arguments can be any valid Python value, even a
function.


## API

#### hecto.copy()

```python
hecto.copy(
    src_path,
    dst_path,

    data=DEFAULT_DATA,
    *,
    exclude=DEFAULT_EXCLUDE,
    include=[],
    skip_if_exists=[],
    envops={},
    render_as=DEFAULT_RENDER_AS,

    pretend=False,
    force=False,
    skip=False,
    quiet=False,
)
```

Uses the template in `src_path` to generate a new project at `dst_path`.

**Arguments**:

- **src_path** (str):<br>
    Absolute path to the project skeleton. May be a version control system URL.

- **dst_path** (str):<br>
    Absolute path to where to render the project template.

- **data** (dict):<br>
    Optional. Data to be passed to the templates.

- **exclude** (list of str):<br>
    Optional. A list of names or shell-style patterns matching files or folders
    that must not be copied.

- **include** (list of str):<br>
    Optional. A list of names or shell-style patterns matching files or folders that must be included, even if its name is a match for the `exclude` list. Eg: `['.gitignore']`.
    The default is an empty list.

- **skip_if_exists** (list of str):<br>
    Optional. Skip any of these file names or shell-style patterns, without asking, if another with the same name already exists in the destination folder.
    It only makes sense if you are copying to a folder that already exists.

- **envops** (dict):<br>
    Optional. Extra options for the Jinja template environment.

- **render_as** (function):<br>
    An optional hook that takes the absolute source path and the relative destination path of a file as arguments.

    It should return `None` if the file must be copied as-is or a Path object of the new relative destination (can be the same as the one received).

    By default all the files with the `.tmpl` postfix are rendered and saved without that postfix. Eg: `readme.md.tmpl` becomes `readme.md`.

- **get_context** (function):<br>
    An optional hook called before rendering a file. Takes the relative
    destination path of the file as argument, and should return a dictionary
    with the context for its rendering.

- **pretend** (bool):<br>
    Optional. Run but do not make any changes

- **force** (bool):<br>
    Optional. Overwrite files that already exist, without asking

- **skip** (bool):<br>
    Optional. Skip files that already exist, without asking

- **quiet** (bool):<br>
    Optional. Suppress the status output


## The hecto.yaml file

If a YAML file named `hecto.yaml` is found in the root of the project, it will be read and used for arguments defaults.

Note that they become just _the defaults_, so any explicitly-passed argument will overwrite them.

```yaml
# Shell-style patterns files/folders that must not be copied.
exclude:
  - "*.bar"
  - ".git"
  - ".git/*"

# Shell-style patterns files/folders that *must be* copied, even if
# they are in the exclude list
include:
  - "foo.bar"

# Shell-style patterns files to skip, without asking, if they already exists
# in the destination folder
skip_if_exists:
  - ".gitignore"

```
