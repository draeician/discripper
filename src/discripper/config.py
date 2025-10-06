"""Configuration loading utilities for discripper."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path("~/.config/discripper.yaml")
DEFAULT_CONFIG: dict[str, Any] = {
    "output_directory": str(Path.home() / "Videos"),
    "compression": False,
    "dry_run": False,
    "classification": {
        "movie_main_title_minutes": 60,
        "movie_total_runtime_minutes": 180,
        "series_min_duration_minutes": 20,
        "series_max_duration_minutes": 60,
        "series_gap_limit": 0.2,
    },
    "naming": {
        "separator": "_",
        "lowercase": False,
    },
    "logging": {
        "level": "INFO",
    },
}

CONFIG_SCHEMA: dict[str, Any] = {
    "output_directory": str,
    "compression": bool,
    "dry_run": bool,
    "classification": {
        "movie_main_title_minutes": (int, float),
        "movie_total_runtime_minutes": (int, float),
        "series_min_duration_minutes": (int, float),
        "series_max_duration_minutes": (int, float),
        "series_gap_limit": (int, float),
    },
    "naming": {
        "separator": str,
        "lowercase": bool,
    },
    "logging": {
        "level": (str, int),
    },
}

__all__ = ["CONFIG_PATH", "DEFAULT_CONFIG", "CONFIG_SCHEMA", "load_config"]


def _merge_config(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep-merged copy of *base* with values from *overrides*."""

    merged: dict[str, Any] = deepcopy(dict(base))
    for key, value in overrides.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def _ensure_type(value: Any, expected: Any, path: str) -> None:
    if isinstance(expected, tuple):
        if not isinstance(value, expected):
            expected_names = ", ".join(sorted({t.__name__ for t in expected}))
            raise ValueError(
                f"Configuration field '{path}' must be one of the types: {expected_names}"
            )
        return

    if expected is bool:
        if not isinstance(value, bool):
            raise ValueError(f"Configuration field '{path}' must be a boolean")
        return

    if expected is str:
        if not isinstance(value, str):
            raise ValueError(f"Configuration field '{path}' must be a string")
        return

    if isinstance(expected, Mapping):
        if not isinstance(value, Mapping):
            raise ValueError(f"Configuration field '{path}' must be a mapping")
        _validate_against_schema(value, expected, prefix=path)
        return

    raise TypeError(f"Unsupported schema type for '{path}': {expected!r}")


def _validate_against_schema(
    config: Mapping[str, Any], schema: Mapping[str, Any], *, prefix: str = ""
) -> None:
    for key, expected in schema.items():
        field_path = f"{prefix}.{key}" if prefix else key
        if key not in config:
            raise ValueError(f"Configuration field '{field_path}' is required")
        value = config[key]
        _ensure_type(value, expected, field_path)


def _validate_config(config: Mapping[str, Any]) -> None:
    _validate_against_schema(config, CONFIG_SCHEMA)


def _validated_defaults() -> dict[str, Any]:
    defaults = deepcopy(DEFAULT_CONFIG)
    _validate_config(defaults)
    return defaults


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load the discripper configuration.

    Parameters
    ----------
    path:
        Optional path to the configuration file. When omitted, :data:`CONFIG_PATH` is used.

    Returns
    -------
    dict[str, Any]
        The configuration dictionary with defaults applied.

    Raises
    ------
    ValueError
        If the configuration file exists but does not contain a mapping.
    """

    config_path = Path(path).expanduser() if path else CONFIG_PATH.expanduser()

    if not config_path.exists():
        return _validated_defaults()

    raw_content = config_path.read_text(encoding="utf-8")
    if not raw_content.strip():
        return _validated_defaults()

    loaded = yaml.safe_load(raw_content)
    if loaded is None:
        return _validated_defaults()

    if not isinstance(loaded, Mapping):
        raise ValueError("Configuration file must define a mapping")

    merged = _merge_config(DEFAULT_CONFIG, loaded)
    _validate_config(merged)
    return merged
