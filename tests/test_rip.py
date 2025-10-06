from __future__ import annotations

from datetime import timedelta
import io
import time
from pathlib import Path
from typing import Callable

import pytest

from subprocess import CompletedProcess

from discripper.core import (
    ClassificationResult,
    RipExecutionError,
    RipPlan,
    TitleInfo,
    rip_disc,
    rip_title,
    run_rip_plan,
)
from discripper.core import rip as rip_module


@pytest.fixture()
def sample_title() -> TitleInfo:
    return TitleInfo(label="Main Feature", duration=timedelta(minutes=95))


class FakePopen:
    def __init__(
        self,
        command: tuple[str, ...],
        *,
        stderr_data: str = "",
        stdout_data: str = "",
        returncode: int = 0,
        finish_delay: float = 0.0,
        on_wait: Callable[[], None] | None = None,
    ) -> None:
        self.args = command
        self.returncode = returncode
        self._stderr = io.StringIO(stderr_data)
        self._stdout = io.StringIO(stdout_data)
        self.stderr = self._stderr
        self.stdout = self._stdout
        self._start = time.monotonic()
        self._finish_delay = finish_delay
        self._on_wait = on_wait

    def poll(self) -> int | None:
        if time.monotonic() - self._start >= self._finish_delay:
            return self.returncode
        return None

    def wait(self, timeout: float | None = None) -> int:
        deadline = None if timeout is None else time.monotonic() + timeout
        while self.poll() is None:
            if deadline is not None and time.monotonic() > deadline:
                raise TimeoutError
            time.sleep(0.01)
        if self._on_wait is not None:
            callback = self._on_wait
            self._on_wait = None
            callback()
        return self.returncode



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
    assert plan.command[:7] == (
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "error",
        "-progress",
        "pipe:2",
    )
    assert "-i" in plan.command
    assert plan.command[-2:] == (plan.device, str(destination))
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

    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        calls.append((command, kwargs))
        return FakePopen(command)

    result = run_rip_plan(plan, popen=fake_popen)

    assert calls
    assert calls[0][0] == plan.command
    assert isinstance(result, CompletedProcess)
    assert result.returncode == 0


def test_run_rip_plan_creates_parent_directories(tmp_path: Path, sample_title: TitleInfo) -> None:
    destination = tmp_path / "sub" / "folder" / "out.mp4"
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        destination,
        which=_ffmpeg_only,
    )

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        assert destination.parent.exists()
        return FakePopen(command)

    result = run_rip_plan(plan, popen=fake_popen)

    assert isinstance(result, CompletedProcess)


def test_run_rip_plan_refuses_to_overwrite_existing_file(
    tmp_path: Path, sample_title: TitleInfo, caplog
) -> None:
    destination = tmp_path / "out.mp4"
    destination.write_bytes(b"existing")
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        destination,
        which=_ffmpeg_only,
    )

    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        calls.append((command, kwargs))
        return FakePopen(command)

    with caplog.at_level("WARNING"):
        with pytest.raises(RipExecutionError, match="Refusing to overwrite existing file"):
            run_rip_plan(plan, popen=fake_popen)

    assert calls == []
    assert any("EVENT=RIP_GUARD" in message for message in caplog.messages)


def test_run_rip_plan_skips_dry_run(
    tmp_path: Path, sample_title: TitleInfo, capsys, caplog
) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        dry_run=True,
        which=_ffmpeg_only,
    )

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        raise AssertionError("popen should not be called for dry-run plans")

    result = run_rip_plan(plan, popen=fake_popen)

    assert result is None

    captured = capsys.readouterr()
    assert "[dry-run] Would execute:" in captured.out
    assert str(plan.destination) in captured.out
    assert any("EVENT=RIP_SKIPPED" in message for message in caplog.messages)


def test_run_rip_plan_logs_success(tmp_path: Path, sample_title: TitleInfo, caplog) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        which=_ffmpeg_only,
    )

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        return FakePopen(
            command,
            on_wait=lambda: plan.destination.write_bytes(b"data"),
        )

    with caplog.at_level("INFO"):
        result = run_rip_plan(plan, popen=fake_popen)

    assert isinstance(result, CompletedProcess)
    assert any("EVENT=RIP_DONE" in message for message in caplog.messages)
    assert any("BYTES=4" in message for message in caplog.messages)


