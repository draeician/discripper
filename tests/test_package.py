"""Smoke tests for the discripper package."""

from pathlib import Path
import sys

import discripper
from discripper import cli
from discripper import core


def test_version_is_string() -> None:
    """The package exposes a version string."""

    assert isinstance(discripper.__version__, str)
    assert discripper.__version__ != ""


def test_cli_main_prints_placeholder(tmp_path, capsys) -> None:
    """The CLI main function prints the placeholder usage text."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    exit_code = cli.main([str(device)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Usage: discripper" in captured.out


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
