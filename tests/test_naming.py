from datetime import timedelta
from pathlib import Path

from discripper.core import (
    TitleInfo,
    movie_output_path,
    sanitize_component,
    series_output_path,
)


def custom_episode_title_strategy(title: TitleInfo, episode_code: str | None) -> str:
    return f"Custom {title.label}"


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


def test_sanitize_component_falls_back_when_separator_invalid() -> None:
    sanitized = sanitize_component("Season • Finale", separator="•")
    assert sanitized == "Season_Finale"


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


def test_series_output_path_applies_lowercase_and_sanitization(tmp_path: Path) -> None:
    title = TitleInfo(label="Épisode Finale!", duration=timedelta(minutes=58))
    config = {
        "output_directory": tmp_path,
        "naming": {"separator": "-", "lowercase": True},
    }

    path = series_output_path("Série Étrange?!", title, "s02e10", config)

    expected = (
        tmp_path
        / "serie-etrange"
        / "serie-etrange-s02e10_episode-finale.mp4"
    )
    assert path == expected


def test_movie_output_path_adds_suffix_when_collision(tmp_path: Path) -> None:
    title = TitleInfo(label="The Matrix", duration=timedelta(minutes=136))
    config = {"output_directory": tmp_path}

    first = movie_output_path(title, config)
    assert first == tmp_path / "The_Matrix.mp4"

    first.touch()

    second = movie_output_path(title, config)
    assert second == tmp_path / "The_Matrix_1.mp4"

    second.touch()

    third = movie_output_path(title, config)
    assert third == tmp_path / "The_Matrix_2.mp4"


def test_series_output_path_adds_suffix_when_collision(tmp_path: Path) -> None:
    title = TitleInfo(label="Pilot", duration=timedelta(minutes=42))
    config = {"output_directory": tmp_path}

    first = series_output_path("Example Show", title, "s01e01", config)
    expected = tmp_path / "Example_Show" / "Example_Show-s01e01_Pilot.mp4"
    assert first == expected

    expected.parent.mkdir(parents=True, exist_ok=True)
    expected.touch()

    second = series_output_path("Example Show", title, "s01e01", config)
    assert second == tmp_path / "Example_Show" / "Example_Show-s01e01_Pilot_1.mp4"


def test_series_output_path_uses_episode_number_strategy(tmp_path: Path) -> None:
    title = TitleInfo(label="Episode 1", duration=timedelta(minutes=44))
    config = {
        "output_directory": tmp_path,
        "naming": {"episode_title_strategy": "episode-number"},
    }

    path = series_output_path("Example Show", title, "s01e05", config)

    assert path == tmp_path / "Example_Show" / "Example_Show-s01e05_Episode_05.mp4"


def test_series_output_path_supports_custom_strategy(tmp_path: Path) -> None:
    title = TitleInfo(label="Pilot", duration=timedelta(minutes=45))
    config = {
        "output_directory": tmp_path,
        "naming": {
            "episode_title_strategy": "test_naming:custom_episode_title_strategy",
        },
    }

    path = series_output_path("Example Show", title, "s01e01", config)

    expected = tmp_path / "Example_Show" / "Example_Show-s01e01_Custom_Pilot.mp4"
    assert path == expected
