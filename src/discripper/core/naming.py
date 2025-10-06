"""Utilities for creating filesystem-safe names from disc metadata."""
from __future__ import annotations

import string
import unicodedata

__all__ = ["sanitize_component"]

_SAFE_CHARS = set(string.ascii_letters + string.digits)
_FALLBACK_NAME = "untitled"
_FALLBACK_SEPARATOR = "_"


def _normalize_separator(separator: str) -> str:
    """Return a single ASCII character usable as a separator."""

    if not separator:
        return _FALLBACK_SEPARATOR

    normalized = unicodedata.normalize("NFKD", separator)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")

    for char in ascii_only:
        if char in _SAFE_CHARS or char in "-_":
            return char

    return _FALLBACK_SEPARATOR


def sanitize_component(
    value: str,
    *,
    separator: str = _FALLBACK_SEPARATOR,
    lowercase: bool = False,
) -> str:
    """Return *value* normalized for safe filesystem usage.

    The sanitizer enforces ASCII output by stripping diacritics and removing
    characters that are not alphanumeric. Replaced characters collapse into the
    configured *separator*. Consecutive separators are reduced to a single
    instance and trimmed from the ends. When the sanitized value would be empty,
    a fallback name is returned to keep downstream paths valid. Set
    :param:`lowercase` to :data:`True` when the resulting component should be
    normalized to lowercase for case-insensitive filesystems.
    """

    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    safe_separator = _normalize_separator(separator)

    pieces: list[str] = []
    previous_was_separator = False
    for char in ascii_only:
        if char in _SAFE_CHARS:
            pieces.append(char)
            previous_was_separator = False
        else:
            if not previous_was_separator:
                pieces.append(safe_separator)
                previous_was_separator = True

    sanitized = "".join(pieces).strip(safe_separator)
    result = sanitized or _FALLBACK_NAME

    if lowercase:
        return result.lower()

    return result
