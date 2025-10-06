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


def test_load_config_overrides_menu_ocr_settings(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "metadata:\n"
        "  menu_ocr:\n"
        "    enabled: true\n"
        "    backend: easyocr\n"
        "    language: spa\n"
        "    confidence_threshold: 0.9\n"
        "    frame_sample_interval: 2\n"
        "    max_regions: 3\n"
    )

    loaded = config.load_config(config_file)

    menu_ocr = loaded["metadata"]["menu_ocr"]
    assert menu_ocr["enabled"] is True
    assert menu_ocr["backend"] == "easyocr"
    assert menu_ocr["language"] == "spa"
    assert menu_ocr["confidence_threshold"] == pytest.approx(0.9)
    assert menu_ocr["frame_sample_interval"] == 2
    assert menu_ocr["max_regions"] == 3


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


def test_load_config_validates_menu_ocr_types(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("metadata:\n  menu_ocr: true\n")

    with pytest.raises(ValueError, match="menu_ocr"):
        config.load_config(config_file)
