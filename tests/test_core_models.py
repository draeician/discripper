from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from discripper.core import DiscInfo, TitleInfo


def test_title_info_is_frozen_and_normalizes_chapters() -> None:
    chapters = [timedelta(minutes=5), timedelta(minutes=10)]
    info = TitleInfo(label="Title 1", duration=timedelta(minutes=42), chapters=chapters)

    assert info.label == "Title 1"
    assert info.duration == timedelta(minutes=42)
    assert info.chapters == (timedelta(minutes=5), timedelta(minutes=10))

    with pytest.raises(FrozenInstanceError):
        info.label = "Another"


def test_disc_info_collects_titles() -> None:
    title = TitleInfo(
        label="Pilot",
        duration=timedelta(minutes=45),
        chapters=(timedelta(minutes=20), timedelta(minutes=25)),
    )
    disc = DiscInfo(label="Series Disc", titles=[title])

    assert disc.label == "Series Disc"
    assert disc.titles == (title,)

    with pytest.raises(FrozenInstanceError):
        disc.titles = ()
