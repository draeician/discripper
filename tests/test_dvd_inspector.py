from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest

from discripper.core import ToolAvailability, inspect_dvd


SAMPLE_LSDVD_OUTPUT = """
lsdvd output

***** No VOBU entries found, assuming blank disc *****

disc = {
    'title': 'SERIES_DISC',
    'track_count': 2,
    'track': [
        {
            'ix': 1,
            'length': '00:42:31.000',
            'chapter_count': 2,
            'chapter': [
                {'ix': 1, 'length': '00:10:00.000'},
                {'ix': 2, 'length': '00:32:31.000'},
            ],
        },
        {
            'ix': 2,
            'length': '00:43:00.500',
            'chapter': {'ix': 1, 'length': '00:43:00.500'},
        },
    ],
}
"""


SAMPLE_LSDVD_WRAPPER_OUTPUT = """
lsdvd output

***** No VOBU entries found, assuming blank disc *****

lsdvd = {
    'device': '/dev/sr0',
    'device_title': 'SERIES_DISC',
    'track_count': 2,
    'disc': {
        'title': 'SERIES_DISC',
        'track_count': 2,
        'track': [
            {
                'ix': 1,
                'length': '00:42:31.000',
                'chapter_count': 2,
                'chapter': [
                    {'ix': 1, 'length': '00:10:00.000'},
                    {'ix': 2, 'length': '00:32:31.000'},
                ],
            },
            {
                'ix': 2,
                'length': '00:43:00.500',
                'chapter': {'ix': 1, 'length': '00:43:00.500'},
            },
        ],
    },
}
"""


@pytest.fixture()
def dvd_tool() -> ToolAvailability:
    return ToolAvailability(command="lsdvd", path="/usr/bin/lsdvd")


def test_inspect_dvd_parses_disc_information(dvd_tool: ToolAvailability) -> None:
    calls: list[list[str]] = []

    def fake_runner(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(stdout=SAMPLE_LSDVD_OUTPUT, stderr="")

    disc = inspect_dvd("/dev/sr0", tool=dvd_tool, runner=fake_runner)

    assert calls == [["/usr/bin/lsdvd", "-Oy", "-c", "/dev/sr0"]]
    assert disc.label == "SERIES_DISC"
    assert len(disc.titles) == 2

    first, second = disc.titles
    assert first.label == "Title 01"
    assert first.duration == timedelta(minutes=42, seconds=31)
    assert first.chapters == (timedelta(minutes=10), timedelta(minutes=32, seconds=31))

    assert second.label == "Title 02"
    assert second.duration == timedelta(minutes=43, seconds=0, microseconds=500_000)
    assert second.chapters == (timedelta(minutes=43, seconds=0, microseconds=500_000),)


def test_inspect_dvd_errors_on_unexpected_output(dvd_tool: ToolAvailability) -> None:
    def fake_runner(args, **kwargs):
        return SimpleNamespace(stdout="unexpected", stderr="")

    with pytest.raises(ValueError):
        inspect_dvd("/dev/sr0", tool=dvd_tool, runner=fake_runner)


def test_inspect_dvd_parses_lsdvd_wrapper_payload(
    dvd_tool: ToolAvailability,
) -> None:
    def fake_runner(args, **kwargs):
        return SimpleNamespace(stdout=SAMPLE_LSDVD_WRAPPER_OUTPUT, stderr="")

    disc = inspect_dvd("/dev/sr0", tool=dvd_tool, runner=fake_runner)

    assert disc.label == "SERIES_DISC"
    assert [title.label for title in disc.titles] == ["Title 01", "Title 02"]
