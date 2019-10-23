import errno
import os
import shutil


def make_folder(folder, pretend=False):
    if pretend:
        return
    if not folder.exists():
        try:
            os.makedirs(str(folder))
        except OSError as e:  # pragma: no cover
            if e.errno != errno.EEXIST:
                raise


def copy_file(src, dst):
    shutil.copy2(str(src), str(dst))
