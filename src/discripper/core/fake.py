"""Test fixtures-backed disc inspector."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from . import DiscInfo, TitleInfo

__all__ = ["inspect_from_fixture"]

_DEFAULT_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def inspect_from_fixture(
    fixture: str | Path,
    *,
    fixture_dir: Optional[Path] = None,
) -> DiscInfo:
    """Load disc information from a JSON fixture for testing purposes."""

    path = Path(fixture)
    if not path.suffix:
        path = path.with_suffix(".json")

    base_dir = Path(fixture_dir) if fixture_dir is not None else _DEFAULT_FIXTURE_DIR
    if not path.is_absolute():
        path = base_dir / path

    payload = _load_payload(path)
    return _disc_from_payload(payload)


def _load_payload(path: Path) -> Mapping[str, object]:
    try:
        data = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise FileNotFoundError(f"Fixture not found: {path}") from exc

    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Fixture {path} does not contain valid JSON") from exc

    if not isinstance(payload, Mapping):
        raise ValueError(f"Fixture {path} must define a JSON object")

    return payload


def _disc_from_payload(payload: Mapping[str, object]) -> DiscInfo:
    from . import DiscInfo, TitleInfo

    label = str(payload.get("label") or "Unknown Disc")
    titles_data = payload.get("titles")

    titles: list[TitleInfo] = []
    for index, title_payload in enumerate(_iter_title_payloads(titles_data), start=1):
        titles.append(_title_from_payload(title_payload, index, TitleInfo))

    return DiscInfo(label=label, titles=tuple(titles))


def _iter_title_payloads(data: object) -> Iterable[Mapping[str, object]]:
    if isinstance(data, Mapping):
        return [data]
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        return [item for item in data if isinstance(item, Mapping)]
    return []


def _title_from_payload(
    payload: Mapping[str, object],
    index: int,
    title_cls: type[TitleInfo],
) -> TitleInfo:
    label_value = payload.get("label")
    if isinstance(label_value, str) and label_value.strip():
        label = label_value.strip()
    else:
        label = f"Title {index:02d}"

    duration = _parse_duration(payload.get("duration"))
    chapters = tuple(
        _parse_duration(item) for item in _iter_chapter_values(payload.get("chapters"))
    )

    return title_cls(label=label, duration=duration, chapters=chapters)


def _iter_chapter_values(data: object) -> Iterable[object]:
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        return list(data)
    return []


def _parse_duration(value: object) -> timedelta:
    if isinstance(value, (int, float)):
        total_seconds = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return timedelta()
        if ":" in text:
            parts = text.split(":")
            try:
                numbers = [float(part) for part in parts]
            except ValueError:
                return timedelta()
            if len(numbers) == 3:
                hours, minutes, seconds = numbers
            elif len(numbers) == 2:
                hours = 0.0
                minutes, seconds = numbers
            elif len(numbers) == 1:
                hours = minutes = 0.0
                seconds = numbers[0]
            else:
                return timedelta()
            total_seconds = hours * 3600 + minutes * 60 + seconds
        else:
            try:
                total_seconds = float(text)
            except ValueError:
                return timedelta()
    else:
        return timedelta()

    total_seconds = max(total_seconds, 0.0)
    seconds_int = int(total_seconds)
    microseconds = int(round((total_seconds - seconds_int) * 1_000_000))
    if microseconds >= 1_000_000:
        seconds_int += 1
        microseconds -= 1_000_000
    return timedelta(seconds=seconds_int, microseconds=microseconds)
