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
from .tools import get_name_filter
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
DEFAULT_EXCLUDE = (
    "hecto.yml",
    "~*",
    "*.py[co]",
    "__pycache__",
    "__pycache__/*",
    ".git",
    ".git/*",
    ".DS_Store",
    ".svn",
)

DEFAULT_INCLUDE = ()

DEFAULT_DATA = {"now": datetime.datetime.utcnow}


def copy(
    src_path,
    dst_path,
    data=None,
    *,
    exclude=None,
    include=None,
    tasks=None,
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
        must be included, even if its name are in the `exclude` list.
        Eg: `['.gitignore']`. The default is an empty list.

    - tasks (list):
        Optional lists of commands to run in order after finishing the copy.
        Like in the templates files, you can use variables on the commands that will
        be replaced by the real values before running the command.
        If one of the commands fail, the rest of them will not run.

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
            tasks=tasks,
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


def resolve_paths(src_path, dst_path):
    try:
        src_path = Path(src_path).resolve()
    except FileNotFoundError:
        raise ValueError("Project template not found")

    if not src_path.exists():
        raise ValueError("Project template not found")

    if not src_path.is_dir():
        raise ValueError("The project template must be a folder")

    return src_path, Path(dst_path).resolve()


def copy_local(
    src_path,
    dst_path,
    data,
    *,
    exclude=None,
    include=None,
    tasks=None,
    extra_paths=None,
    envops=None,
    **flags
):
    src_path, dst_path = resolve_paths(src_path, dst_path)

    defaults = load_defaults(src_path, **flags)

    default_exclude = defaults.pop("exclude", None)
    if exclude is None:
        exclude = default_exclude or DEFAULT_EXCLUDE

    default_include = defaults.pop("include", None)
    if include is None:
        include = default_include or DEFAULT_INCLUDE

    default_tasks = defaults.pop("tasks", None)
    if tasks is None:
        tasks = default_tasks or []

    must_filter = get_name_filter(exclude, include)
    data.setdefault("folder_name", dst_path.name)
    render = get_jinja_renderer(src_path, data, envops)

    if not flags["quiet"]:
        print("")  # padding space

    for folder, _, files in os.walk(str(src_path)):
        rel_folder = folder.replace(str(src_path), "", 1).lstrip(os.path.sep)
        rel_folder = render.string(rel_folder)

        if must_filter(rel_folder):
            continue

        folder = Path(folder)
        rel_folder = Path(rel_folder)

        for src_name in files:
            dst_name = re.sub(RE_TMPL, "", src_name)
            dst_name = render.string(dst_name)
            rel_path = rel_folder / dst_name

            if must_filter(rel_path):
                continue

            source_path = folder / src_name
            render_file(dst_path, rel_path, source_path, render, **flags)

    if not flags["quiet"]:
        print("")  # padding space

    if tasks:
        run_tasks(dst_path, render, tasks)


def load_defaults(src_path, **flags):
    defaults_path = Path(src_path) / "hecto.yml"
    if not defaults_path.exists():
        return {}
    try:
        return yaml.safe_load(defaults_path.read_text())
    except yaml.YAMLError:
        if not flags.get("quiet"):
            printf_exception("INVALID CONFIG FILE", msg=str(defaults_path))
        return {}


def render_file(dst_path, rel_path, source_path, render, **flags):
    """Process or copy a file of the skeleton.
    """
    final_path = dst_path.resolve() / rel_path
    if not flags["pretend"]:
        make_folder(final_path.parent)

    if source_path.suffix == ".tmpl":
        content = render(source_path)
    else:
        content = None

    display_path = str(rel_path).replace("." + os.path.sep, ".", 1)

    if not final_path.exists():
        if not flags["quiet"]:
            printf("create", display_path, style=STYLE_OK)
    else:
        if file_is_identical(source_path, final_path, content):
            if not flags["quiet"]:
                printf("identical", display_path, style=STYLE_IGNORE)
            return

        if not overwrite_file(display_path, source_path, final_path, content, **flags):
            return

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


def overwrite_file(display_path, source_path, final_path, content, **flags):
    if not flags["quiet"]:
        printf("conflict", display_path, style=STYLE_DANGER)
    if flags["force"]:
        overwrite = True
    elif flags["skip"]:
        overwrite = False
    else:  # pragma: no cover
        msg = " Overwrite {}?".format(final_path)
        overwrite = prompt_bool(msg, default=True)

    if not flags["quiet"]:
        printf("force" if overwrite else "skip", display_path, style=STYLE_WARNING)

    return overwrite


def run_tasks(dst_path, render, tasks):
    dst_path = str(dst_path)
    for task in tasks:
        task = render.string(task)
        subprocess.run(task, shell=True, check=True, cwd=dst_path)
