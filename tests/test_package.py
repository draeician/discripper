"""Smoke tests for the discripper package."""

import discripper


def test_version_is_string() -> None:
    """The package exposes a version string."""

    assert isinstance(discripper.__version__, str)
    assert discripper.__version__ != ""
