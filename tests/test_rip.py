from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from discripper.core import RipPlan, TitleInfo, rip_title


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
