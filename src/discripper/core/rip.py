"""Ripping helpers for turning inspected titles into actionable plans."""

from __future__ import annotations

import logging
import shlex
from collections.abc import Callable
from dataclasses import dataclass
from os import fspath
from pathlib import Path
from shutil import which as default_which
from subprocess import (
    CalledProcessError,
    CompletedProcess,
    run as subprocess_run,
)
from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from . import ClassificationResult, TitleInfo


logger = logging.getLogger(__name__)


def _log_rip_failure(plan: RipPlan, reason: str, exit_code: int) -> None:
    """Emit a structured log entry describing a failed rip attempt."""

    logger.error(
        'EVENT=RIP_FAILED FILE="%s" EXIT_CODE=%d REASON="%s"',
        plan.destination,
        exit_code,
        reason,
    )


@dataclass(frozen=True, slots=True)
class RipPlan:
    """Structured description of how a single title should be ripped."""

    device: str
    title: "TitleInfo"
    destination: Path
    command: Tuple[str, ...]
    will_execute: bool


class RipExecutionError(RuntimeError):
    """Error raised when executing an external ripping command fails."""

    exit_code: int

    def __init__(self, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _ffmpeg_command(device: str, destination: Path) -> Tuple[str, ...]:
    return (
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        device,
        str(destination),
    )


def _dvdbackup_command(device: str, title_info: "TitleInfo", destination: Path) -> Tuple[str, ...]:
    output_dir = destination.parent
    label = destination.stem or title_info.label or "title"
    return (
        "dvdbackup",
        "-i",
        device,
        "-o",
        str(output_dir),
        "-n",
        label,
        "-F",
    )


def _select_rip_command(
    device: str,
    title_info: "TitleInfo",
    destination: Path,
    which: Callable[[str], Optional[str]],
) -> Tuple[str, ...]:
    if which("dvdbackup"):
        return _dvdbackup_command(device, title_info, destination)

    if which("ffmpeg"):
        return _ffmpeg_command(device, destination)

    raise RuntimeError("No supported ripping tools found on PATH")


def rip_title(
    device: str | Path,
    title_info: "TitleInfo",
    dest_path: str | Path,
    *,
    dry_run: bool = False,
    which: Callable[[str], Optional[str]] = default_which,
) -> RipPlan:
    """Return the rip plan for ``title_info`` from ``device`` to ``dest_path``.

    The function does not execute any external commands yet; it only prepares
    the command that future tasks will run.  When ``dry_run`` is :data:`True`,
    the plan records that the command should not be executed.
    """

    device_path = fspath(device)
    destination = Path(dest_path)

    command = _select_rip_command(device_path, title_info, destination, which)

    return RipPlan(
        device=device_path,
        title=title_info,
        destination=destination,
        command=command,
        will_execute=not dry_run,
    )


def run_rip_plan(
    plan: RipPlan,
    *,
    run: Callable[..., CompletedProcess[Any]] = subprocess_run,
) -> Optional[CompletedProcess[Any]]:
    """Execute *plan* using the configured external command.

    The :class:`RipPlan` returned by :func:`rip_title` describes a full command
    tuple that reads from the optical device and writes to the destination.  This
    helper runs that command by delegating to :func:`subprocess.run` with
    ``check=True`` so callers receive an exception when the external tool
    reports a failure.

    When ``plan.will_execute`` is :data:`False` (e.g., for ``--dry-run``), the
    function does nothing and returns :data:`None`.
    """

    if not plan.will_execute:
        print(f"[dry-run] Would execute: {shlex.join(plan.command)}")
        logger.info('EVENT=RIP_SKIPPED FILE="%s" REASON=dry-run', plan.destination)
        return None

    if plan.destination.exists():
        logger.warning(
            'EVENT=RIP_GUARD FILE="%s" REASON=destination-exists',
            plan.destination,
        )
        raise RipExecutionError(
            (
                "Refusing to overwrite existing file "
                f"'{plan.destination}'. Remove the file or choose a different output path."
            ),
            exit_code=2,
        )

    plan.destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = run(plan.command, check=True)

        size_bytes: Optional[int]
        try:
            size_bytes = plan.destination.stat().st_size
        except FileNotFoundError:
            size_bytes = None
        except OSError:
            size_bytes = None

        if size_bytes is not None:
            logger.info(
                'EVENT=RIP_DONE FILE="%s" BYTES=%d STATUS=success',
                plan.destination,
                size_bytes,
            )
        else:
            logger.info(
                'EVENT=RIP_DONE FILE="%s" BYTES=unknown STATUS=success',
                plan.destination,
            )

        return result
    except FileNotFoundError as exc:  # pragma: no cover - defensive on Python <3.11
        _log_rip_failure(plan, "tool-not-found", 2)
        raise RipExecutionError(
            f"Ripping tool '{plan.command[0]}' was not found on PATH.",
            exit_code=2,
        ) from exc
    except PermissionError as exc:
        _log_rip_failure(plan, "permission-denied", 2)
        raise RipExecutionError(
            f"Permission denied while executing '{plan.command[0]}'.",
            exit_code=2,
        ) from exc
    except CalledProcessError as exc:
        _log_rip_failure(plan, f"subprocess-exit-{exc.returncode}", 2)
        raise RipExecutionError(
            (
                "Ripping command failed with exit code "
                f"{exc.returncode}: {' '.join(plan.command)}"
            ),
            exit_code=2,
        ) from exc
    except OSError as exc:  # pragma: no cover - generic OS error guard
        _log_rip_failure(plan, exc.strerror or str(exc), 2)
        raise RipExecutionError(
            f"Unexpected I/O error executing '{plan.command[0]}': {exc.strerror or exc}.",
            exit_code=2,
        ) from exc


def rip_disc(
    device: str | Path,
    classification: "ClassificationResult",
    destination_factory: Callable[["TitleInfo", str | None], str | Path],
    *,
    dry_run: bool = False,
    which: Callable[[str], Optional[str]] = default_which,
) -> Tuple[RipPlan, ...]:
    """Return rip plans for all titles selected by *classification*.

    The *destination_factory* callback receives each :class:`TitleInfo` and the
    associated episode code (``s01eNN``) when available.  It must return the
    output path where the resulting file should be written.  The function does
    not perform any I/O; it simply prepares plans by delegating to
    :func:`rip_title` for every relevant title.
    """

    episodes = classification.episodes
    episode_codes: Tuple[str | None, ...]
    if classification.episode_codes:
        episode_codes = classification.episode_codes
    else:
        episode_codes = tuple(None for _ in episodes)

    plans = []
    for title, code in zip(episodes, episode_codes):
        destination = destination_factory(title, code)
        plans.append(
            rip_title(
                device,
                title,
                destination,
                dry_run=dry_run,
                which=which,
            )
        )

    return tuple(plans)

