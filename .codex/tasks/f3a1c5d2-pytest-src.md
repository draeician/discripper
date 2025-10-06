---
id: f3a1c5d2
title: "Configure pytest src layout"
role: Coder
priority: P0
phase_id: "P1-T6"
depends_on:
  - 4a7d2c19
acceptance:
  - "`pyproject.toml` (or `pytest.ini`) sets pytest defaults: `-q`, `pythonpath=src`, and any needed ini options."
  - "A placeholder test (e.g., `tests/test_placeholder.py`) exists so discovery verifies the layout."
  - "`pytest -q` passes from a clean checkout."
evidence:
  expected:
    - "pytest -q"
  artifacts:
    - "pyproject.toml"
    - "tests/test_placeholder.py"
---

## Context
Align pytest with the src/ layout early so later tests run without import friction and CI can execute consistently.

## Plan
- Add pytest configuration under `pyproject.toml` to point at `src/` and quiet output.
- Create a minimal placeholder test to assert the harness works.
- Run pytest to confirm discovery and the config behave as expected.
