"""Smoke tests for the discripper package."""

from importlib import metadata
from pathlib import Path
import sys

import discripper
from discripper import cli
from discripper import core


def test_version_is_string() -> None:
    """The package exposes a version string."""

    assert isinstance(discripper.__version__, str)
    assert discripper.__version__ != ""


def test_cli_main_errors_without_inspection_tools(tmp_path, monkeypatch, capsys) -> None:
    """The CLI reports a helpful error when no inspection tools are available."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    monkeypatch.setattr(
        cli,
        "discover_inspection_tools",
        lambda: core.InspectionTools(dvd=None, fallback=None, blu_ray=None),
    )

    exit_code = cli.main([str(device)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "No supported inspection tools" in captured.err


def test_core_version_is_exposed() -> None:
    """The core package exposes a placeholder version string."""

    assert isinstance(core.__version__, str)
    assert core.__version__ != ""


def test_pytest_pythonpath_includes_src() -> None:
    """Pytest configuration ensures the source directory is importable."""

    repo_root = Path(__file__).resolve().parents[1]
    expected_src = repo_root / "src"

    assert expected_src.exists()
    assert any(Path(path).resolve() == expected_src for path in map(Path, sys.path))


def test_console_script_entry_point_registered() -> None:
    """The console script entry point resolves to the CLI main function."""

    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        console_scripts = entry_points.select(group="console_scripts")
    else:  # pragma: no cover - fallback for older importlib.metadata APIs
        console_scripts = entry_points.get("console_scripts", [])

    discripper_entry = next((ep for ep in console_scripts if ep.name == "discripper"), None)

    assert discripper_entry is not None
    assert discripper_entry.value == "discripper.cli:main"
    assert discripper_entry.load() is cli.main
