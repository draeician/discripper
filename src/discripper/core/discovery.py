"""Discovery helpers for external inspection tools."""

from __future__ import annotations

from dataclasses import dataclass
from shutil import which as default_which
from typing import Callable, Iterable, Optional

__all__ = [
    "ToolAvailability",
    "InspectionTools",
    "BLURAY_INSPECTOR_CANDIDATES",
    "discover_inspection_tools",
]


@dataclass(frozen=True, slots=True)
class ToolAvailability:
    """Information about a discovered external command."""

    command: str
    path: str


@dataclass(frozen=True, slots=True)
class InspectionTools:
    """Bundle of the external tools used for disc inspection."""

    dvd: Optional[ToolAvailability]
    fallback: Optional[ToolAvailability]
    blu_ray: Optional[ToolAvailability]


BLURAY_INSPECTOR_CANDIDATES: tuple[str, ...] = (
    "makemkvcon",
    "bd_info",
)
"""Candidate commands that can act as a Blu-ray inspector."""


def _discover_single(
    command: str, which: Callable[[str], Optional[str]],
) -> Optional[ToolAvailability]:
    path = which(command)
    if path:
        return ToolAvailability(command=command, path=path)
    return None


def _discover_first(
    commands: Iterable[str], which: Callable[[str], Optional[str]],
) -> Optional[ToolAvailability]:
    for command in commands:
        found = _discover_single(command, which)
        if found is not None:
            return found
    return None


def discover_inspection_tools(
    *, which: Callable[[str], Optional[str]] = default_which,
) -> InspectionTools:
    """Return available inspection tools for DVD and Blu-ray discs."""

    dvd = _discover_single("lsdvd", which)
    fallback = _discover_single("ffprobe", which)
    blu_ray = _discover_first(BLURAY_INSPECTOR_CANDIDATES, which)
    return InspectionTools(dvd=dvd, fallback=fallback, blu_ray=blu_ray)
