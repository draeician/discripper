"""Configuration loading utilities for discripper."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import yaml

CONFIG_PATH = Path("~/.config/discripper.yaml")
DEFAULT_CONFIG: dict[str, Any] = {
    "output_directory": str(Path.home() / "Videos"),
    "compression": False,
    "naming": {
        "separator": "_",
        "lowercase": False,
    },
    "logging": {
        "level": "INFO",
    },
}

__all__ = ["CONFIG_PATH", "DEFAULT_CONFIG", "load_config"]


def _merge_config(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep-merged copy of *base* with values from *overrides*."""

    merged: dict[str, Any] = deepcopy(dict(base))
    for key, value in overrides.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


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
        return deepcopy(DEFAULT_CONFIG)

    raw_content = config_path.read_text(encoding="utf-8")
    if not raw_content.strip():
        return deepcopy(DEFAULT_CONFIG)

    loaded = yaml.safe_load(raw_content)
    if loaded is None:
        return deepcopy(DEFAULT_CONFIG)

    if not isinstance(loaded, Mapping):
        raise ValueError("Configuration file must define a mapping")

    return _merge_config(DEFAULT_CONFIG, loaded)
