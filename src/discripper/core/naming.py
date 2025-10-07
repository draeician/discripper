"""Utilities for creating filesystem-safe names from disc metadata."""

from __future__ import annotations

import re
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Mapping
import string
import unicodedata

__all__ = [
    "sanitize_component",
    "movie_output_path",
    "series_output_path",
    "select_disc_title",
    "TITLE_SOURCE_KEY",
]

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from . import DiscInfo, TitleInfo

_SAFE_CHARS = set(string.ascii_letters + string.digits)
_FALLBACK_NAME = "untitled"
_FALLBACK_SEPARATOR = "_"
_SLUG_SEPARATOR = "-"
_DEFAULT_DIRECTORY_PATTERN = "{slug}"
_DEFAULT_FILENAME_PATTERN = "{slug}_track{index:02d}{extension}"
_EPISODE_CODE_PATTERN = re.compile(r"s(?P<season>\d+)e(?P<episode>\d+)", re.IGNORECASE)

TITLE_SOURCE_KEY = "_title_source"

EpisodeTitleStrategy = Callable[["TitleInfo", str | None], str]

_BUILTIN_EPISODE_STRATEGIES: dict[str, EpisodeTitleStrategy] = {}


def _register_builtin_episode_strategy(name: str, func: EpisodeTitleStrategy) -> None:
    _BUILTIN_EPISODE_STRATEGIES[name] = func


def _label_strategy(title: "TitleInfo", episode_code: str | None) -> str:
    return title.label


def _episode_number_strategy(title: "TitleInfo", episode_code: str | None) -> str:
    if not episode_code:
        return title.label

    match = _EPISODE_CODE_PATTERN.fullmatch(episode_code)
    if not match:
        return episode_code

    episode_number = int(match.group("episode"))
    return f"Episode {episode_number:02d}"


_register_builtin_episode_strategy("label", _label_strategy)
_register_builtin_episode_strategy("episode-number", _episode_number_strategy)


@lru_cache(maxsize=None)
def _load_strategy(identifier: str) -> EpisodeTitleStrategy:
    normalized = identifier.strip()
    if not normalized:
        return _BUILTIN_EPISODE_STRATEGIES["label"]

    builtin = _BUILTIN_EPISODE_STRATEGIES.get(normalized)
    if builtin is not None:
        return builtin

    if ":" not in normalized:
        available = ", ".join(sorted(_BUILTIN_EPISODE_STRATEGIES))
        raise ValueError(
            "Unknown episode title strategy '"
            f"{identifier}'. Available built-ins: {available}."
        )

    module_name, _, attribute = normalized.partition(":")
    if not module_name or not attribute:
        raise ValueError(
            "Episode title strategy must be defined as 'module:callable'."
        )

    module = import_module(module_name)
    strategy = getattr(module, attribute)
    if not callable(strategy):  # pragma: no cover - defensive
        raise TypeError(
            f"Episode title strategy '{identifier}' must be callable."
        )

    return strategy  # type: ignore[return-value]


def _strategy_from_config(
    config: Mapping[str, object]
) -> tuple[EpisodeTitleStrategy, str]:
    naming_config = config.get("naming")
    if isinstance(naming_config, Mapping):
        candidate = naming_config.get("episode_title_strategy")
        if isinstance(candidate, str):
            strategy = _load_strategy(candidate)
            return strategy, candidate

    return _BUILTIN_EPISODE_STRATEGIES["label"], "label"


def _episode_title_from_strategy(
    title: "TitleInfo",
    episode_code: str,
    config: Mapping[str, object],
) -> str:
    strategy, identifier = _strategy_from_config(config)
    try:
        inferred = strategy(title, episode_code)
    except Exception as exc:  # pragma: no cover - strategy-defined behaviour
        raise RuntimeError(
            f"Episode title strategy '{identifier}' raised an error: {exc}"
        ) from exc

    if not isinstance(inferred, str):
        raise TypeError(
            (
                "Episode title strategy '"
                f"{identifier}' must return a string, got {type(inferred).__name__}."
            )
        )

    normalized = inferred.strip()
    return normalized or title.label


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


def _ensure_unique_path(path: Path) -> Path:
    """Return a path that does not collide with an existing file.

    When *path* already exists, the function appends an incrementing suffix of
    the form ``_1``, ``_2``, … before the file extension until a free name is
    found.  The original path is returned unchanged when no collision is
    detected.
    """

    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _slugify_title(value: str) -> str:
    """Return a deterministic slug for *value* using ASCII-safe characters.

    The slug implementation follows the specification introduced for the
    title-aware ripping flow: characters are normalized to ASCII, whitespace is
    collapsed to hyphens, output is lowercased, and only alphanumeric
    characters, hyphens, and underscores are preserved. Runs of separators are
    collapsed into a single hyphen. When the resulting slug would be empty, a
    stable fallback string is returned.
    """

    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")

    pieces: list[str] = []
    previous_was_separator = False
    for char in ascii_only:
        if char.isalnum():
            pieces.append(char.lower())
            previous_was_separator = False
            continue

        if char in "-_":
            candidate = char
        elif char.isspace():
            candidate = _SLUG_SEPARATOR
        else:
            candidate = _SLUG_SEPARATOR

        if not previous_was_separator:
            pieces.append(candidate)
            previous_was_separator = True

    slug = "".join(pieces).strip("-_")
    return slug or _FALLBACK_NAME


