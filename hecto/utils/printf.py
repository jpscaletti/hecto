from enum import Enum

import colorama
from colorama import Fore as cFore
from colorama import Style as cStyle


_all__ = ("Style", "printf", "printf_exception")

colorama.init()


class Style(Enum):
    OK = [cFore.GREEN, cStyle.BRIGHT]
    WARNING = [cFore.YELLOW, cStyle.BRIGHT]
    IGNORE = [cFore.CYAN]
    DANGER = [cFore.RED, cStyle.BRIGHT]


def printf(action, msg, style, indent=10, quiet=False):
    if quiet:
        return
    action = action.rjust(indent, " ")
    out = style.value + [action, cFore.RESET, cStyle.RESET_ALL, "  ", msg]
    print(*out, sep="")


def printf_exception(action, msg="", quiet=False):
    if not quiet:
        return printf(action, msg, style=Style.DANGER)
