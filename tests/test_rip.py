from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from subprocess import CalledProcessError, CompletedProcess

from discripper.core import (
    ClassificationResult,
    RipExecutionError,
    RipPlan,
    TitleInfo,
    rip_disc,
    rip_title,
    run_rip_plan,
)


@pytest.fixture()
def sample_title() -> TitleInfo:
    return TitleInfo(label="Main Feature", duration=timedelta(minutes=95))


def _ffmpeg_only(cmd: str) -> str | None:
    if cmd == "ffmpeg":
        return "/usr/bin/ffmpeg"
    return None


def test_rip_title_builds_ffmpeg_plan(tmp_path: Path, sample_title: TitleInfo) -> None:
    destination = tmp_path / "output.mp4"

    plan = rip_title("/dev/sr0", sample_title, destination, which=_ffmpeg_only)

    assert isinstance(plan, RipPlan)
    assert plan.title is sample_title
    assert plan.destination == destination
    assert plan.device == "/dev/sr0"
    assert plan.command[:5] == ("ffmpeg", "-hide_banner", "-loglevel", "error", "-i")
    assert plan.command[-1] == str(destination)
    assert plan.will_execute is True


def test_rip_title_honors_dry_run_flag(tmp_path: Path, sample_title: TitleInfo) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        dry_run=True,
        which=_ffmpeg_only,
    )

    assert plan.will_execute is False
    assert plan.device == str(tmp_path / "device.iso")


def test_rip_title_prefers_dvdbackup_when_available(
    tmp_path: Path, sample_title: TitleInfo
) -> None:
    destination = tmp_path / "movie.mp4"

    def fake_which(command: str) -> str | None:
        if command == "dvdbackup":
            return "/usr/bin/dvdbackup"
        if command == "ffmpeg":
            return "/usr/bin/ffmpeg"
        return None

    plan = rip_title("/dev/sr0", sample_title, destination, which=fake_which)

    assert plan.command[0] == "dvdbackup"
    assert "-i" in plan.command
    assert plan.destination == destination


def test_rip_title_errors_without_known_tools(tmp_path: Path, sample_title: TitleInfo) -> None:
    def fake_which(command: str) -> None:
        return None

    with pytest.raises(RuntimeError, match="No supported ripping tools"):
        rip_title("/dev/sr0", sample_title, tmp_path / "out.mp4", which=fake_which)


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

    plans = rip_disc(
        "/dev/sr0",
        classification,
        destination_factory,
        which=_ffmpeg_only,
    )

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

    plans = rip_disc(
        "/dev/sr0",
        classification,
        destination_factory,
        dry_run=True,
        which=_ffmpeg_only,
    )

    assert len(plans) == 2
    assert [plan.destination.name for plan in plans] == [
        "s01e01_Pilot.mp4",
        "s01e02_Episode Two.mp4",
    ]
    assert all(plan.will_execute is False for plan in plans)


def test_run_rip_plan_invokes_subprocess(tmp_path: Path, sample_title: TitleInfo) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        which=_ffmpeg_only,
    )

    calls: list[tuple[tuple[str, ...], bool]] = []

    def fake_run(command: tuple[str, ...], check: bool) -> CompletedProcess[str]:
        calls.append((command, check))
        return CompletedProcess(command, 0)

    result = run_rip_plan(plan, run=fake_run)

    assert calls == [(plan.command, True)]
    assert isinstance(result, CompletedProcess)
    assert result.returncode == 0


def test_run_rip_plan_skips_dry_run(tmp_path: Path, sample_title: TitleInfo) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        dry_run=True,
        which=_ffmpeg_only,
    )

    def fake_run(command: tuple[str, ...], check: bool) -> CompletedProcess[str]:
        raise AssertionError("run should not be called for dry-run plans")

    result = run_rip_plan(plan, run=fake_run)

    assert result is None


def test_run_rip_plan_maps_called_process_error(
    tmp_path: Path, sample_title: TitleInfo
) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        which=_ffmpeg_only,
    )

    def fake_run(command: tuple[str, ...], check: bool) -> CompletedProcess[str]:
        raise CalledProcessError(3, command)

    with pytest.raises(RipExecutionError) as excinfo:
        run_rip_plan(plan, run=fake_run)

    assert excinfo.value.exit_code == 2
    assert "exit code 3" in str(excinfo.value)


def test_run_rip_plan_maps_os_error(tmp_path: Path, sample_title: TitleInfo) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        which=_ffmpeg_only,
    )

    def fake_run(command: tuple[str, ...], check: bool) -> CompletedProcess[str]:
        raise OSError(5, "Input/output error")

    with pytest.raises(RipExecutionError) as excinfo:
        run_rip_plan(plan, run=fake_run)

    assert excinfo.value.exit_code == 2
    assert "Input/output error" in str(excinfo.value)
