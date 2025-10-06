"""Disc classification heuristics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Literal, Sequence, Tuple

if TYPE_CHECKING:  # pragma: no cover - for typing only
    from . import DiscInfo, TitleInfo

DiscType = Literal["movie", "series"]


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """Result of classifying a disc into movie or series content."""

    disc_type: DiscType
    episodes: Tuple[TitleInfo, ...]


_MOVIE_MAIN_TITLE_THRESHOLD = timedelta(minutes=60)
_MOVIE_TOTAL_RUNTIME_LIMIT = timedelta(hours=3)
_SERIES_MIN_DURATION = timedelta(minutes=20)
_SERIES_MAX_DURATION = timedelta(minutes=60)
_SERIES_GAP_LIMIT = 0.2  # 20% variation allowed between episode runtimes


def classify_disc(disc: DiscInfo) -> ClassificationResult:
    """Classify *disc* according to PRD heuristics.

    The function returns the inferred :class:`ClassificationResult`.
    """

    titles = list(disc.titles)
    if not titles:
        return ClassificationResult("movie", ())

    episode_candidates = _series_candidates(list(enumerate(titles)))
    if episode_candidates:
        ordered = tuple(title for _, title in episode_candidates)
        return ClassificationResult("series", ordered)

    durations = [title.duration.total_seconds() for title in titles]
    longest_index = max(range(len(titles)), key=durations.__getitem__)
    longest_title = titles[longest_index]
    total_runtime = sum(durations)

    if _is_movie_candidate(longest_title, durations, total_runtime):
        return ClassificationResult("movie", (longest_title,))

    return ClassificationResult("movie", (longest_title,))


def _is_movie_candidate(
    longest_title: TitleInfo,
    durations: Sequence[float],
    total_runtime: float,
) -> bool:
    longest_duration = longest_title.duration
    if longest_duration <= _MOVIE_MAIN_TITLE_THRESHOLD:
        return False

    if total_runtime > _MOVIE_TOTAL_RUNTIME_LIMIT.total_seconds():
        return False

    longest_seconds = longest_duration.total_seconds()
    return all(
        longest_seconds >= duration * 1.2 or duration == longest_seconds
        for duration in durations
    )


def _series_candidates(
    indexed_titles: Sequence[tuple[int, TitleInfo]],
) -> Tuple[tuple[int, TitleInfo], ...]:
    filtered = [
        (index, title)
        for index, title in indexed_titles
        if _SERIES_MIN_DURATION <= title.duration <= _SERIES_MAX_DURATION
    ]
    if len(filtered) < 2:
        return ()

    seconds = [title.duration.total_seconds() for _, title in filtered]
    average = sum(seconds) / len(seconds)
    if average == 0:
        return ()

    max_gap = max(abs(duration - average) / average for duration in seconds)
    if max_gap > _SERIES_GAP_LIMIT:
        return ()

    return tuple(sorted(filtered, key=lambda item: (item[1].duration, item[0])))
