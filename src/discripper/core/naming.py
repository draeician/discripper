"""Utilities for creating filesystem-safe names from disc metadata."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Mapping
import string
import unicodedata

__all__ = ["sanitize_component", "movie_output_path", "series_output_path"]

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from . import TitleInfo

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


def _extract_naming_preferences(
    config: Mapping[str, object],
) -> tuple[str, bool]:
    """Return separator and lowercase preferences from *config*."""

    separator = _FALLBACK_SEPARATOR
    lowercase = False

    naming_config = config.get("naming")
    if isinstance(naming_config, Mapping):
        configured_separator = naming_config.get("separator")
        if isinstance(configured_separator, str):
            separator = configured_separator

        lowercase = bool(naming_config.get("lowercase", False))

    return separator, lowercase


def _output_directory_from_config(config: Mapping[str, object]) -> Path:
    output_dir_value = config.get("output_directory")
    if not isinstance(output_dir_value, (str, Path)):
        raise ValueError("Configuration must define an 'output_directory' string or path")

    return Path(output_dir_value).expanduser()


def movie_output_path(
    title: "TitleInfo",
    config: Mapping[str, object],
) -> Path:
    """Return the destination path for a movie title based on *config*."""

    separator, lowercase = _extract_naming_preferences(config)
    sanitized_title = sanitize_component(
        title.label,
        separator=separator,
        lowercase=lowercase,
    )

    return _output_directory_from_config(config) / f"{sanitized_title}.mp4"


def series_output_path(
    series_label: str,
    title: "TitleInfo",
    episode_code: str,
    config: Mapping[str, object],
) -> Path:
    """Return the destination path for a series episode."""

    separator, lowercase = _extract_naming_preferences(config)
    sanitized_series = sanitize_component(
        series_label,
        separator=separator,
        lowercase=lowercase,
    )
    sanitized_episode = sanitize_component(
        title.label,
        separator=separator,
        lowercase=lowercase,
    )

    directory = _output_directory_from_config(config) / sanitized_series
    filename = f"{sanitized_series}-{episode_code}_{sanitized_episode}.mp4"
    return directory / filename
