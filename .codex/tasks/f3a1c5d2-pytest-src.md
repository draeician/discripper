---
id: f3a1c5d2
title: "Configure pytest src layout"
role: Coder
priority: P0
phase_id: "P1-T6"
depends_on:
  - 4a7d2c19
acceptance:
  - "`pyproject.toml` (or `pytest.ini`) configures pytest with `pythonpath = [\"src\"]`, default `-q` flag, and coverage settings matching the local gate (`--cov=src --cov-fail-under=80`)."
  - "`tests/test_placeholder.py` exists and imports `discripper` to prove discovery works with the src layout."
  - "`pytest -q --cov=src --cov-fail-under=80` succeeds from a clean checkout."
evidence:
  expected:
    - "pip install -e ."
    - "ruff check ."
    - "pytest -q --cov=src --cov-fail-under=80"
  artifacts:
    - "pyproject.toml"
    - "tests/test_placeholder.py"
---

## Context
Align pytest with the src/ directory structure so later tests run without path hacks and coverage targets are enforced from day one.

## Plan
- Add pytest configuration (preferably in `pyproject.toml`) that points to `src/`, sets the quiet flag, and enforces coverage thresholds.
- Write a simple placeholder test that imports `discripper` to validate discovery against the src layout.
- Execute the local gates to ensure pytest passes with the configured options.