def test_run_rip_plan_maps_called_process_error(
    tmp_path: Path, sample_title: TitleInfo
) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        which=_ffmpeg_only,
    )

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        return FakePopen(command, returncode=3)

    with pytest.raises(RipExecutionError) as excinfo:
        run_rip_plan(plan, popen=fake_popen)

    assert excinfo.value.exit_code == 2
    assert "exit code 3" in str(excinfo.value)


def test_run_rip_plan_maps_os_error(tmp_path: Path, sample_title: TitleInfo) -> None:
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        tmp_path / "out.mp4",
        which=_ffmpeg_only,
    )

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        raise OSError(5, "Input/output error")

    with pytest.raises(RipExecutionError) as excinfo:
        run_rip_plan(plan, popen=fake_popen)

    assert excinfo.value.exit_code == 2
    assert "Input/output error" in str(excinfo.value)


def test_run_rip_plan_reports_ffmpeg_progress(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    title = TitleInfo(label="Short", duration=timedelta(seconds=10))
    plan = rip_title(
        tmp_path / "device.iso",
        title,
        tmp_path / "out.mp4",
        which=_ffmpeg_only,
    )

    stderr_data = "\n".join(
        [
            "frame=1",
            "out_time_ms=1000",
            "total_size=2048",
            "speed=1.0x",
            "progress=continue",
            "junk",
            "out_time_ms=5000",
            "speed=1.5x",
            "total_size=4096",
            "progress=end",
        ]
    )
    stderr_data += "\n"

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        return FakePopen(
            command,
            stderr_data=stderr_data,
            on_wait=lambda: plan.destination.write_bytes(b"done"),
        )

    with caplog.at_level("INFO"):
        run_rip_plan(plan, popen=fake_popen)

    progress_logs = [
        record.message
        for record in caplog.records
        if "EVENT=PROGRESS BACKEND=ffmpeg" in record.message
    ]

    assert progress_logs, "Expected ffmpeg progress logs"
    assert any("PCT=" in message and "PCT=100.0" not in message for message in progress_logs)
    assert any("PCT=100.0" in message for message in progress_logs)


def test_run_rip_plan_reports_dvdbackup_progress(
    tmp_path: Path,
    sample_title: TitleInfo,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "movie.mp4"
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        destination,
        which=lambda cmd: "/usr/bin/dvdbackup" if cmd == "dvdbackup" else None,
    )

    sizes = iter([0, 2048, 4096, 8192])

    monkeypatch.setattr(rip_module, "_probe_dvd_volume_size", lambda device: 8192)
    monkeypatch.setattr(rip_module, "_directory_size", lambda path: next(sizes, 8192))

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        return FakePopen(command, finish_delay=0.05)

    with caplog.at_level("INFO"):
        run_rip_plan(plan, popen=fake_popen)

    progress_logs = [
        record.message
        for record in caplog.records
        if "EVENT=PROGRESS BACKEND=dvdbackup" in record.message
    ]

    assert progress_logs, "Expected dvdbackup progress logs"
    assert any("BYTES_DONE=2048" in message for message in progress_logs)
    assert any("PCT=" in message for message in progress_logs)


def test_run_rip_plan_reports_dvdbackup_spinner_when_unknown_total(
    tmp_path: Path,
    sample_title: TitleInfo,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "movie.mp4"
    plan = rip_title(
        tmp_path / "device.iso",
        sample_title,
        destination,
        which=lambda cmd: "/usr/bin/dvdbackup" if cmd == "dvdbackup" else None,
    )

    sizes = iter([0, 1024, 2048])

    monkeypatch.setattr(rip_module, "_probe_dvd_volume_size", lambda device: None)
    monkeypatch.setattr(rip_module, "_directory_size", lambda path: next(sizes, 2048))

    def fake_popen(command: tuple[str, ...], **kwargs: object) -> FakePopen:
        return FakePopen(command, finish_delay=0.05)

    with caplog.at_level("INFO"):
        run_rip_plan(plan, popen=fake_popen)

    progress_logs = [
        record.message
        for record in caplog.records
        if "EVENT=PROGRESS BACKEND=dvdbackup" in record.message
    ]

    assert progress_logs, "Expected dvdbackup progress logs"
    assert any("SPINNER=true" in message for message in progress_logs)
    assert all(
        "PCT=" not in message for message in progress_logs if "SPINNER=true" in message
    )
