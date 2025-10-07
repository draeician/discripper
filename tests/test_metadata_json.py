"""Tests for metadata JSON export helpers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from subprocess import CompletedProcess

from discripper.core import ClassificationResult, DiscInfo, RipPlan, TitleInfo
from discripper.core.metadata_json import build_metadata_document, write_metadata_document


def _fake_version_runner(command: tuple[str, ...], **_kwargs) -> CompletedProcess[str]:
    tool = command[0]
    return CompletedProcess(command, 0, stdout=f"{tool} version test\n", stderr="")


def test_build_metadata_document_includes_streams(tmp_path: Path) -> None:
    title = TitleInfo(label="Main Feature", duration=timedelta(minutes=95))
    disc = DiscInfo(label="Sample Disc", titles=(title,))
    classification = ClassificationResult("movie", (title,))

    destination = tmp_path / "the-matrix" / "the-matrix_track01.mp4"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"example")

    plan = RipPlan(
        device="/dev/sr0",
        title=title,
        destination=destination,
        command=("ffmpeg", "-i", "/dev/sr0", str(destination)),
        will_execute=True,
    )

    ffprobe_payload = {
        "format": {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "duration": "5400.5",
            "bit_rate": "1500000",
        },
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "h264",
                "bit_rate": "1200000",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "30000/1001",
                "pix_fmt": "yuv420p",
                "tags": {"language": "eng"},
            },
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "aac",
                "bit_rate": "192000",
                "channels": 2,
                "channel_layout": "stereo",
                "sample_rate": "48000",
                "tags": {"language": "eng"},
            },
        ],
    }

    def fake_ffprobe_runner(command: tuple[str, ...], **_kwargs) -> CompletedProcess[str]:
        assert command[0] == "ffprobe"
        return CompletedProcess(command, 0, stdout=json.dumps(ffprobe_payload), stderr="")

    document = build_metadata_document(
        disc,
        classification,
        (plan,),
        config={"title": "The Matrix"},
        which=lambda name: name,
        ffprobe_runner=fake_ffprobe_runner,
        version_runner=_fake_version_runner,
        now=lambda: datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    assert document["disc"] == {"label": "Sample Disc", "id": None}
    assert document["title"] == "The Matrix"
    assert document["classification"]["type"] == "movie"
    assert document["tracks"][0]["output"]["path"] == str(destination)
    assert document["tracks"][0]["output"]["size_bytes"] == destination.stat().st_size
    assert document["tracks"][0]["format"]["container"] == "mov,mp4,m4a,3gp,3g2,mj2"
    video_stream = next(
        stream for stream in document["tracks"][0]["streams"] if stream["type"] == "video"
    )
    assert video_stream["codec"] == "h264"
    assert document["tools"]["ffmpeg"].startswith("ffmpeg version test")
    assert document["tools"]["ffprobe"].startswith("ffprobe version test")


def test_build_metadata_document_without_ffprobe(tmp_path: Path) -> None:
    title = TitleInfo(label="Episode", duration=timedelta(minutes=42))
    disc = DiscInfo(label="Series Disc", titles=(title,))
    classification = ClassificationResult("series", (title,), ("s01e01",))

    destination = tmp_path / "series" / "series_track01.mp4"
    plan = RipPlan(
        device="/dev/sr0",
        title=title,
        destination=destination,
        command=("ffmpeg", "-i", "/dev/sr0", str(destination)),
        will_execute=True,
    )

    document = build_metadata_document(
        disc,
        classification,
        (plan,),
        config={},
        which=lambda _name: None,
        ffprobe_runner=_fake_version_runner,
        version_runner=_fake_version_runner,
        now=lambda: datetime(2024, 6, 1, tzinfo=timezone.utc),
    )

    track = document["tracks"][0]
    assert track["streams"] == []
    assert track["output"]["exists"] is False
    assert document["tools"]["ffmpeg"].startswith("ffmpeg version test")


def test_write_metadata_document_persists_json(tmp_path: Path) -> None:
    document = {
        "generated_at": datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
        "disc": {"label": "Sample", "id": None},
        "classification": {"type": "movie", "episode_count": 1},
        "title": "Sample",
        "output_root": str(tmp_path),
        "tools": {},
        "tracks": [],
    }

    path = write_metadata_document(document, tmp_path)

    assert path.name == "metadata.json"
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == document


def test_build_metadata_document_handles_missing_metadata(tmp_path: Path) -> None:
    title = TitleInfo(
        label="Feature",
        duration=timedelta(minutes=90),
        chapters=(timedelta(minutes=5),),
    )
    disc = DiscInfo(label="Sparse Disc", titles=(title,))
    classification = ClassificationResult("movie", (title,))

    destination = tmp_path / "slug" / "slug_track01.mp4"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"data")

    plan = RipPlan(
        device="/dev/sr0",
        title=title,
        destination=destination,
        command=("ffmpeg", "-i", "/dev/sr0", str(destination)),
        will_execute=True,
    )

    def incomplete_ffprobe(command: tuple[str, ...], **_kwargs) -> CompletedProcess[str]:
        assert command[0] == "ffprobe"
        payload = {"streams": [{"codec_type": "audio"}]}
        return CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")

    document = build_metadata_document(
        disc,
        classification,
        (plan,),
        config={},
        which=lambda name: "ffprobe" if name == "ffprobe" else None,
        ffprobe_runner=incomplete_ffprobe,
        version_runner=_fake_version_runner,
        now=lambda: datetime(2024, 7, 1, tzinfo=timezone.utc),
    )

    track = document["tracks"][0]
    assert track["format"] == {}
    assert track["streams"] == [
        {
            "type": "audio",
            "index": None,
            "codec": None,
            "codec_long": None,
            "bit_rate": None,
            "language": None,
            "channels": None,
            "channel_layout": None,
            "sample_rate": None,
        }
    ]
    assert track["output"]["exists"] is True


def test_write_metadata_document_creates_parent_directories(tmp_path: Path) -> None:
    document = {
        "generated_at": datetime(2024, 8, 1, tzinfo=timezone.utc).isoformat(),
        "disc": {"label": "Sample", "id": None},
        "classification": {"type": "movie", "episode_count": 0},
        "title": None,
        "output_root": None,
        "tools": {},
        "tracks": [],
    }

    target_dir = tmp_path / "nested" / "metadata"

    path = write_metadata_document(document, target_dir)

    assert path.exists()
    assert path.parent == target_dir
