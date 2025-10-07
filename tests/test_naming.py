from copy import deepcopy
from datetime import timedelta
from pathlib import Path

from discripper import config as config_module
from discripper.core import (
    DiscInfo,
    TitleInfo,
    TITLE_SOURCE_KEY,
    movie_output_path,
    sanitize_component,
    select_disc_title,
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


def test_sanitize_component_falls_back_when_separator_invalid() -> None:
    sanitized = sanitize_component("Season • Finale", separator="•")
    assert sanitized == "Season_Finale"


def test_movie_output_path_uses_disc_title_slug(tmp_path: Path) -> None:
    title = TitleInfo(label="The Matrix", duration=timedelta(minutes=136))
    config = {
        "output_directory": str(tmp_path / "Movies"),
        "title": "Matrix Reloaded",
    }

    path = movie_output_path(title, config, track_index=2)

    expected = tmp_path / "Movies" / "matrix-reloaded" / "matrix-reloaded_track02.mp4"
    assert path == expected


def test_movie_output_path_defaults_without_naming_section(tmp_path: Path) -> None:
    title = TitleInfo(label="Strange: Name", duration=timedelta(minutes=90))
    config = {"output_directory": tmp_path}

    path = movie_output_path(title, config)

    expected = tmp_path / "strange-name" / "strange-name_track01.mp4"
    assert path == expected


def test_series_output_path_creates_nested_structure(tmp_path: Path) -> None:
    title = TitleInfo(label="The Long Night", duration=timedelta(minutes=52))
    config = {
        "output_directory": tmp_path / "Series",
        "title": "Game of Thrones",
    }

    path = series_output_path("Ignored", title, "s01e03", config, track_index=3)

    expected = tmp_path / "Series" / "game-of-thrones" / "game-of-thrones_track03.mp4"
    assert path == expected


def test_series_output_path_defaults_without_naming_section(tmp_path: Path) -> None:
    title = TitleInfo(label="Episode #2", duration=timedelta(minutes=48))
    config = {"output_directory": tmp_path}

    path = series_output_path("Strange Show", title, "s01e02", config)

    expected = tmp_path / "strange-show" / "strange-show_track01.mp4"
    assert path == expected


def test_movie_output_path_adds_suffix_when_collision(tmp_path: Path) -> None:
    title = TitleInfo(label="The Matrix", duration=timedelta(minutes=136))
    config = {"output_directory": tmp_path}

    first = movie_output_path(title, config)
    expected = tmp_path / "the-matrix" / "the-matrix_track01.mp4"
    assert first == expected

    expected.parent.mkdir(parents=True, exist_ok=True)
    first.touch()

    second = movie_output_path(title, config)
    assert second == tmp_path / "the-matrix" / "the-matrix_track01_1.mp4"

    second.touch()

    third = movie_output_path(title, config)
    assert third == tmp_path / "the-matrix" / "the-matrix_track01_2.mp4"


def test_series_output_path_adds_suffix_when_collision(tmp_path: Path) -> None:
    title = TitleInfo(label="Pilot", duration=timedelta(minutes=42))
    config = {"output_directory": tmp_path}

    first = series_output_path("Example Show", title, "s01e01", config)
    expected = tmp_path / "example-show" / "example-show_track01.mp4"
    assert first == expected

    expected.parent.mkdir(parents=True, exist_ok=True)
    expected.touch()

    second = series_output_path("Example Show", title, "s01e01", config)
    assert second == tmp_path / "example-show" / "example-show_track01_1.mp4"


def test_movie_output_path_honors_custom_patterns(tmp_path: Path) -> None:
    title = TitleInfo(label="The Matrix", duration=timedelta(minutes=136))
    config = deepcopy(config_module.DEFAULT_CONFIG)
    config["output_directory"] = str(tmp_path)
    config["naming"]["disc_directory_pattern"] = "custom/{slug}"
    config["naming"]["track_filename_pattern"] = "{slug}-{index:03d}.{ext}"

    path = movie_output_path(title, config, track_index=5)

    expected = tmp_path / "custom" / "the-matrix" / "the-matrix-005.mp4"
    assert path == expected


def test_select_disc_title_prefers_cli_override() -> None:
    disc = DiscInfo(label="Sample Disc")
    config = {TITLE_SOURCE_KEY: "cli", "title": "  Custom Title  "}

    selected, source = select_disc_title(config, disc)

    assert selected == "Custom Title"
    assert source == "cli"


def test_select_disc_title_uses_config_source_when_missing_marker() -> None:
    disc = DiscInfo(label="Sample Disc")
    config = {"title": " Preconfigured "}

    selected, source = select_disc_title(config, disc)

    assert selected == "Preconfigured"
    assert source == "config"


def test_select_disc_title_falls_back_to_disc_label() -> None:
    disc = DiscInfo(label="  Disc Label  ")
    config: dict[str, object] = {}

    selected, source = select_disc_title(config, disc)

    assert selected == "Disc Label"
    assert source == "disc-label"


def test_select_disc_title_uses_fallback_when_no_label() -> None:
    disc = DiscInfo(label="   ")
    config: dict[str, object] = {}

    selected, source = select_disc_title(config, disc)

    assert selected == "untitled"
    assert source == "fallback"
