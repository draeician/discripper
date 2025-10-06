"""Tests for external tool discovery helpers."""

from __future__ import annotations

from typing import Optional

from discripper.core import (
    BLURAY_INSPECTOR_CANDIDATES,
    InspectionTools,
    ToolAvailability,
    discover_inspection_tools,
)


def test_discover_inspection_tools_prefers_primary_candidates() -> None:
    paths = {
        "lsdvd": "/usr/bin/lsdvd",
        "ffprobe": "/usr/bin/ffprobe",
        "makemkvcon": "/opt/makemkv/bin/makemkvcon",
        "bd_info": "/usr/local/bin/bd_info",
    }

    def fake_which(command: str) -> Optional[str]:
        return paths.get(command)

    discovered = discover_inspection_tools(which=fake_which)

    assert discovered == InspectionTools(
        dvd=ToolAvailability("lsdvd", paths["lsdvd"]),
        fallback=ToolAvailability("ffprobe", paths["ffprobe"]),
        blu_ray=ToolAvailability("makemkvcon", paths["makemkvcon"]),
    )


def test_discover_inspection_tools_uses_first_available_blu_ray_candidate() -> None:
    fallback_paths = {
        "lsdvd": None,
        "ffprobe": None,
        "makemkvcon": None,
        "bd_info": "/usr/bin/bd_info",
    }

    def fake_which(command: str) -> Optional[str]:
        return fallback_paths.get(command)

    discovered = discover_inspection_tools(which=fake_which)

    assert discovered.dvd is None
    assert discovered.fallback is None
    assert discovered.blu_ray == ToolAvailability("bd_info", "/usr/bin/bd_info")


def test_discover_inspection_tools_handles_missing_commands() -> None:
    def fake_which(command: str) -> Optional[str]:  # pragma: no cover - defensive
        return None

    discovered = discover_inspection_tools(which=fake_which)

    assert discovered == InspectionTools(dvd=None, fallback=None, blu_ray=None)


def test_blu_ray_candidate_list_is_not_empty() -> None:
    assert BLURAY_INSPECTOR_CANDIDATES
