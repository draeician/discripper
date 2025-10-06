"""Placeholder metadata lookup interfaces for future integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from . import DiscInfo


@dataclass(frozen=True, slots=True)
class EpisodeMetadata:
    """Describes metadata for a single episode on a disc."""

    title: str | None = None
    overview: str | None = None
    season: int | None = None
    number: int | None = None


@dataclass(frozen=True, slots=True)
class DiscMetadata:
    """Collection of metadata describing an entire disc."""

    title: str | None = None
    overview: str | None = None
    episodes: tuple[EpisodeMetadata, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - trivial tuple conversion
        object.__setattr__(self, "episodes", tuple(self.episodes))


@dataclass(frozen=True, slots=True)
class MetadataLookupResult:
    """Result produced by a :class:`MetadataProvider`."""

    provider: str
    metadata: DiscMetadata | None
    message: str | None = None

    @property
    def found(self) -> bool:
        """Return :data:`True` when metadata is available."""

        return self.metadata is not None


@runtime_checkable
class MetadataProvider(Protocol):
    """Protocol describing metadata providers such as TheTVDB or TMDB."""

    name: str

    def lookup_disc(self, disc: "DiscInfo") -> MetadataLookupResult:
        """Return metadata for *disc* or a placeholder result."""


@dataclass(frozen=True, slots=True)
class NullMetadataProvider:
    """Fallback provider used until external integrations are implemented."""

    name: str = "none"

    def lookup_disc(self, disc: "DiscInfo") -> MetadataLookupResult:  # pragma: no cover - thin
        return MetadataLookupResult(
            provider=self.name,
            metadata=None,
            message=(
                "Metadata lookup is not yet implemented. "
                "This placeholder avoids blocking rip workflows."
            ),
        )


DEFAULT_METADATA_PROVIDER = NullMetadataProvider()

__all__ = [
    "EpisodeMetadata",
    "DiscMetadata",
    "MetadataLookupResult",
    "MetadataProvider",
    "NullMetadataProvider",
    "DEFAULT_METADATA_PROVIDER",
]
