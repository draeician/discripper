from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from discripper import config


def _flatten(mapping: Mapping[str, object], prefix: str = ""):
    for key, value in mapping.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping):
            yield from _flatten(value, path)
        else:
            yield path, value


def _format_default(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        home = str(Path.home())
        if home and value.startswith(home):
            remainder = value[len(home) :].lstrip("/")
            return f"~/{remainder}" if remainder else "~"
        return value
    return str(value)


def test_readme_defaults_table_matches_defaults() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    parts = readme.split("### Defaults & overrides", maxsplit=1)
    assert len(parts) == 2, "Defaults & overrides section missing"

    section = parts[1]
    if "###" in section:
        section = section.split("###", maxsplit=1)[0]

    table_block = re.findall(r"^\|.*$", section, flags=re.MULTILINE)
    assert table_block, "Defaults & overrides table is missing"

    lines = [line.strip() for line in table_block]
    table_defaults: dict[str, str] = {}
    for line in lines:
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        setting_cell, default_cell = cells[0], cells[1]
        setting = setting_cell.strip("`")
        if setting in {"Setting", ""}:
            continue
        table_defaults[setting] = default_cell.strip("`")

    expected_config_path = str(config.CONFIG_PATH)
    assert (
        table_defaults.get("Configuration file path") == expected_config_path
    ), "Configuration file path row mismatch"

    for path, value in _flatten(config.DEFAULT_CONFIG):
        formatted = _format_default(value)
        assert path in table_defaults, f"Missing defaults row for {path}"
        assert (
            table_defaults[path] == formatted
        ), f"Default mismatch for {path}: expected {formatted!r}"
