from datetime import timedelta
from pathlib import Path

from discripper.core import (
    TitleInfo,
    movie_output_path,
    sanitize_component,
    series_output_path,
)


def test_sanitize_component_replaces_unsafe_characters() -> None:
    sanitized = sanitize_component("Firefly: Serenity/Part 1")
    assert sanitized == "Firefly_Serenity_Part_1"


def test_sanitize_component_strips_diacritics() -> None:
    sanitized = sanitize_component("Café del Mar")
    assert sanitized == "Cafe_del_Mar"


def test_sanitize_component_honors_custom_separator() -> None:
    sanitized = sanitize_component("Episode 01", separator="-")
    assert sanitized == "Episode-01"


def test_sanitize_component_collapses_repeated_separators() -> None:
    sanitized = sanitize_component("  --  odd***name  ")
    assert sanitized == "odd_name"


def test_sanitize_component_returns_fallback_when_empty() -> None:
    sanitized = sanitize_component("@@@@")
    assert sanitized == "untitled"


def test_sanitize_component_applies_lowercase_when_requested() -> None:
    sanitized = sanitize_component("Firefly: Serenity", lowercase=True)
    assert sanitized == "firefly_serenity"


def test_movie_output_path_uses_configured_directory(tmp_path: Path) -> None:
    title = TitleInfo(label="The Matrix", duration=timedelta(minutes=136))
    config = {
        "output_directory": str(tmp_path / "Movies"),
        "naming": {"separator": "-", "lowercase": True},
    }

    path = movie_output_path(title, config)

    assert path == tmp_path / "Movies" / "the-matrix.mp4"


def test_movie_output_path_defaults_without_naming_section(tmp_path: Path) -> None:
    title = TitleInfo(label="Strange: Name", duration=timedelta(minutes=90))
    config = {"output_directory": tmp_path}

    path = movie_output_path(title, config)

    assert path.name == "Strange_Name.mp4"


def test_series_output_path_creates_nested_structure(tmp_path: Path) -> None:
    title = TitleInfo(label="The Long Night", duration=timedelta(minutes=52))
    config = {
        "output_directory": tmp_path / "Series",
        "naming": {"separator": "-", "lowercase": True},
    }

    path = series_output_path("Game of Thrones", title, "s01e03", config)

    expected = (
        tmp_path
        / "Series"
        / "game-of-thrones"
        / "game-of-thrones-s01e03_the-long-night.mp4"
    )
    assert path == expected


def test_series_output_path_defaults_without_naming_section(tmp_path: Path) -> None:
    title = TitleInfo(label="Episode #2", duration=timedelta(minutes=48))
    config = {"output_directory": tmp_path}

    path = series_output_path("Strange Show", title, "s01e02", config)

    assert path == tmp_path / "Strange_Show" / "Strange_Show-s01e02_Episode_2.mp4"
