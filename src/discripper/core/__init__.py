"""Core data structures and functionality for :mod:`discripper`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Tuple

from .discovery import (
    BLURAY_INSPECTOR_CANDIDATES,
    InspectionTools,
    ToolAvailability,
    discover_inspection_tools,
)

__all__ = [
    "DiscInfo",
    "TitleInfo",
    "InspectionTools",
    "ToolAvailability",
    "discover_inspection_tools",
    "BLURAY_INSPECTOR_CANDIDATES",
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
