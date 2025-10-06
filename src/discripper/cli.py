"""Command-line interface for the discripper tool."""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .config import load_config
from .core import (
    BluRayNotSupportedError,
    ClassificationResult,
    DiscInfo,
    InspectionTools,
    RipExecutionError,
    RipPlan,
    TitleInfo,
    ToolAvailability,
    classify_disc,
    discover_inspection_tools,
    inspect_dvd,
    inspect_from_fixture,
    inspect_with_ffprobe,
    movie_output_path,
    rip_disc,
    run_rip_plan,
    series_output_path,
    thresholds_from_config,
)


logger = logging.getLogger(__name__)


# Exit code definitions.  These mirror the expectations outlined in the PRD
# and keep :func:`main` readable when returning early.  The values are
# intentionally small integers so they map cleanly onto the shell's exit status
# semantics.
EXIT_SUCCESS = 0
EXIT_DISC_NOT_DETECTED = 1
EXIT_RIP_FAILED = 2
EXIT_UNEXPECTED_ERROR = 3


def _print_error(message: str) -> None:
    """Emit *message* to :data:`sys.stderr` with a standard prefix."""

    print(f"Error: {message}", file=sys.stderr)


def _inspect_disc(device: str, tools: InspectionTools) -> DiscInfo:
    """Return :class:`DiscInfo` for *device* using discovered *tools*."""

    dvd_tool = tools.dvd
    if isinstance(dvd_tool, ToolAvailability):
        return inspect_dvd(device, tool=dvd_tool)

    fallback_tool = tools.fallback
    if isinstance(fallback_tool, ToolAvailability):
        return inspect_with_ffprobe(device, tool=fallback_tool)

    raise RuntimeError(
        "No supported inspection tools found. Install 'lsdvd' or 'ffprobe' and try again."
    )


def _destination_factory(
    disc: DiscInfo,
    classification: ClassificationResult,
    config: Mapping[str, Any],
) -> Callable[[TitleInfo, str | None], Path]:
    """Return a destination factory compatible with :func:`rip_disc`."""

    def factory(title: TitleInfo, episode_code: str | None) -> Path:
        if classification.disc_type == "movie":
            return movie_output_path(title, config)

        if not episode_code:
            raise RuntimeError(
                "Series classification requires episode codes for destination planning"
            )

        return series_output_path(disc.label, title, episode_code, config)

    return factory


def _plan_rips(
    device: str,
    classification: ClassificationResult,
    disc: DiscInfo,
    config: Mapping[str, Any],
    *,
    dry_run: bool,
):
    destination_factory = _destination_factory(disc, classification, config)
    return rip_disc(
        device,
        classification,
        destination_factory,
        dry_run=dry_run,
    )


def _compression_output_path(path: Path) -> Path:
    """Return the destination path for compressed output derived from *path*."""

    return path.with_name(f"{path.stem}-compressed{path.suffix}")


def _handbrake_command(source: Path) -> tuple[str, ...]:
    """Return the HandBrakeCLI command for compressing *source* into a new file."""

    destination = _compression_output_path(source)
    return (
        "HandBrakeCLI",
        "-i",
        str(source),
        "-o",
        str(destination),
        "--preset",
        "Fast 1080p30",
    )


def _emit_compression_plan(plan: RipPlan, *, executed: bool) -> None:
    """Log the HandBrake compression plan for *plan*'s destination."""

    command = _handbrake_command(plan.destination)
    status = "ready" if executed else "dry-run"
    logger.info(
        'EVENT=COMPRESS_PLAN STATUS=%s SOURCE="%s" OUTPUT="%s" COMMAND="%s"',
        status,
        plan.destination,
        _compression_output_path(plan.destination),
        shlex.join(command),
    )


def _execute_rip_plans(
    plans: Sequence[RipPlan], *, enable_compression: bool = False
) -> int:
    """Run *plans* sequentially and return the resulting exit code."""

    for plan in plans:
        try:
            result = run_rip_plan(plan)
        except RipExecutionError as exc:
            _print_error(str(exc))
            return exc.exit_code
        except Exception as exc:  # pragma: no cover - defensive catch-all
            _print_error(f"Unexpected ripping failure: {exc}")
            return EXIT_UNEXPECTED_ERROR
        else:
            if enable_compression:
                _emit_compression_plan(
                    plan, executed=bool(plan.will_execute and result is not None)
                )
    return EXIT_SUCCESS


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
    parser.add_argument(
        "--simulate",
        dest="simulate",
        metavar="FIXTURE",
        help=argparse.SUPPRESS,
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

    if getattr(args, "simulate", None):
        config["simulate"] = args.simulate

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


def _run_main(argv: Sequence[str] | None = None) -> int:
    """Execute the CLI and return an appropriate exit code."""

    args = parse_arguments(argv)
    config = resolve_cli_config(args)
    configure_logging(config)

    simulate_fixture = config.get("simulate")

    disc: DiscInfo
    if simulate_fixture:
        try:
            disc = inspect_from_fixture(simulate_fixture)
        except Exception as exc:  # pragma: no cover - defensive
            _print_error(f"Failed to load simulation fixture: {exc}")
            return EXIT_DISC_NOT_DETECTED

        config["dry_run"] = True
        device = f"simulate:{Path(simulate_fixture).name}"
        config["device"] = device
    else:
        device_path = config.get("device")
        if not _is_readable_device(device_path):
            path_display = str(device_path) if device_path is not None else "<unknown>"
            _print_error(
                "device path "
                f"'{path_display}' not found or unreadable. Check that the disc is inserted "
                "and the device path is correct."
            )
            return EXIT_DISC_NOT_DETECTED

        device = str(Path(str(device_path)).expanduser())

        try:
            tools = discover_inspection_tools()
            disc = _inspect_disc(device, tools)
        except BluRayNotSupportedError as exc:
            _print_error(str(exc))
            return EXIT_DISC_NOT_DETECTED
        except Exception as exc:  # pragma: no cover - defensive
            _print_error(f"Failed to inspect disc: {exc}")
            return EXIT_DISC_NOT_DETECTED

    thresholds = thresholds_from_config(config)
    classification = classify_disc(disc, thresholds=thresholds)
    logger.info(
        "EVENT=CLASSIFIED TYPE=%s EPISODES=%d LABEL=\"%s\"",
        classification.disc_type,
        len(classification.episodes),
        disc.label,
    )

    try:
        plans = _plan_rips(
            device,
            classification,
            disc,
            config,
            dry_run=bool(config.get("dry_run", False)),
        )
    except Exception as exc:
        _print_error(f"Failed to prepare rip plan: {exc}")
        return EXIT_UNEXPECTED_ERROR

    return _execute_rip_plans(
        plans,
        enable_compression=bool(config.get("compression", False)),
    )


def _handle_unexpected_exception(exc: Exception) -> int:
    """Log *exc* when debugging and surface a friendly user message."""

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Unhandled exception encountered", exc_info=exc)

    _print_error("An unexpected error occurred. Run with --verbose for details.")
    return EXIT_UNEXPECTED_ERROR


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the console script."""

    try:
        return _run_main(argv)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        _print_error("Operation cancelled by user.")
        return EXIT_UNEXPECTED_ERROR
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return _handle_unexpected_exception(exc)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
