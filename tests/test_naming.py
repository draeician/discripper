from discripper.core import sanitize_component


def test_sanitize_component_replaces_unsafe_characters() -> None:
    sanitized = sanitize_component("Firefly: Serenity/Part 1")
    assert sanitized == "Firefly_Serenity_Part_1"


def test_sanitize_component_strips_diacritics() -> None:
    sanitized = sanitize_component("Café del Mar")
    assert sanitized == "Cafe_del_Mar"


def test_sanitize_component_honors_custom_separator() -> None:
    sanitized = sanitize_component("Episode 01", separator="-")
    assert sanitized == "Episode-01"


def test_sanitize_component_collapses_repeated_separators() -> None:
    sanitized = sanitize_component("  --  odd***name  ")
    assert sanitized == "odd_name"


def test_sanitize_component_returns_fallback_when_empty() -> None:
    sanitized = sanitize_component("@@@@")
    assert sanitized == "untitled"


def test_sanitize_component_applies_lowercase_when_requested() -> None:
    sanitized = sanitize_component("Firefly: Serenity", lowercase=True)
    assert sanitized == "firefly_serenity"
