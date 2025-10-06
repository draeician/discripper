import logging
from datetime import timedelta

import pytest

from discripper.core import (
    DiscInfo,
    TitleInfo,
    classify_disc,
    inspect_from_fixture,
    thresholds_from_config,
)


def test_classify_disc_movie_fixture_selects_longest_title():
    disc = inspect_from_fixture("sample_disc")

    result = classify_disc(disc)

    assert result.disc_type == "movie"
    assert result.episodes == (disc.titles[0],)
    assert result.episode_codes == ()
    assert result.numbered_episodes == ()


def test_classify_disc_movie_selects_longest_title():
    long_feature = TitleInfo(label="Main Feature", duration=timedelta(minutes=110))
    extras = (
        TitleInfo(label="Trailer", duration=timedelta(minutes=5)),
        TitleInfo(label="Deleted Scenes", duration=timedelta(minutes=8)),
    )
    disc = DiscInfo(label="Sample Movie", titles=(long_feature, *extras))

    result = classify_disc(disc)

    assert result.disc_type == "movie"
    assert result.episodes == (long_feature,)
    assert result.episode_codes == ()
    assert result.numbered_episodes == ()


def test_classify_disc_series_detects_similar_episodes():
    episode_titles = (
        TitleInfo(label="Ep1", duration=timedelta(minutes=25)),
        TitleInfo(label="Ep2", duration=timedelta(minutes=24)),
        TitleInfo(label="Ep3", duration=timedelta(minutes=26)),
        TitleInfo(label="Bonus", duration=timedelta(minutes=70)),
    )
    disc = DiscInfo(label="Sample Series", titles=episode_titles)

    result = classify_disc(disc)

    assert result.disc_type == "series"
    assert result.episodes == (
        episode_titles[1],
        episode_titles[0],
        episode_titles[2],
    )
    assert result.episode_codes == ("s01e01", "s01e02", "s01e03")
    assert result.numbered_episodes == (
        ("s01e01", episode_titles[1]),
        ("s01e02", episode_titles[0]),
        ("s01e03", episode_titles[2]),
    )


def test_classify_disc_series_from_fixture_detects_all_six_episodes():
    disc = inspect_from_fixture("six_episode_series")

    result = classify_disc(disc)

    assert result.disc_type == "series"
    assert len(result.episodes) == 6
    assert all(title.label.startswith("Episode ") for title in result.episodes)
    assert result.episode_codes == (
        "s01e01",
        "s01e02",
        "s01e03",
        "s01e04",
        "s01e05",
        "s01e06",
    )
    assert result.numbered_episodes == tuple(zip(result.episode_codes, result.episodes))


def test_classify_disc_threshold_overrides_from_config():
    episode_titles = (
        TitleInfo(label="Ep1", duration=timedelta(minutes=25)),
        TitleInfo(label="Ep2", duration=timedelta(minutes=24)),
        TitleInfo(label="Ep3", duration=timedelta(minutes=26)),
    )
    disc = DiscInfo(label="Sample Series", titles=episode_titles)

    thresholds = thresholds_from_config(
        {"classification": {"series_min_duration_minutes": 30}}
    )
    result = classify_disc(disc, thresholds=thresholds)

    assert result.disc_type == "movie"
    assert result.episodes == (episode_titles[2],)
    assert result.episode_codes == ()


def test_classify_disc_logs_warning_on_ambiguous_disc(caplog):
    ambiguous_titles = (
        TitleInfo(label="Feature", duration=timedelta(minutes=50)),
        TitleInfo(label="Bonus", duration=timedelta(minutes=10)),
        TitleInfo(label="Trailer", duration=timedelta(minutes=5)),
    )
    disc = DiscInfo(label="Ambiguous Disc", titles=ambiguous_titles)

    with caplog.at_level(logging.WARNING):
        result = classify_disc(disc)

    assert result.disc_type == "movie"
    assert result.episodes == (ambiguous_titles[0],)

    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert warnings, "Expected a warning when falling back to movie classification"
    assert "Ambiguous disc structure" in warnings[0].message


def test_classify_disc_ambiguous_fixture_defaults_to_movie():
    disc = inspect_from_fixture("ambiguous_disc")

    result = classify_disc(disc)

    assert result.disc_type == "movie"
    assert result.episodes == (disc.titles[0],)
    assert result.episode_codes == ()


@pytest.mark.parametrize(
    ("fixture_name", "expected_type", "expected_labels", "expected_codes"),
    [
        ("sample_disc", "movie", ["Pilot"], ()),
        ("single_movie_disc", "movie", ["Main Feature"], ()),
        (
            "six_episode_series",
            "series",
            [
                "Episode 1 - The Arrival",
                "Episode 3 - Power Surge",
                "Episode 5 - Shadow Run",
                "Episode 2 - Hidden Signals",
                "Episode 6 - Last Light",
                "Episode 4 - Broken Trust",
            ],
            (
                "s01e01",
                "s01e02",
                "s01e03",
                "s01e04",
                "s01e05",
                "s01e06",
            ),
        ),
        ("ambiguous_disc", "movie", ["Borderline Feature"], ()),
    ],
)
def test_fixture_classifications_are_deterministic(
    fixture_name: str,
    expected_type: str,
    expected_labels: list[str],
    expected_codes: tuple[str, ...],
) -> None:
    disc = inspect_from_fixture(fixture_name)

    result = classify_disc(disc)

    labels = [title.label for title in result.episodes]

    assert result.disc_type == expected_type
    assert labels == expected_labels
    assert result.episode_codes == expected_codes
    assert result.numbered_episodes == tuple(zip(expected_codes, result.episodes))
