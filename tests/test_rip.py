from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from discripper.core import (
    ClassificationResult,
    RipPlan,
    TitleInfo,
    rip_disc,
    rip_title,
)


@pytest.fixture()
def sample_title() -> TitleInfo:
    return TitleInfo(label="Main Feature", duration=timedelta(minutes=95))


def test_rip_title_builds_ffmpeg_plan(tmp_path: Path, sample_title: TitleInfo) -> None:
    destination = tmp_path / "output.mp4"

    plan = rip_title("/dev/sr0", sample_title, destination)

    assert isinstance(plan, RipPlan)
    assert plan.title is sample_title
    assert plan.destination == destination
    assert plan.device == "/dev/sr0"
    assert plan.command[:5] == ("ffmpeg", "-hide_banner", "-loglevel", "error", "-i")
    assert plan.command[-1] == str(destination)
    assert plan.will_execute is True


def test_rip_title_honors_dry_run_flag(tmp_path: Path, sample_title: TitleInfo) -> None:
    plan = rip_title(tmp_path / "device.iso", sample_title, tmp_path / "out.mp4", dry_run=True)

    assert plan.will_execute is False
    assert plan.device == str(tmp_path / "device.iso")


def test_rip_disc_movie_invokes_destination_factory(
    tmp_path: Path, sample_title: TitleInfo
) -> None:
    classification = ClassificationResult("movie", (sample_title,))
    destinations: list[Path] = []

    def destination_factory(title: TitleInfo, code: str | None) -> Path:
        assert code is None
        assert title is sample_title
        path = tmp_path / f"{title.label}.mp4"
        destinations.append(path)
        return path

    plans = rip_disc("/dev/sr0", classification, destination_factory)

    assert len(plans) == 1
    assert plans[0].destination == destinations[0]
    assert plans[0].command[-1] == str(destinations[0])


def test_rip_disc_series_uses_episode_codes(tmp_path: Path) -> None:
    title_one = TitleInfo(label="Pilot", duration=timedelta(minutes=45))
    title_two = TitleInfo(label="Episode Two", duration=timedelta(minutes=44))
    classification = ClassificationResult(
        "series", (title_one, title_two), ("s01e01", "s01e02")
    )

    def destination_factory(title: TitleInfo, code: str | None) -> Path:
        assert code is not None
        return tmp_path / f"{code}_{title.label}.mp4"

    plans = rip_disc("/dev/sr0", classification, destination_factory, dry_run=True)

    assert len(plans) == 2
    assert [plan.destination.name for plan in plans] == [
        "s01e01_Pilot.mp4",
        "s01e02_Episode Two.mp4",
    ]
    assert all(plan.will_execute is False for plan in plans)
