"""Tests for the metadata placeholder interfaces."""

from __future__ import annotations

from datetime import timedelta

from discripper.core import (
    DEFAULT_METADATA_PROVIDER,
    DiscInfo,
    DiscMetadata,
    EpisodeMetadata,
    MetadataLookupResult,
    NullMetadataProvider,
    TitleInfo,
)


def test_disc_metadata_normalizes_episode_iterables() -> None:
    episode = EpisodeMetadata(title="Pilot")
    metadata = DiscMetadata(episodes=[episode])

    assert isinstance(metadata.episodes, tuple)
    assert metadata.episodes == (episode,)


def test_null_metadata_provider_returns_placeholder_message() -> None:
    disc = DiscInfo(label="Sample Disc", titles=(TitleInfo("Title 1", timedelta(minutes=90)),))

    provider: NullMetadataProvider = DEFAULT_METADATA_PROVIDER
    result = provider.lookup_disc(disc)

    assert isinstance(result, MetadataLookupResult)
    assert result.provider == "none"
    assert result.metadata is None
    assert result.message and "not yet implemented" in result.message
    assert not result.found
