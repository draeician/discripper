"""Smoke tests for the discripper package."""

import discripper
from discripper import cli


def test_version_is_string() -> None:
    """The package exposes a version string."""

    assert isinstance(discripper.__version__, str)
    assert discripper.__version__ != ""


def test_cli_main_prints_placeholder(capsys) -> None:
    """The CLI main function prints the placeholder usage text."""

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Usage: discripper" in captured.out
