"""Tests for the Blu-ray inspection placeholder."""

from __future__ import annotations

import pytest

from discripper.core import BluRayNotSupportedError, ToolAvailability, inspect_blu_ray


def test_inspect_blu_ray_raises_placeholder_error() -> None:
    tool = ToolAvailability(command="makemkvcon", path="/usr/bin/makemkvcon")

    with pytest.raises(BluRayNotSupportedError) as excinfo:
        inspect_blu_ray("/dev/sr0", tool=tool)

    message = str(excinfo.value)
    assert "Blu-ray inspection is not supported yet" in message
    assert "makemkvcon" in message
    assert "/dev/sr0" in message


def test_inspect_blu_ray_handles_missing_tool() -> None:
    with pytest.raises(BluRayNotSupportedError) as excinfo:
        inspect_blu_ray("/dev/sr1", tool=None)

    message = str(excinfo.value)
    assert "no Blu-ray inspection tool detected" in message
    assert "/dev/sr1" in message
