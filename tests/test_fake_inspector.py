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


def test_inspect_from_fixture_loads_single_movie_fixture() -> None:
    disc = inspect_from_fixture("single_movie_disc")

    assert disc.label == "Single Movie Feature"
    assert len(disc.titles) == 3

    main_feature, deleted_scenes, trailer = disc.titles

    assert main_feature.label == "Main Feature"
    assert main_feature.duration == timedelta(hours=1, minutes=52, seconds=30)
    assert main_feature.chapters == (
        timedelta(minutes=25),
        timedelta(minutes=23, seconds=30),
        timedelta(minutes=24, seconds=15),
        timedelta(minutes=39, seconds=45),
    )

    assert deleted_scenes.label == "Deleted Scenes"
    assert deleted_scenes.duration == timedelta(minutes=15)
    assert deleted_scenes.chapters == (
        timedelta(minutes=5),
        timedelta(minutes=5),
        timedelta(minutes=5),
    )

    assert trailer.label == "Theatrical Trailer"
    assert trailer.duration == timedelta(minutes=2, seconds=30)
    assert trailer.chapters == ()


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


def test_simulation_samples_are_available() -> None:
    samples_dir = Path(__file__).resolve().parents[1] / "samples"

    movie_disc = inspect_from_fixture("simulated_movie", fixture_dir=samples_dir)
    assert movie_disc.label == "Simulation: Feature Film"
    assert len(movie_disc.titles) == 2
    assert movie_disc.titles[0].label == "Main Feature"

    series_disc = inspect_from_fixture("simulated_series", fixture_dir=samples_dir)
    assert series_disc.label == "Simulation: Limited Series"
    assert len(series_disc.titles) == 4
    assert series_disc.titles[0].label == "Episode 1"
