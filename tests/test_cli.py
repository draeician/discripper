"""Tests for the discripper command-line interface."""

from __future__ import annotations

from pathlib import Path

import yaml

from discripper import cli


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
