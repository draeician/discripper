from __future__ import annotations

from pathlib import Path

from discripper.config import DEFAULT_CONFIG
from discripper.core.classifier import classify_disc, thresholds_from_config
from discripper.core.fake import inspect_from_fixture
from discripper.core.naming import movie_output_path, series_output_path


def _simulation_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "samples" / f"{name}.json"


def test_simulated_movie_output_matches_prd_pattern(tmp_path: Path) -> None:
    config = DEFAULT_CONFIG.copy()
    output_dir = tmp_path / "Videos"
    config["output_directory"] = str(output_dir)

    disc = inspect_from_fixture(_simulation_fixture("simulated_movie"))
    classification = classify_disc(disc, thresholds=thresholds_from_config(config))

    assert classification.disc_type == "movie"

    movie_plan = movie_output_path(classification.episodes[0], config)
    assert movie_plan == output_dir / "Main_Feature.mp4"


def test_simulated_series_output_matches_prd_pattern(tmp_path: Path) -> None:
    config = DEFAULT_CONFIG.copy()
    output_dir = tmp_path / "Videos"
    config["output_directory"] = str(output_dir)

    disc = inspect_from_fixture(_simulation_fixture("simulated_series"))
    classification = classify_disc(disc, thresholds=thresholds_from_config(config))

    assert classification.disc_type == "series"
    assert classification.episode_codes is not None

    destinations = [
        series_output_path(disc.label, title, code, config)
        for title, code in zip(classification.episodes, classification.episode_codes)
    ]

    expected_dir = output_dir / "Simulation_Limited_Series"
    assert destinations == [
        expected_dir / "Simulation_Limited_Series-s01e01_Episode_3.mp4",
        expected_dir / "Simulation_Limited_Series-s01e02_Episode_1.mp4",
        expected_dir / "Simulation_Limited_Series-s01e03_Episode_2.mp4",
        expected_dir / "Simulation_Limited_Series-s01e04_Episode_4.mp4",
    ]
