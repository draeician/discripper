"""Command-line interface for the discripper tool."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from .config import load_config

_PLACEHOLDER_USAGE = (
    "discripper CLI (placeholder)\n\n"
    "Usage: discripper [options]\n\n"
    "This interface will be implemented in future tasks."
)


def build_argument_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the CLI."""

    parser = argparse.ArgumentParser(
        prog="discripper", description="discripper command-line interface"
    )
    parser.add_argument(
        "device",
        nargs="?",
        default="/dev/sr0",
        help="Path to the optical media device (default: %(default)s).",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        help="Path to the configuration file to use.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging output.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing side effects.",
    )
    return parser


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments from *argv* or :data:`sys.argv`."""

    parser = build_argument_parser()
    return parser.parse_args(argv)


def _resolve_log_level(value: object) -> int:
    """Return the numeric log level for *value* with a safe default."""

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        resolved = logging.getLevelName(value.upper())
        if isinstance(resolved, int):
            return resolved

    return logging.INFO


def configure_logging(config: Mapping[str, Any]) -> None:
    """Configure the root logger based on the provided *config*."""

    level_value = None
    logging_config = config.get("logging")
    if isinstance(logging_config, Mapping):
        level_value = logging_config.get("level")

    logging.basicConfig(level=_resolve_log_level(level_value), force=True)


def resolve_cli_config(args: argparse.Namespace) -> dict[str, Any]:
    """Return the effective configuration after applying CLI overrides."""

    config = load_config(args.config_path)

    config["device"] = args.device

    if args.verbose:
        config.setdefault("logging", {})["level"] = "DEBUG"

    if args.dry_run:
        config["dry_run"] = True

    return config


def _is_readable_device(path: object) -> bool:
    """Return ``True`` if *path* points to an existing readable file."""

    if not isinstance(path, (str, Path)):
        return False

    try:
        candidate = Path(path).expanduser()
    except Exception:  # pragma: no cover - defensive
        return False

    if not candidate.exists():
        return False

    return os.access(candidate, os.R_OK)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the console script."""

    args = parse_arguments(argv)
    config = resolve_cli_config(args)
    configure_logging(config)

    device_path = config.get("device")
    if not _is_readable_device(device_path):
        path_display = str(device_path) if device_path is not None else "<unknown>"
        print(
            f"Error: device path '{path_display}' not found or unreadable. "
            "Check that the disc is inserted and the device path is correct.",
            file=sys.stderr,
        )
        return 1

    print(_PLACEHOLDER_USAGE)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
