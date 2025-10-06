"""Disc classification heuristics."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
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
    episode_codes: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.episode_codes and len(self.episode_codes) != len(self.episodes):
            msg = "episode_codes must align with episodes"
            raise ValueError(msg)

    @property
    def numbered_episodes(self) -> Tuple[Tuple[str, "TitleInfo"], ...]:
        """Return episodes paired with their inferred ``s01eNN`` codes."""

        return tuple(zip(self.episode_codes, self.episodes))


@dataclass(frozen=True, slots=True)
class ClassificationThresholds:
    """Configurable thresholds that steer the classification heuristics."""

    movie_main_title: timedelta = timedelta(minutes=60)
    movie_total_runtime: timedelta = timedelta(hours=3)
    series_min_duration: timedelta = timedelta(minutes=20)
    series_max_duration: timedelta = timedelta(minutes=60)
    series_gap_limit: float = 0.2


DEFAULT_THRESHOLDS = ClassificationThresholds()


def classify_disc(
    disc: DiscInfo, *, thresholds: ClassificationThresholds | None = None
) -> ClassificationResult:
    """Classify *disc* according to PRD heuristics.

    The function returns the inferred :class:`ClassificationResult`.
    """

    active_thresholds = thresholds or DEFAULT_THRESHOLDS
    titles = list(disc.titles)
    if not titles:
        return ClassificationResult("movie", ())

    episode_candidates = _series_candidates(
        list(enumerate(titles)), active_thresholds
    )
    if episode_candidates:
        ordered = tuple(title for _, title in episode_candidates)
        codes = tuple(f"s01e{index + 1:02d}" for index in range(len(ordered)))
        return ClassificationResult("series", ordered, codes)

    durations = [title.duration.total_seconds() for title in titles]
    longest_index = max(range(len(titles)), key=durations.__getitem__)
    longest_title = titles[longest_index]
    total_runtime = sum(durations)

    if _is_movie_candidate(longest_title, durations, total_runtime, active_thresholds):
        return ClassificationResult("movie", (longest_title,))

    return ClassificationResult("movie", (longest_title,))


def _is_movie_candidate(
    longest_title: TitleInfo,
    durations: Sequence[float],
    total_runtime: float,
    thresholds: ClassificationThresholds,
) -> bool:
    longest_duration = longest_title.duration
    if longest_duration <= thresholds.movie_main_title:
        return False

    if total_runtime > thresholds.movie_total_runtime.total_seconds():
        return False

    longest_seconds = longest_duration.total_seconds()
    return all(
        longest_seconds >= duration * 1.2 or duration == longest_seconds
        for duration in durations
    )


def _series_candidates(
    indexed_titles: Sequence[tuple[int, TitleInfo]],
    thresholds: ClassificationThresholds,
) -> Tuple[tuple[int, TitleInfo], ...]:
    filtered = [
        (index, title)
        for index, title in indexed_titles
        if thresholds.series_min_duration
        <= title.duration
        <= thresholds.series_max_duration
    ]
    if len(filtered) < 2:
        return ()

    seconds = [title.duration.total_seconds() for _, title in filtered]
    average = sum(seconds) / len(seconds)
    if average == 0:
        return ()

    max_gap = max(abs(duration - average) / average for duration in seconds)
    if max_gap > thresholds.series_gap_limit:
        return ()

    return tuple(sorted(filtered, key=lambda item: (item[1].duration, item[0])))


def thresholds_from_config(
    config: Mapping[str, object]
) -> ClassificationThresholds:
    """Return :class:`ClassificationThresholds` derived from *config* mapping."""

    classification_section = config.get("classification")
    if not isinstance(classification_section, Mapping):
        return DEFAULT_THRESHOLDS

    defaults = DEFAULT_THRESHOLDS

    def _duration_from_minutes(value: object, default: timedelta) -> timedelta:
        if isinstance(value, (int, float)) and value > 0:
            return timedelta(minutes=float(value))
        return default

    def _ratio(value: object, default: float) -> float:
        if isinstance(value, (int, float)) and value >= 0:
            return float(value)
        return default

    movie_main = _duration_from_minutes(
        classification_section.get("movie_main_title_minutes"),
        defaults.movie_main_title,
    )
    movie_total_runtime = _duration_from_minutes(
        classification_section.get("movie_total_runtime_minutes"),
        defaults.movie_total_runtime,
    )
    series_min = _duration_from_minutes(
        classification_section.get("series_min_duration_minutes"),
        defaults.series_min_duration,
    )
    series_max = _duration_from_minutes(
        classification_section.get("series_max_duration_minutes"),
        defaults.series_max_duration,
    )
    gap_limit = _ratio(
        classification_section.get("series_gap_limit"), defaults.series_gap_limit
    )

    derived = ClassificationThresholds(
        movie_main_title=movie_main,
        movie_total_runtime=movie_total_runtime,
        series_min_duration=series_min,
        series_max_duration=series_max,
        series_gap_limit=gap_limit,
    )

    if derived == defaults:
        return defaults

    return derived
