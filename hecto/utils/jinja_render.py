import os

import jinja2
from jinja2.sandbox import SandboxedEnvironment


__all__ = ("ENVOPS_DEFAULT", "JinjaRender")

ENVOPS_DEFAULT = {"autoescape": False, "keep_trailing_newline": True}


class JinjaRender(object):
    def __init__(self, src_path, data, envops=None):
        # Jinja <= 2.10 does not work with `pathlib.Path`s
        self.src_path = str(src_path)
        self.data = data

        _envops = ENVOPS_DEFAULT.copy()
        _envops.update(envops or {})
        _envops.setdefault("loader", jinja2.FileSystemLoader(self.src_path))
        self.env = SandboxedEnvironment(**_envops)

    def __call__(self, fullpath):
        relpath = str(fullpath).replace(self.src_path, "", 1).lstrip(os.path.sep)
        tmpl = self.env.get_template(relpath)
        return tmpl.render(**self.data)

    def string(self, string):
        tmpl = self.env.from_string(string)
        return tmpl.render(**self.data)
