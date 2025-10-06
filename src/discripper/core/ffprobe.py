"""Fallback disc inspection using :command:`ffprobe`."""

from __future__ import annotations

import json
from datetime import timedelta
from subprocess import PIPE, CompletedProcess, run as subprocess_run
from typing import TYPE_CHECKING, Callable

from .discovery import ToolAvailability

__all__ = ["inspect_with_ffprobe"]

Runner = Callable[..., CompletedProcess[str]]

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from . import DiscInfo


def inspect_with_ffprobe(
    device: str,
    *,
    tool: ToolAvailability,
    runner: Runner = subprocess_run,
) -> "DiscInfo":
    """Inspect a disc device using :command:`ffprobe` and return structured info."""

    command = [
        tool.path,
        "-v",
        "error",
        "-show_entries",
        "format=duration:format_tags=title",
        "-of",
        "json",
        device,
    ]
    result = runner(command, check=True, stdout=PIPE, stderr=PIPE, text=True)
    return _disc_from_payload(result.stdout)


def _disc_from_payload(output: str) -> "DiscInfo":
    from . import DiscInfo, TitleInfo

    payload = _load_json(output)
    format_info = payload.get("format") if isinstance(payload, dict) else None

    label = "Unknown Disc"
    duration = timedelta()

    if isinstance(format_info, dict):
        tags = format_info.get("tags")
        if isinstance(tags, dict):
            title = tags.get("title")
            if isinstance(title, str) and title.strip():
                label = title.strip()

        duration = _parse_duration(format_info.get("duration"))

    title_label = label if label != "Unknown Disc" else "Title"
    return DiscInfo(label=label, titles=(TitleInfo(label=title_label, duration=duration),))


def _load_json(output: str) -> dict[str, object]:
    try:
        payload = json.loads(output or "{}")
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError("Unexpected ffprobe output; not valid JSON") from exc

    if isinstance(payload, dict):
        return payload
    raise ValueError("Unexpected ffprobe output; expected JSON object")


def _parse_duration(value: object) -> timedelta:
    if isinstance(value, (int, float)):
        seconds = float(value)
    elif isinstance(value, str):
        try:
            seconds = float(value)
        except ValueError:
            return timedelta()
    else:
        return timedelta()

    seconds = max(seconds, 0.0)
    seconds_int = int(seconds)
    microseconds = int(round((seconds - seconds_int) * 1_000_000))
    if microseconds >= 1_000_000:
        seconds_int += 1
        microseconds -= 1_000_000
    return timedelta(seconds=seconds_int, microseconds=microseconds)
