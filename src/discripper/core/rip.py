"""Ripping helpers for turning inspected titles into actionable plans."""

from __future__ import annotations

from dataclasses import dataclass
from os import fspath
from pathlib import Path
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from . import TitleInfo


@dataclass(frozen=True, slots=True)
class RipPlan:
    """Structured description of how a single title should be ripped."""

    device: str
    title: "TitleInfo"
    destination: Path
    command: Tuple[str, ...]
    will_execute: bool


def rip_title(
    device: str | Path,
    title_info: "TitleInfo",
    dest_path: str | Path,
    *,
    dry_run: bool = False,
) -> RipPlan:
    """Return the rip plan for ``title_info`` from ``device`` to ``dest_path``.

    The function does not execute any external commands yet; it only prepares
    the command that future tasks will run.  When ``dry_run`` is :data:`True`,
    the plan records that the command should not be executed.
    """

    device_path = fspath(device)
    destination = Path(dest_path)

    command = (
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        device_path,
        str(destination),
    )

    return RipPlan(
        device=device_path,
        title=title_info,
        destination=destination,
        command=command,
        will_execute=not dry_run,
    )