def _disc_slug_from_config(config: Mapping[str, object], fallback: str) -> str:
    configured = config.get("title")
    if isinstance(configured, str):
        normalized = configured.strip()
        if normalized:
            return _slugify_title(normalized)

    return _slugify_title(fallback)


def _naming_patterns(config: Mapping[str, object]) -> tuple[str, str]:
    directory_pattern = _DEFAULT_DIRECTORY_PATTERN
    filename_pattern = _DEFAULT_FILENAME_PATTERN

    naming_config = config.get("naming")
    if isinstance(naming_config, Mapping):
        directory_candidate = naming_config.get("disc_directory_pattern")
        if isinstance(directory_candidate, str) and directory_candidate.strip():
            directory_pattern = directory_candidate

        filename_candidate = naming_config.get("track_filename_pattern")
        if isinstance(filename_candidate, str) and filename_candidate.strip():
            filename_pattern = filename_candidate

    return directory_pattern, filename_pattern


def _render_pattern(pattern: str, *, slug: str, index: int, extension: str) -> str:
    ext = extension[1:] if extension.startswith(".") else extension
    try:
        rendered = pattern.format(slug=slug, index=index, extension=extension, ext=ext)
    except KeyError as exc:  # pragma: no cover - defensive, validated via tests
        missing = exc.args[0]
        raise ValueError(
            (
                "Naming pattern must use only the placeholders 'slug', 'index', "
                f"'extension', or 'ext'. Missing: {missing!r}."
            )
        ) from exc

    normalized = rendered.strip()
    if not normalized:
        raise ValueError("Naming pattern rendered an empty value")

    return normalized


def _build_slugged_path(
    slug: str,
    *,
    track_index: int,
    config: Mapping[str, object],
    extension: str = ".mp4",
) -> Path:
    directory_pattern, filename_pattern = _naming_patterns(config)

    directory_segment = _render_pattern(
        directory_pattern,
        slug=slug,
        index=track_index,
        extension=extension,
    )
    filename = _render_pattern(
        filename_pattern,
        slug=slug,
        index=track_index,
        extension=extension,
    )

    output_root = _output_directory_from_config(config)
    directory = (output_root / directory_segment).expanduser()

    return _ensure_unique_path(directory / filename)


def movie_output_path(
    title: "TitleInfo",
    config: Mapping[str, object],
    *,
    track_index: int = 1,
) -> Path:
    """Return the destination path for a movie title based on *config*.

    The path now incorporates the disc title slug so that ``--title`` or the
    auto-detected fallback drives both the directory and filename.
    """

    slug = _disc_slug_from_config(config, title.label)
    return _build_slugged_path(slug, track_index=track_index, config=config)


def series_output_path(
    series_label: str,
    title: "TitleInfo",
    episode_code: str,
    config: Mapping[str, object],
    *,
    track_index: int = 1,
) -> Path:
    """Return the destination path for a series episode.

    Series outputs share the same slug-driven directory and filename pattern as
    movies so downstream processing can rely on deterministic naming. Episode
    metadata continues to be inferred for other behaviours (e.g., metadata
    writers) even though it is no longer embedded in the filename itself.
    """

    slug = _disc_slug_from_config(config, series_label)
    return _build_slugged_path(slug, track_index=track_index, config=config)


def select_disc_title(
    config: Mapping[str, object],
    disc: "DiscInfo",
) -> tuple[str, str]:
    """Return the effective disc title and its provenance.

    The helper inspects the configuration for a ``title`` override and normalizes
    it. When present, it is treated as the authoritative value and the source is
    derived from :data:`TITLE_SOURCE_KEY` when available. When no override exists
    (or it is empty), the disc label is used as a fallback. Ultimately the
    function always returns a non-empty ASCII-safe string so downstream naming
    utilities can rely on deterministic behaviour.
    """

    configured = config.get("title")
    if isinstance(configured, str):
        normalized = configured.strip()
        if normalized:
            source = config.get(TITLE_SOURCE_KEY)
            if isinstance(source, str) and source.strip():
                return normalized, source
            return normalized, "config"

    label = disc.label.strip()
    if label:
        return label, "disc-label"

    return _FALLBACK_NAME, "fallback"
