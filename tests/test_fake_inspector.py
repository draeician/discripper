from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from discripper.core.fake import inspect_from_fixture


def test_inspect_from_fixture_loads_sample_fixture() -> None:
    disc = inspect_from_fixture("sample_disc")

    assert disc.label == "Sample Disc"
    assert len(disc.titles) == 2

    first, second = disc.titles

    assert first.label == "Pilot"
    assert first.duration == timedelta(hours=1, minutes=30)
    assert first.chapters == (
        timedelta(minutes=30),
        timedelta(minutes=30),
        timedelta(minutes=30),
    )

    assert second.label == "Title 02"
    assert second.duration == timedelta(minutes=45)
    assert second.chapters == (
        timedelta(minutes=15),
        timedelta(minutes=15),
        timedelta(minutes=15),
    )


def test_inspect_from_fixture_accepts_custom_directory(tmp_path: Path) -> None:
    fixture_path = tmp_path / "custom.json"
    fixture_path.write_text(
        json.dumps(
            {
                "label": "Temp Disc",
                "titles": [
                    {
                        "label": "Only Title",
                        "duration": 600,
                        "chapters": [200, 200, 200],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    disc = inspect_from_fixture("custom", fixture_dir=tmp_path)

    assert disc.label == "Temp Disc"
    assert len(disc.titles) == 1
    title = disc.titles[0]
    assert title.label == "Only Title"
    assert title.duration == timedelta(minutes=10)
    assert title.chapters == (
        timedelta(minutes=3, seconds=20),
        timedelta(minutes=3, seconds=20),
        timedelta(minutes=3, seconds=20),
    )
