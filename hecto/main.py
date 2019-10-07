import datetime
import filecmp
import os
import re
import shutil
import subprocess
from pathlib import Path

import yaml

from . import vcs
from .tools import copy_file
from .tools import get_jinja_renderer
from .tools import get_name_filters
from .tools import make_folder
from .tools import printf
from .tools import printf_exception
from .tools import prompt_bool
from .tools import STYLE_DANGER
from .tools import STYLE_IGNORE
from .tools import STYLE_OK
from .tools import STYLE_WARNING


__all__ = ("copy", "copy_local", "load_defaults")

# Files of the template to exclude from the final project
DEFAULT_EXCLUDE = [
    "~*",
    "*.py[co]",
    "__pycache__",
    "__pycache__/*",
    ".git",
    ".git/*",
    ".DS_Store",
    ".svn",
    ".hg",
]

DEFAULT_INCLUDE = ()

DEFAULT_DATA = {"now": datetime.datetime.utcnow}


def copy(
    src_path,
    dst_path,
    data=None,
    *,
    exclude=None,
    include=None,
    skip_if_exists=None,
    envops=None,
    pretend=False,
    force=False,
    skip=False,
    quiet=False
):
    """
    Uses the template in src_path to generate a new project at dst_path.

    Arguments:

    - src_path (str):
        Absolute path to the project skeleton. May be a version control system URL

    - dst_path (str):
        Absolute path to where to render the skeleton

    - data (dict):
        Optional. Data to be passed to the templates in addtion to the user data from
        a `hecto.json`.

    - exclude (list):
        A list of names or shell-style patterns matching files or folders
        that must not be copied.

    - include (list):
        A list of names or shell-style patterns matching files or folders that
        must be included, even if its name is a match for the `exclude` list.
        Eg: `['.gitignore']`. The default is an empty list.

    - skip_if_exists (list):
        Skip any of these files if another with the same name already exists in the
        destination folder. (it only makes sense if you are copying to a folder that
        already exists).

    - envops (dict):
        Extra options for the Jinja template environment.

    - pretend (bool):
        Run but do not make any changes

    - force (bool):
        Overwrite files that already exist, without asking

    - skip (bool):
        Skip files that already exist, without asking

    - quiet (bool):
        Suppress the status output

    """
    repo = vcs.get_repo(src_path)
    if repo:
        src_path = vcs.clone(repo)

    _data = DEFAULT_DATA.copy()
    _data.update(data or {})

    try:
        copy_local(
            src_path,
            dst_path,
            data=_data,
            exclude=exclude,
            include=include,
            skip_if_exists=skip_if_exists,
            envops=envops,
            pretend=pretend,
            force=force,
            skip=skip,
            quiet=quiet,
        )
    finally:
        if repo:
            shutil.rmtree(src_path)


RE_TMPL = re.compile(r"\.tmpl$", re.IGNORECASE)


def resolve_source_path(src_path):
    try:
        src_path = Path(src_path).resolve()
    except FileNotFoundError:
        raise ValueError("Project template not found")

    if not src_path.exists():
        raise ValueError("Project template not found")

    if not src_path.is_dir():
        raise ValueError("The project template must be a folder")

    return src_path


