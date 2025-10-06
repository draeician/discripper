"""Ripping helpers for turning inspected titles into actionable plans."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from os import fspath
from pathlib import Path
from shutil import which as default_which
from subprocess import CompletedProcess, run as subprocess_run
from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from . import ClassificationResult, TitleInfo


@dataclass(frozen=True, slots=True)
class RipPlan:
    """Structured description of how a single title should be ripped."""

    device: str
    title: "TitleInfo"
    destination: Path
    command: Tuple[str, ...]
    will_execute: bool


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
        return None

    return run(plan.command, check=True)


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
