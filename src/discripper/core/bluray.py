"""Blu-ray inspection placeholder implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

from .discovery import ToolAvailability

__all__ = ["BluRayNotSupportedError", "inspect_blu_ray"]

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from subprocess import CompletedProcess

    from . import DiscInfo

Runner = Callable[..., "CompletedProcess[str]"]


class BluRayNotSupportedError(RuntimeError):
    """Error raised when Blu-ray inspection is requested."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:  # pragma: no cover - trivial formatting
        return self.message


def _describe_tool(tool: Optional[ToolAvailability]) -> str:
    if tool is None:
        return "no Blu-ray inspection tool detected"

    return f"detected {tool.command!r} at {tool.path!r}"


def inspect_blu_ray(
    device: str,
    *,
    tool: Optional[ToolAvailability],
    runner: Optional[Runner] = None,
) -> "DiscInfo":
    """Placeholder Blu-ray inspector that raises a user-friendly error."""

    description = _describe_tool(tool)
    raise BluRayNotSupportedError(
        message=(
            "Blu-ray inspection is not supported yet in discripper; "
            f"{description}. Requested device: {device!r}."
        )
    )
