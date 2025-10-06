"""DVD inspection using :command:`lsdvd`."""

from __future__ import annotations

import ast
import re
from datetime import timedelta
from subprocess import PIPE, CompletedProcess, run as subprocess_run
from typing import TYPE_CHECKING, Callable, Iterable, Mapping, Sequence

from .discovery import ToolAvailability

__all__ = ["inspect_dvd"]

Runner = Callable[..., CompletedProcess[str]]
_DISC_PATTERN = re.compile(r"(disc|lsdvd)\s*=\s*(\{.*\})", re.DOTALL)

if TYPE_CHECKING:
    from . import DiscInfo, TitleInfo


def inspect_dvd(
    device: str,
    *,
    tool: ToolAvailability,
    runner: Runner = subprocess_run,
) -> "DiscInfo":
    """Inspect a DVD device using :command:`lsdvd` and return structured info."""

    command = [tool.path, "-Oy", "-c", device]
    result = runner(command, check=True, stdout=PIPE, stderr=PIPE, text=True)
    disc_payload = _parse_lsdvd_output(result.stdout)
    return _disc_from_payload(disc_payload)


def _parse_lsdvd_output(output: str) -> Mapping[str, object]:
    match = _DISC_PATTERN.search(output)
    if not match:
        raise ValueError("Unexpected lsdvd output; missing disc payload")

    key, payload_text = match.groups()
    payload = ast.literal_eval(payload_text)  # nosec: controlled input from lsdvd
    if not isinstance(payload, dict):
        raise ValueError("Parsed lsdvd payload is not a mapping")

    if key == "lsdvd":
        disc_payload = payload.get("disc")
        if not isinstance(disc_payload, Mapping):
            raise ValueError("Parsed lsdvd wrapper does not contain disc mapping")
        return disc_payload

    return payload


def _disc_from_payload(payload: Mapping[str, object]) -> "DiscInfo":
    from . import DiscInfo, TitleInfo

    title = str(payload.get("title", "")) or "Unknown Disc"
    tracks_data = payload.get("track")
    titles: list[TitleInfo] = []

    if isinstance(tracks_data, Mapping):
        tracks_iter: Iterable[Mapping[str, object]] = [tracks_data]
    elif isinstance(tracks_data, Sequence):
        tracks_iter = [item for item in tracks_data if isinstance(item, Mapping)]
    else:
        tracks_iter = []

    for track in sorted(tracks_iter, key=lambda item: int(item.get("ix", 0))):
        titles.append(_title_from_track(track, TitleInfo))

    return DiscInfo(label=title, titles=titles)


def _title_from_track(
    track: Mapping[str, object], title_cls: type["TitleInfo"],
) -> "TitleInfo":
    index = int(track.get("ix", 0))
    label = f"Title {index:02d}" if index else "Title"
    duration_text = str(track.get("length", "0"))
    duration = _parse_duration(duration_text)

    chapters_data = track.get("chapter") or track.get("chapters") or []
    chapters: list[timedelta] = []
    if isinstance(chapters_data, Mapping):
        chapters_data = [chapters_data]
    if isinstance(chapters_data, Sequence):
        for chapter in chapters_data:
            if isinstance(chapter, Mapping) and "length" in chapter:
                chapters.append(_parse_duration(str(chapter["length"])))

    return title_cls(label=label, duration=duration, chapters=tuple(chapters))


def _parse_duration(value: str) -> timedelta:
    hours = minutes = seconds = 0
    microseconds = 0

    parts = value.split(":")
    if len(parts) == 3:
        hours, minutes, seconds_part = parts
    elif len(parts) == 2:
        hours = 0
        minutes, seconds_part = parts
    else:
        seconds_part = parts[0] if parts else "0"

    if isinstance(hours, str):
        hours = int(hours or 0)
    if isinstance(minutes, str):
        minutes = int(minutes or 0)

    seconds_str, dot, fraction = seconds_part.partition(".")
    seconds = int(seconds_str or 0)
    if dot:
        fraction = (fraction + "000000")[:6]
        microseconds = int(fraction)

    return timedelta(hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
