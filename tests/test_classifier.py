from datetime import timedelta

from discripper.core import DiscInfo, TitleInfo, classify_disc


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
