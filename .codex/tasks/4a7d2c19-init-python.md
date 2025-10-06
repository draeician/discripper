---
id: 4a7d2c19
title: "Initialize PEP 621 project"
role: Coder
priority: P0
phase_id: "P1-T1"
depends_on: []
acceptance:
  - "`pyproject.toml` defines a `[project]` table for {PROJECT_SLUG} with name, version, description, authors, and readme using PEP 621 fields."
  - "`src/{PROJECT_SLUG}/__init__.py` and `tests/` exist so the src layout and baseline test tree are ready."
  - "`python -m build` completes successfully from the repo root."
evidence:
  expected:
    - "python -m build"
  artifacts:
    - "pyproject.toml"
    - "src/{PROJECT_SLUG}/__init__.py"
---

## Context
Set up the minimal Python packaging scaffold so later tasks can add code, configs, and entry points per the roadmap.

## Plan
- Create `pyproject.toml` with PEP 621 metadata for {PROJECT_SLUG} and build-system config.
- Add `src/{PROJECT_SLUG}/__init__.py` and ensure `tests/` directory exists.
- Verify `python -m build` succeeds against the new layout.
