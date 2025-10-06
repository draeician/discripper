"""Command-line interface for the discripper tool."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Sequence

from .config import load_config

_PLACEHOLDER_USAGE = (
    "discripper CLI (placeholder)\n\n"
    "Usage: discripper [options]\n\n"
    "This interface will be implemented in future tasks."
)


def build_argument_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the CLI."""

    parser = argparse.ArgumentParser(description="discripper command-line interface")
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


def resolve_cli_config(args: argparse.Namespace) -> dict[str, Any]:
    """Return the effective configuration after applying CLI overrides."""

    config = load_config(args.config_path)

    if args.verbose:
        config.setdefault("logging", {})["level"] = "DEBUG"

    if args.dry_run:
        config["dry_run"] = True

    return config


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the console script."""

    args = parse_arguments(argv)
    resolve_cli_config(args)

    print(_PLACEHOLDER_USAGE)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
