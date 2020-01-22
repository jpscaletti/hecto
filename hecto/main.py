import datetime
import filecmp
import os
import re
import shutil
from pathlib import Path

import yaml

from . import vcs
from .utils import copy_file
from .utils import JinjaRender
from .utils import load_config
from .utils import make_filter
from .utils import make_folder
from .utils import make_matcher
from .utils import printf, printf_exception, Style
from .utils import prompt_bool


__all__ = ("copy", "copy_local")


def copy(
    src_path,
    dst_path,
    data=None,
    *,
    exclude=None,
    include=None,
    skip_if_exists=None,
    envops=None,
    render_as=None,
    get_context=None,
    pretend=False,
    force=False,
    skip=False,
    quiet=False,
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

    - render_as (function):
        An optional hook that takes the absolute source path and the relative
        destination path of a file as arguments.

        It should return `None` if the file must be copied as-is or a Path object
        of the new relative destination (can be the same as the one received).

        By default, all the files with the `.tmpl` or `.append` postfix are
        will be saved to a file without that postfix.
        Eg: `readme.md.tmpl` becomes `readme.md`.

    - get_context (function):
        An optional hook called before rendering a file. Takes the relative
        destination path of the file as argument, and should return a dictionary
        with the context for its rendering.

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

    try:
        copy_local(
            src_path,
            dst_path,
            data=data,
            exclude=exclude,
            include=include,
            skip_if_exists=skip_if_exists,
            envops=envops,
            render_as=render_as,
            get_context=get_context,
            pretend=pretend,
            force=force,
            skip=skip,
            quiet=quiet,
        )
    finally:
        if repo:
            shutil.rmtree(src_path)


GLOBAL_DEFAULTS = {
    "exclude": ["~*", "~*/*", ".*", ".*/*", "__pycache__", "__pycache__/*"],
    "include": [".gitignore", ".gittouch", ".touch"],
    "skip_if_exists": [],
}

DEFAULT_DATA = {"now": datetime.datetime.utcnow}
RE_TMPL = re.compile(r"\.(tmpl|append)$", re.IGNORECASE)


def default_render_as(src_path, dst_path):
    if dst_path.suffix in (".tmpl", ".append"):
        return Path(re.sub(RE_TMPL, "", str(dst_path)))


def resolve_source_path(src_path):
    src_path = Path(src_path).resolve()
    if not src_path.exists():
        raise ValueError("Project template not found")

    if not src_path.is_dir():
        raise ValueError("The project template must be a folder")

    return src_path


def copy_local(
    src_path,
    dst_path,
    data=None,
    *,
    exclude=None,
    include=None,
    skip_if_exists=None,
    envops=None,
    render_as=None,
    get_context=None,
    **flags,
):
    src_path = resolve_source_path(src_path)
    dst_path = Path(dst_path).resolve()
    render_as = render_as or default_render_as
    get_context = get_context

    user_settings = {
        "exclude": exclude,
        "include": include,
        "skip_if_exists": skip_if_exists,
    }
    config = get_config(user_settings, src_path, flags)
    config["exclude"].extend(["hecto.yaml", "hecto.yml"])

    envops = envops or {}
    envops.setdefault("block_start_string", "[%")
    envops.setdefault("block_end_string", "%]")
    envops.setdefault("variable_start_string", "[[")
    envops.setdefault("variable_end_string", "]]")

    _data = DEFAULT_DATA.copy()
    _data.update(data or {})
    _data.setdefault("folder_name", dst_path.name)
    render = JinjaRender(src_path, _data, envops)

    exclude_patterns = [render.string(pattern) for pattern in config["exclude"]]
    include_patterns = [render.string(pattern) for pattern in config["include"]]
    skip_if_exists_patterns = [
        render.string(pattern) for pattern in config["skip_if_exists"]
    ]

    must_exclude = make_matcher(exclude_patterns)
    must_include = make_matcher(include_patterns)
    must_filter = make_filter(must_exclude, must_include)
    must_skip_if_exists = make_matcher(skip_if_exists_patterns)

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
            render_file(
                dst_path,
                rel_path,
                source_path,
                render,
                render_as,
                get_context,
                must_skip_if_exists,
                flags,
            )


def get_config(user_settings, src_path, flags):
    try:
        return load_config(
            GLOBAL_DEFAULTS,
            user_settings,
            [src_path / "hecto.yaml", src_path / "hecto.yml"],
        )
    except yaml.YAMLError:
        printf_exception(
            "INVALID CONFIG FILE", msg="hecto.yaml", quiet=flags.get("quiet")
        )
        return GLOBAL_DEFAULTS


def get_source_paths(folder, rel_folder, files, render, must_filter):
    source_paths = []
    for src_name in files:
        dst_name = render.string(src_name)
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
        printf("identical", display_path, style=Style.IGNORE, quiet=flags["quiet"])
        return

    make_folder(final_path, pretend=flags["pretend"])
    printf("created", display_path, style=Style.OK, quiet=flags["quiet"])


def render_file(
    dst_path,
    rel_path,
    source_path,
    render,
    render_as,
    get_context,
    must_skip_if_exists,
    flags,
):
    """Process or copy a file of the skeleton.
    """
    render_to = render_as(source_path, rel_path)
    if render_to:
        context = get_context(rel_path) if get_context else {}
        content = render(source_path, **context)
        rel_path = render_to
        append = str(source_path).endswith(".append")
    else:
        content = None
        append = False

    display_path = str(rel_path)
    final_path = dst_path / rel_path
    exists = final_path.exists()

    if exists and append:
        printf("extended", display_path, style=Style.OK, quiet=flags["quiet"])
    elif exists:
        if file_is_identical(source_path, final_path, content):
            printf("identical", display_path, style=Style.IGNORE, quiet=flags["quiet"])
            return

        if must_skip_if_exists(rel_path):
            printf("skipped", display_path, style=Style.WARNING, quiet=flags["quiet"])
            return

        if overwrite_file(display_path, source_path, final_path, content, flags):
            printf("updated", display_path, style=Style.WARNING, quiet=flags["quiet"])
        else:
            printf("skipped", display_path, style=Style.WARNING, quiet=flags["quiet"])
            return
    else:
        printf("created", display_path, style=Style.OK, quiet=flags["quiet"])

    if flags["pretend"]:
        return

    if content is None:
        copy_file(source_path, final_path)
    elif append:
        with final_path.open("a") as f:
            f.write(content)
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
    if flags["force"]:
        return True
    if flags["skip"]:  # pragma: no cover
        return False

    printf("conflict", display_path, style=Style.DANGER, quiet=flags["quiet"])
    msg = f" Overwrite {final_path}?"  # pragma: no cover
    return prompt_bool(msg, default=True)  # pragma: no cover
