---
id: 7c9e2a15
title: "Implement config loader"
role: Coder
priority: P1
phase_id: "P2-T1"
depends_on:
  - 9b3e6d84
  - d42c9f70
  - f3a1c5d2
acceptance:
  - "`src/discripper/core/config.py` implements a loader that starts from project defaults, reads `~/.config/discripper.yaml` when present, and merges CLI overrides with precedence defaults < file < overrides."
  - "`discripper --help` documents a `--config-path` (or similarly named) flag that lets users specify an alternate config file path."
  - "Unit tests in `tests/test_config.py` cover no-file, file-only, and file-plus-overrides scenarios using temporary paths, and the suite passes with `pytest -q --cov=src --cov-fail-under=80`."
evidence:
  expected:
    - "pip install -e ."
    - "ruff check ."
    - "pytest -q --cov=src --cov-fail-under=80"
    - "discripper --help"
  artifacts:
    - "src/discripper/core/config.py"
    - "src/discripper/cli.py"
    - "tests/test_config.py"
---

## Context
Phase 2 adds real configuration handling so the CLI can honor defaults while letting users override settings via config files and command-line flags.

## Plan
- Implement the configuration loader in `src/discripper/core/config.py`, including YAML parsing and precedence handling aligned with the PRD. 
- Extend the CLI to expose a `--config-path` flag that feeds into the loader while continuing to support the default at `~/.config/discripper.yaml`.
- Add comprehensive pytest coverage around precedence scenarios and ensure all local gates succeed.
