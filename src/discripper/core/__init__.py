"""Core data structures and functionality for :mod:`discripper`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Tuple

from .bluray import BluRayNotSupportedError, inspect_blu_ray
from .discovery import (
    BLURAY_INSPECTOR_CANDIDATES,
    InspectionTools,
    ToolAvailability,
    discover_inspection_tools,
)
from .dvd import inspect_dvd
from .fake import inspect_from_fixture
from .ffprobe import inspect_with_ffprobe

__all__ = [
    "DiscInfo",
    "TitleInfo",
    "InspectionTools",
    "ToolAvailability",
    "discover_inspection_tools",
    "BLURAY_INSPECTOR_CANDIDATES",
    "BluRayNotSupportedError",
    "inspect_dvd",
    "inspect_blu_ray",
    "inspect_with_ffprobe",
    "inspect_from_fixture",
    "__version__",
]


@dataclass(frozen=True, slots=True)
class TitleInfo:
    """Metadata describing a single title discovered on a disc."""

    label: str
    duration: timedelta
    chapters: Tuple[timedelta, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - simple conversion
        object.__setattr__(self, "chapters", tuple(self.chapters))


@dataclass(frozen=True, slots=True)
class DiscInfo:
    """Aggregate information for a physical disc and its titles."""

    label: str
    titles: Tuple[TitleInfo, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - simple conversion
        object.__setattr__(self, "titles", tuple(self.titles))


__version__ = "0.0.0"
