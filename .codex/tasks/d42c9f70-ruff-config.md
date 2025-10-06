---
id: d42c9f70
title: "Add Ruff config"
role: Coder
priority: P0
phase_id: "P1-T5"
depends_on:
  - 4a7d2c19
acceptance:
  - "`pyproject.toml` (or `.ruff.toml`) configures Ruff with agreed rules for the src layout."
  - "`ruff check .` passes without diagnostics."
  - "Add Ruff invocation to developer docs or tooling so contributors know how to lint."
evidence:
  expected:
    - "ruff check ."
  artifacts:
    - "pyproject.toml"
    - "docs or README snippet describing lint command"
---

## Context
Introduce linting early to keep style consistent and catch issues before expanding the codebase.

## Plan
- Configure Ruff via `pyproject.toml` (preferred) with project-appropriate rules and ignores.
- Ensure lint command covers `src/` and `tests/` directories.
- Run Ruff and update docs or scripts so contributors can lint reliably.
