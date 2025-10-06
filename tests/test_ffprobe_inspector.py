from __future__ import annotations

import json
from datetime import timedelta

import pytest

from discripper.core import DiscInfo, TitleInfo
from discripper.core.discovery import ToolAvailability
from discripper.core.ffprobe import inspect_with_ffprobe


class DummyCompletedProcess:
    def __init__(self, args: list[str], stdout: str) -> None:
        self.args = args
        self.returncode = 0
        self.stdout = stdout


@pytest.fixture()
def ffprobe_tool() -> ToolAvailability:
    return ToolAvailability(command="ffprobe", path="/usr/bin/ffprobe")


def test_inspect_with_ffprobe_parses_title_and_duration(ffprobe_tool: ToolAvailability) -> None:
    payload = {
        "format": {
            "duration": "123.5",
            "tags": {"title": "Sample Disc"},
        }
    }
    ffprobe_output = json.dumps(payload)
    captured_command: list[str] = []

    def runner(command, check, stdout=None, stderr=None, text=None):  # type: ignore[override]
        captured_command.extend(command)
        return DummyCompletedProcess(command, ffprobe_output)

    disc = inspect_with_ffprobe("/dev/sr0", tool=ffprobe_tool, runner=runner)

    expected_command = [
        ffprobe_tool.path,
        "-v",
        "error",
        "-show_entries",
        "format=duration:format_tags=title",
        "-of",
        "json",
        "/dev/sr0",
    ]
    assert captured_command == expected_command

    assert isinstance(disc, DiscInfo)
    assert disc.label == "Sample Disc"
    assert len(disc.titles) == 1
    title = disc.titles[0]
    assert isinstance(title, TitleInfo)
    assert title.label == "Sample Disc"
    assert title.duration == timedelta(seconds=123, microseconds=500000)


def test_inspect_with_ffprobe_handles_missing_fields(ffprobe_tool: ToolAvailability) -> None:
    ffprobe_output = json.dumps({"format": {}})

    def runner(command, check, stdout=None, stderr=None, text=None):  # type: ignore[override]
        return DummyCompletedProcess(command, ffprobe_output)

    disc = inspect_with_ffprobe("/dev/sr0", tool=ffprobe_tool, runner=runner)

    assert disc.label == "Unknown Disc"
    assert len(disc.titles) == 1
    title = disc.titles[0]
    assert title.label == "Title"
    assert title.duration == timedelta(0)


def test_inspect_with_ffprobe_rejects_non_json(ffprobe_tool: ToolAvailability) -> None:
    def runner(command, check, stdout=None, stderr=None, text=None):  # type: ignore[override]
        return DummyCompletedProcess(command, "not-json")

    with pytest.raises(ValueError):
        inspect_with_ffprobe("/dev/sr0", tool=ffprobe_tool, runner=runner)
