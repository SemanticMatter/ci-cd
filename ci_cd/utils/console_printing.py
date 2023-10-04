"""Relevant tools for printing to the console."""
import platform
from enum import Enum


class Emoji(str, Enum):
    """Unicode strings for certain emojis."""

    def __new__(cls, value: str) -> "Emoji":
        obj = str.__new__(cls, value)
        if platform.system() == "Windows":
            # Windows does not support unicode emojis, so we replace them with
            # their corresponding unicode escape sequences
            obj._value_ = value.encode("unicode_escape").decode("utf-8")
        else:
            obj._value_ = value
        return obj

    PARTY_POPPER = "\U0001f389"
    CHECK_MARK = "\u2714"
    CROSS_MARK = "\u274c"
    CURLY_LOOP = "\u27b0"
