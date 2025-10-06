"""Tests for the discripper command-line interface."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from discripper import cli
import pytest


def _write_config(tmp_path: Path, content: dict[str, object]) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(content), encoding="utf-8")
    return config_path


def test_parse_arguments_supports_expected_flags() -> None:
    """The CLI parser recognises the config, verbose, and dry-run flags."""

    args = cli.parse_arguments(["--config", "example.yaml", "--verbose", "--dry-run"])

    assert args.config_path == "example.yaml"
    assert args.verbose is True
    assert args.dry_run is True


def test_parse_arguments_includes_device_with_default() -> None:
    """The parser exposes a device argument with the expected default value."""

    args = cli.parse_arguments([])

    assert args.device == "/dev/sr0"


def test_resolve_cli_config_uses_custom_config_path(tmp_path) -> None:
    """Providing --config loads and returns the specified configuration file."""

    config_path = _write_config(
        tmp_path,
        {
            "logging": {"level": "WARNING"},
            "dry_run": False,
        },
    )

    args = cli.parse_arguments(["--config", str(config_path)])
    resolved = cli.resolve_cli_config(args)

    assert resolved["logging"]["level"] == "WARNING"
    assert resolved["dry_run"] is False


def test_resolve_cli_config_sets_device_from_arguments(tmp_path) -> None:
    """The device argument is propagated into the resolved configuration."""

    config_path = _write_config(tmp_path, {})

    args = cli.parse_arguments(["--config", str(config_path), "/dev/dvd"])
    resolved = cli.resolve_cli_config(args)

    assert resolved["device"] == "/dev/dvd"


def test_resolve_cli_config_overrides_logging_with_verbose(tmp_path) -> None:
    """--verbose forces the logging level to DEBUG regardless of config value."""

    config_path = _write_config(tmp_path, {"logging": {"level": "INFO"}})

    args = cli.parse_arguments(["--config", str(config_path), "--verbose"])
    resolved = cli.resolve_cli_config(args)

    assert resolved["logging"]["level"] == "DEBUG"


def test_resolve_cli_config_sets_dry_run_flag(tmp_path) -> None:
    """--dry-run updates the configuration to reflect a dry run."""

    config_path = _write_config(tmp_path, {"dry_run": False})

    args = cli.parse_arguments(["--config", str(config_path), "--dry-run"])
    resolved = cli.resolve_cli_config(args)

    assert resolved["dry_run"] is True


def test_resolve_cli_config_applies_precedence(tmp_path) -> None:
    """Defaults are overridden by config file, which in turn yields to CLI flags."""

    config_path = _write_config(
        tmp_path,
        {
            "output_directory": "/mnt/custom",
            "logging": {"level": "WARNING"},
            "dry_run": False,
        },
    )

    args = cli.parse_arguments(
        ["--config", str(config_path), "--verbose", "--dry-run"]
    )
    resolved = cli.resolve_cli_config(args)

    assert resolved["output_directory"] == "/mnt/custom"
    assert resolved["logging"]["level"] == "DEBUG"
    assert resolved["dry_run"] is True


def test_cli_help_mentions_device_default() -> None:
    """The help output mentions the default device path."""

    help_text = cli.build_argument_parser().format_help()

    assert "/dev/sr0" in help_text


def test_cli_main_help_output_lists_expected_options(capsys) -> None:
    """Running the CLI with --help shows usage and all defined options."""

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0

    captured = capsys.readouterr().out

    assert "usage: discripper" in captured
    assert "--config" in captured
    assert "--verbose" in captured
    assert "--dry-run" in captured


def test_main_configures_info_logging_by_default() -> None:
    """INFO logging is enabled when --verbose is not supplied."""

    logging.basicConfig(level=logging.NOTSET, force=True)
    try:
        cli.main([])
        assert logging.getLogger().getEffectiveLevel() == logging.INFO
    finally:
        logging.basicConfig(level=logging.NOTSET, force=True)


def test_main_configures_debug_logging_with_verbose() -> None:
    """DEBUG logging is enabled when --verbose is provided."""

    logging.basicConfig(level=logging.NOTSET, force=True)
    try:
        cli.main(["--verbose"])
        assert logging.getLogger().getEffectiveLevel() == logging.DEBUG
    finally:
        logging.basicConfig(level=logging.NOTSET, force=True)