def copy_local(
    src_path,
    dst_path,
    data,
    *,
    exclude=None,
    include=None,
    skip_if_exists=None,
    extra_paths=None,
    envops=None,
    **flags
):
    src_path = resolve_source_path(src_path)
    dst_path = Path(dst_path).resolve()

    defaults = load_defaults(src_path, **flags)

    default_exclude = defaults.pop("exclude", None)
    if exclude is None:
        exclude = default_exclude or DEFAULT_EXCLUDE
    exclude.append("hecto.yml")

    default_include = defaults.pop("include", None)
    if include is None:
        include = default_include or DEFAULT_INCLUDE

    default_skip_if_exists = defaults.pop("skip_if_exists", None)
    if skip_if_exists is None:
        skip_if_exists = default_skip_if_exists or []

    render = get_jinja_renderer(src_path, data, envops)
    skip_if_exists = [render.string(pattern) for pattern in skip_if_exists]
    must_filter, must_skip = get_name_filters(exclude, include, skip_if_exists)
    data.setdefault("folder_name", dst_path.name)

    if not flags["quiet"]:
        print("")  # padding space

    for folder, _, files in os.walk(str(src_path)):
        rel_folder = folder.replace(str(src_path), "", 1).lstrip(os.path.sep)
        rel_folder = render.string(rel_folder)
        rel_folder = rel_folder.replace("." + os.path.sep, ".", 1)

        if must_filter(rel_folder):
            continue

        folder = Path(folder)
        rel_folder = Path(rel_folder)

        render_folder(dst_path, rel_folder, flags)

        source_paths = get_source_paths(folder, rel_folder, files, render, must_filter)

        for source_path, rel_path in source_paths:
            render_file(dst_path, rel_path, source_path, render, must_skip, flags)


def load_defaults(src_path, **flags):
    defaults_path = Path(src_path) / "hecto.yml"
    if not defaults_path.exists():
        return {}
    try:
        return yaml.safe_load(defaults_path.read_text())
    except yaml.YAMLError:
        printf_exception(
            "INVALID CONFIG FILE",
            msg=str(defaults_path),
            quiet=flags.get("quiet")
        )
        return {}


def get_source_paths(folder, rel_folder, files, render, must_filter):
    source_paths = []
    for src_name in files:
        dst_name = re.sub(RE_TMPL, "", src_name)
        dst_name = render.string(dst_name)
        rel_path = rel_folder / dst_name

        if must_filter(rel_path):
            continue
        source_paths.append((folder / src_name, rel_path))
    return source_paths


def render_folder(dst_path, rel_folder, flags):
    final_path = dst_path / rel_folder
    display_path = str(rel_folder) + os.path.sep

    if str(rel_folder) == ".":
        make_folder(final_path, pretend=flags["pretend"])
        return

    if final_path.exists():
        printf("identical", display_path, style=STYLE_IGNORE, quiet=flags["quiet"])
        return

    make_folder(final_path, pretend=flags["pretend"])
    printf("create", display_path, style=STYLE_OK, quiet=flags["quiet"])


def render_file(dst_path, rel_path, source_path, render, must_skip, flags):
    """Process or copy a file of the skeleton.
    """
    if source_path.suffix == ".tmpl":
        content = render(source_path)
    else:
        content = None

    display_path = str(rel_path)
    final_path = dst_path / rel_path

    if final_path.exists():
        if file_is_identical(source_path, final_path, content):
            printf("identical", display_path, style=STYLE_IGNORE, quiet=flags["quiet"])
            return

        if must_skip(rel_path):
            printf("skip", display_path, style=STYLE_WARNING, quiet=flags["quiet"])
            return

        if overwrite_file(
            display_path, source_path, final_path, content, flags
        ):
            printf("force", display_path, style=STYLE_WARNING, quiet=flags["quiet"])
        else:
            printf("skip", display_path, style=STYLE_WARNING, quiet=flags["quiet"])
            return
    else:
        printf("create", display_path, style=STYLE_OK, quiet=flags["quiet"])

    if flags["pretend"]:
        return

    if content is None:
        copy_file(source_path, final_path)
    else:
        final_path.write_text(content)


def file_is_identical(source_path, final_path, content):
    if content is None:
        return files_are_identical(source_path, final_path)

    return file_has_this_content(final_path, content)


def files_are_identical(path1, path2):
    return filecmp.cmp(str(path1), str(path2), shallow=False)


def file_has_this_content(path, content):
    return content == path.read_text()


def overwrite_file(display_path, source_path, final_path, content, flags):
    printf("conflict", display_path, style=STYLE_DANGER, quiet=flags["quiet"])
    if flags["force"]:
        return True
    if flags["skip"]:  # pragma: no cover
        return False

    msg = f" Overwrite {final_path}?"  # pragma: no cover
    return prompt_bool(msg, default=True)  # pragma: no cover
