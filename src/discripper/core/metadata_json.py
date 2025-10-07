"""Utilities for exporting rip metadata to structured JSON documents."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from fractions import Fraction
from itertools import zip_longest
from pathlib import Path
from shutil import which as default_which
from subprocess import CalledProcessError, CompletedProcess, run as subprocess_run
from typing import TYPE_CHECKING, Callable, Mapping, Sequence

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from . import ClassificationResult, DiscInfo
    from .rip import RipPlan


Runner = Callable[..., CompletedProcess[str]]

__all__ = [
    "build_metadata_document",
    "write_metadata_document",
]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                return int(float(value))
            except ValueError:
                return None
    return None


def _to_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _frame_rate(stream: Mapping[str, object]) -> float | None:
    rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
    if isinstance(rate, (int, float)):
        return float(rate)
    if isinstance(rate, str):
        if "/" in rate:
            try:
                return float(Fraction(rate))
            except (ZeroDivisionError, ValueError):
                return None
        try:
            return float(rate)
        except ValueError:
            return None
    return None


def _language_from_stream(stream: Mapping[str, object]) -> str | None:
    tags = stream.get("tags")
    if isinstance(tags, Mapping):
        language = tags.get("language")
        if isinstance(language, str) and language.strip():
            return language.strip()
    return None


def _parse_streams(streams: Sequence[object] | None) -> list[dict[str, object]]:
    parsed: list[dict[str, object]] = []
    if not isinstance(streams, Sequence):
        return parsed

    for raw_stream in streams:
        if not isinstance(raw_stream, Mapping):
            continue

        codec_type = raw_stream.get("codec_type")
        if not isinstance(codec_type, str):
            continue

        stream_info: dict[str, object] = {
            "type": codec_type,
            "index": raw_stream.get("index"),
            "codec": raw_stream.get("codec_name"),
            "codec_long": raw_stream.get("codec_long_name"),
            "bit_rate": _to_int(raw_stream.get("bit_rate")),
            "language": _language_from_stream(raw_stream),
        }

        if codec_type == "video":
            stream_info.update(
                {
                    "width": raw_stream.get("width"),
                    "height": raw_stream.get("height"),
                    "frame_rate": _frame_rate(raw_stream),
                    "pixel_format": raw_stream.get("pix_fmt"),
                }
            )
        elif codec_type == "audio":
            stream_info.update(
                {
                    "channels": raw_stream.get("channels"),
                    "channel_layout": raw_stream.get("channel_layout"),
                    "sample_rate": _to_int(raw_stream.get("sample_rate")),
                }
            )
        elif codec_type == "subtitle":
            subtitle_tags = raw_stream.get("tags")
            if isinstance(subtitle_tags, Mapping):
                stream_info["title"] = subtitle_tags.get("title")

        parsed.append(stream_info)

    return parsed


def _chapter_map(plan: "RipPlan") -> list[dict[str, object]]:
    chapters: list[dict[str, object]] = []
    for index, chapter_duration in enumerate(plan.title.chapters, start=1):
        chapters.append(
            {
                "index": index,
                "duration_seconds": chapter_duration.total_seconds(),
            }
        )
    return chapters


def _ffprobe_payload(
    ffprobe_path: str,
    media_path: Path,
    *,
    runner: Runner,
) -> Mapping[str, object] | None:
    try:
        result = runner(
            (
                ffprobe_path,
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                "-show_chapters",
                str(media_path),
            ),
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, CalledProcessError, OSError):
        return None

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None

    if isinstance(payload, Mapping):
        return payload
    return None


def _format_info(payload: Mapping[str, object] | None) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        return {}

    format_section = payload.get("format")
    if not isinstance(format_section, Mapping):
        return {}

    return {
        "container": format_section.get("format_name"),
        "duration_seconds": _to_float(format_section.get("duration")),
        "bit_rate": _to_int(format_section.get("bit_rate")),
    }


def _collect_tool_versions(
    plans: Sequence["RipPlan"],
    *,
    runner: Runner,
    ffprobe_path: str | None,
) -> dict[str, str | None]:
    tools: set[str] = set()
    for plan in plans:
        if plan.command:
            tools.add(plan.command[0])
    if ffprobe_path:
        tools.add(Path(ffprobe_path).name)

    versions: dict[str, str | None] = {}
    for tool in sorted(tools):
        versions[tool] = _probe_version(tool, runner=runner)
    return versions


def _probe_version(tool: str, *, runner: Runner) -> str | None:
    for flag in ("--version", "-version"):
        try:
            result = runner(
                (tool, flag),
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, CalledProcessError, OSError):
            continue

        text = (result.stdout or result.stderr or "").strip()
        if text:
            return text.splitlines()[0]

    return None


def _metadata_output_path(plans: Sequence["RipPlan"]) -> Path | None:
    for plan in plans:
        if plan.will_execute:
            return plan.destination.parent
    return None


def build_metadata_document(
    disc: "DiscInfo",
    classification: "ClassificationResult",
    plans: Sequence["RipPlan"],
    *,
    config: Mapping[str, object],
    which: Callable[[str], str | None] = default_which,
    ffprobe_runner: Runner = subprocess_run,
    version_runner: Runner = subprocess_run,
    now: Callable[[], datetime] = _now_utc,
) -> dict[str, object]:
    ffprobe_path = which("ffprobe")
    metadata_root = _metadata_output_path(plans)

    tracks: list[dict[str, object]] = []
    episode_codes: Sequence[str | None] = ()
    if classification.episode_codes:
        episode_codes = classification.episode_codes
    else:
        episode_codes = tuple(None for _ in classification.episodes)

    for index, pair in enumerate(zip_longest(plans, episode_codes, fillvalue=None), start=1):
        plan = pair[0]
        if plan is None:
            continue
        episode_code = pair[1]
        output_path = plan.destination
        exists = output_path.exists()
        size_bytes: int | None = None
        if exists:
            try:
                size_bytes = output_path.stat().st_size
            except OSError:
                size_bytes = None

        ffprobe_payload = None
        if ffprobe_path and exists:
            ffprobe_payload = _ffprobe_payload(ffprobe_path, output_path, runner=ffprobe_runner)

        track_document: dict[str, object] = {
            "index": index,
            "title": plan.title.label,
            "episode_code": episode_code,
            "planned_duration_seconds": plan.title.duration.total_seconds(),
            "chapters": {
                "count": len(plan.title.chapters),
                "map": _chapter_map(plan),
            },
            "output": {
                "path": str(output_path),
                "container": output_path.suffix[1:] if output_path.suffix else None,
                "exists": exists,
                "size_bytes": size_bytes,
            },
            "format": _format_info(ffprobe_payload),
            "streams": _parse_streams(
                ffprobe_payload.get("streams") if isinstance(ffprobe_payload, Mapping) else None
            ),
        }

        tracks.append(track_document)

    document: dict[str, object] = {
        "generated_at": now().isoformat(),
        "disc": {
            "label": disc.label,
            "id": None,
        },
        "classification": {
            "type": classification.disc_type,
            "episode_count": len(classification.episodes),
        },
        "title": config.get("title"),
        "output_root": str(metadata_root) if metadata_root else None,
        "tools": _collect_tool_versions(plans, runner=version_runner, ffprobe_path=ffprobe_path),
        "tracks": tracks,
    }

    return document


def write_metadata_document(document: Mapping[str, object], directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "metadata.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return path

