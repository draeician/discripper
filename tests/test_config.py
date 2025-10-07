from __future__ import annotations

from pathlib import Path

import pytest

from discripper import config


def test_load_config_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.yaml"

    loaded = config.load_config(missing_path)

    assert loaded == config.DEFAULT_CONFIG


def test_load_config_overrides_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "output_directory: /mnt/media\n" "naming:\n" "  lowercase: true\n"
    )

    loaded = config.load_config(config_file)

    assert loaded["output_directory"] == "/mnt/media"
    assert loaded["naming"]["lowercase"] is True
    assert loaded["naming"]["separator"] == config.DEFAULT_CONFIG["naming"]["separator"]


def test_load_config_respects_logging_file(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "logging:\n" "  level: DEBUG\n" "  file: /var/log/discripper.log\n",
        encoding="utf-8",
    )

    loaded = config.load_config(config_file)

    assert loaded["logging"]["level"] == "DEBUG"
    assert loaded["logging"]["file"] == "/var/log/discripper.log"


def test_load_config_rejects_non_mapping(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("[]")

    with pytest.raises(ValueError):
        config.load_config(config_file)


def test_load_config_validates_schema_types(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("compression: 1\n")

    with pytest.raises(ValueError, match="compression"):
        config.load_config(config_file)


def test_load_config_validates_nested_schema(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("naming: lowercase\n")

    with pytest.raises(ValueError, match="naming"):
        config.load_config(config_file)


def test_load_config_overrides_metadata_and_patterns(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "metadata:\n"
        "  placement: output-root\n"
        "  directory: ~/Media/discripper\n"
        "naming:\n"
        "  track_filename_pattern: '{slug}-{index:02d}.{ext}'\n",
        encoding="utf-8",
    )

    loaded = config.load_config(config_file)

    assert loaded["metadata"]["placement"] == "output-root"
    assert loaded["metadata"]["directory"] == "~/Media/discripper"
    assert (
        loaded["naming"]["track_filename_pattern"]
        == "{slug}-{index:02d}.{ext}"
    )
