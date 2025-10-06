# TASKS.md — PRD-Driven Roadmap for discripper

> Source of truth: `PRD.md`  
> Tokens from Phase 0.2:
> - `{PROJECT_NAME}` = "discripper"
> - `{PROJECT_SLUG}` = "discripper"
> - `{ENTRYPOINT}` = "discripper"
> - `{CONFIG_PATH}` = "~/.config/discripper.yaml"

## Phase 1 – Project Setup & Scaffolding
- [x] Initialize Python project (PEP 621 `pyproject.toml`, `src/` layout, tests/) (repo builds locally) [#P1-T1]
- [x] Add console entry point for `{ENTRYPOINT}` in `pyproject.toml` (entry shows in `pip install -e .`) [#P1-T2]
- [x] Create package skeleton `src/{PROJECT_SLUG}/cli.py` and `src/{PROJECT_SLUG}/core/__init__.py` (imports succeed) [#P1-T3]
- [x] Add `.gitignore` for Python, build, and test artifacts (ignored files confirmed) [#P1-T4]
- [x] Add `ruff` config and minimal rule-set in `pyproject.toml` (ruff runs clean) [#P1-T5]
- [x] Add `pytest` config (`-q`, `pythonpath=src`) (tests discover/run) [#P1-T6]
- [x] Add `LICENSE` and minimal top-level `README.md` (files present) [#P1-T7]

## Phase 2 – Config & CLI
- [x] Implement config loader reading `{CONFIG_PATH}` (defaults used if file missing) [#P2-T1]
- [x] Implement CLI flags: `--config`, `--verbose`, `--dry-run` (flags override config values) [#P2-T2]
- [x] Add device argument with default `/dev/sr0` (help shows default) [#P2-T3]
- [x] Wire logging levels (INFO default, DEBUG with `--verbose`) (log level toggles) [#P2-T4]
- [x] Add schema fields: `output_directory`, `compression`, `naming.separator`, `naming.lowercase`, `logging.level` (schema validated) [#P2-T5]
- [ ] Unit tests for config precedence (defaults < config file < CLI flags) (pytest passes) [#P2-T6]
- [ ] `{ENTRYPOINT} --help` shows usage and options (help includes flags/args) [#P2-T7]

## Phase 3 – Core Inspection / Input Acquisition
- [ ] Define dataclasses `DiscInfo`, `TitleInfo` (fields for label, titles, chapters, durations) [#P3-T1]
- [ ] Implement tool discovery for `lsdvd`, `ffprobe`, and Blu-ray inspector (detect availability) [#P3-T2]
- [ ] Implement DVD inspector adapter using `lsdvd` where available (parses durations/titles) [#P3-T3]
- [ ] Implement fallback inspector using `ffprobe` on device (best-effort title/duration extraction) [#P3-T4]
- [ ] Stub Blu-ray path (documented detection; usable later) (graceful “not supported yet” message) [#P3-T5]
- [ ] Add fake inspector loading JSON fixtures from `tests/fixtures/` (injectable for tests) [#P3-T6]
- [ ] Error if device missing/unreadable (non-zero exit, actionable message) [#P3-T7]

## Phase 4 – Core Classification / Processing Logic
- [ ] Implement classifier per PRD thresholds (movie vs series) (returns type + episodes) [#P4-T1]
- [ ] Make thresholds configurable (e.g., long-title >60min, gaps <20%) (config keys respected) [#P4-T2]
- [ ] Episode inference for series (order + s01eNN labels) (deterministic numbering) [#P4-T3]
- [ ] Default to movie on ambiguous structure with warning (log explains heuristic) [#P4-T4]
- [ ] Unit tests: movie-only disc fixture (classifier selects main title) [#P4-T5]
- [ ] Unit tests: 6-episode fixture (classifier detects series, counts episodes) [#P4-T6]
- [ ] Unit tests: borderline/ambiguous fixture (falls back to movie) [#P4-T7]

## Phase 5 – Execution / Ripping Pipeline
- [ ] Implement `rip_title(device, title_info, dest_path, *, dry_run=False)` (returns success plan) [#P5-T1]
- [ ] Implement `rip_disc(...)` orchestrator for movie & series flows (iterates titles) [#P5-T2]
- [ ] Implement `ffmpeg`-based basic ripping path (document constraints) (ffmpeg path works) [#P5-T3]
- [ ] Detect and use `dvdbackup`/other tools if available (choose simplest successful path) [#P5-T4]
- [ ] Handle I/O errors with clear messages and non-zero exit codes (errors mapped) [#P5-T5]
- [ ] `--dry-run` prints plan only; performs no writes (no file side-effects) [#P5-T6]

## Phase 6 – Naming & Organization
- [ ] Implement ASCII/unsafe char sanitization; use `naming.separator` (sanitizer unit-tested) [#P6-T1]
- [ ] Implement `naming.lowercase` transformation (filenames & dirs reflect flag) [#P6-T2]
- [ ] Movie pattern: `<movieTitle>.mp4` in configured output dir (file path correct) [#P6-T3]
- [ ] Series pattern: `<seriesName>/<seriesName>-s01eNN_<title>.mp4` (path shape correct) [#P6-T4]
- [ ] Collision handling appends suffix `_1`, `_2`, … (no overwrite occurs) [#P6-T5]
- [ ] Ensure parent directories are created as needed (dirs created automatically) [#P6-T6]

## Phase 7 – Orchestration, Logging, Error Handling
- [ ] CLI main flow: config → inspect → classify → plan → rip (end-to-end path executes) [#P7-T1]
- [ ] Structured logs: classification summary (e.g., `EVENT=CLASSIFIED TYPE=series EPISODES=6`) [#P7-T2]
- [ ] Structured logs: rip results per file (e.g., `EVENT=RIP_DONE FILE=... BYTES=...`) [#P7-T3]
- [ ] Exit codes: 1=disc not detected, 2=rip failed, etc. (documented; enforced) [#P7-T4]
- [ ] Prompt/guard only when destructive overwrite would occur (safe default) [#P7-T5]
- [ ] Centralize exceptions → user-friendly messages (no raw tracebacks by default) [#P7-T6]

## Phase 8 – Tests & Fixtures
- [ ] Add fixtures: single-movie disc JSON (titles + durations) (file present) [#P8-T1]
- [ ] Add fixtures: multi-episode disc JSON (6 episodes) (file present) [#P8-T2]
- [ ] Add fixtures: ambiguous structure JSON (borderline durations) (file present) [#P8-T3]
- [ ] Tests: config precedence (defaults/config/CLI) (pytest passes) [#P8-T4]
- [ ] Tests: classification across all fixtures (pass; deterministic) [#P8-T5]
- [ ] Tests: naming sanitization & lowercase options (pass) [#P8-T6]
- [ ] Tests: dry-run planning prints expected actions (pass) [#P8-T7]
- [ ] Tests: exit code mapping for common failures (pass) [#P8-T8]
- [ ] Coverage gate ≥ 80% (report shows ≥80%) [#P8-T9]

## Phase 9 – Packaging & Install
- [ ] Finalize `pyproject.toml` metadata (name, version, classifiers) (builds sdist/wheel) [#P9-T1]
- [ ] Confirm `console_scripts` exposes `{ENTRYPOINT}` (invokes CLI after install) [#P9-T2]
- [ ] Makefile: `install`, `lint`, `test`, `format` targets (targets run successfully) [#P9-T3]
- [ ] Verify `pipx install -e .` and `pip install -e .` (both flows work) [#P9-T4]

## Phase 10 – Docs & Quickstart
- [ ] Root `README.md`: prerequisites (apt tools), install, usage (movie & series), dry-run (sections present) [#P10-T1]
- [ ] Document config schema and `{CONFIG_PATH}` override (examples provided) [#P10-T2]
- [ ] Troubleshooting section: common errors & resolutions (page anchors added) [#P10-T3]
- [ ] CLI `--help` examples included in docs (copy/paste verified) [#P10-T4]

## Phase 11 – Simulation / E2E Dry-Run
- [ ] Hidden flag `--simulate FIXTURE.json` drives full pipeline without hardware (flag works) [#P11-T1]
- [ ] Provide two sample simulation JSONs (movie, series) (files included) [#P11-T2]
- [ ] `scripts/demo.sh` shows planning & dry-run with simulate (script runs clean) [#P11-T3]

## Phase 12 – Optional / Deferred Features
- [ ] Post-rip HandBrake hook if `compression=true` (command assembled; disabled by default) [#P12-T1]
- [ ] Configurable episode title inference strategy (pluggable; documented) [#P12-T2]
- [ ] Metadata lookup (TheTVDB/TMDB) placeholder interface (non-blocking stub) [#P12-T3]

## Phase 13 – Final QA & Acceptance
- [ ] `scripts/acceptance.sh` runs fixtures end-to-end (exit codes & plans verified) [#P13-T1]
- [ ] Verify PRD acceptance criteria satisfied (checklist compiled) [#P13-T2]
- [ ] Verify directory/naming conventions match PRD (examples produced) [#P13-T3]
- [ ] Verify config defaults & overrides (table in docs updated) [#P13-T4]

## Phase 14 – Validation Against PRD
- [ ] Produce validation report mapping implementation → PRD sections (✅/❌ per item) [#P14-T1]
- [ ] List gaps & propose minimal follow-ups (new tasks enumerated) [#P14-T2]
- [ ] Sign-off: Reviewer + Auditor notes recorded in `.codex/reviews/` & `.codex/audit/` (files present) [#P14-T3]
