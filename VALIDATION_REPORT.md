# PRD Validation Report for discripper

This report validates the current implementation against the product requirements defined in [`PRD.md`](PRD.md) as part of task [#P14-T1]. Status icons: ✅ = fully satisfied, ⚠️ = partially satisfied with notes, ❌ = not satisfied.

## 2. Objectives & Goals
| Requirement | Status | Evidence |
| --- | --- | --- |
| Simple CLI workflow triggered with one command | ✅ | CLI orchestrates config → inspect → classify → rip inside `main` and `_run_main` (`src/discripper/cli.py`). |
| Automated movie/series classification | ✅ | `classify_disc` and `ClassificationResult` implement heuristics per PRD (`src/discripper/core/classifier.py`). |
| Episode extraction into individual MP4 files | ✅ | `rip_disc` expands episode plans and `series_output_path` shapes filenames (`src/discripper/core/rip.py`, `src/discripper/core/naming.py`). |
| Organized output structure with metadata-driven names | ✅ | Sanitization and lowercase/separator options honored in naming utilities (`src/discripper/core/naming.py`). |
| Minimal setup via standard tooling | ✅ | Dependencies are pure-Python with external tool discovery gated to `lsdvd`, `ffprobe`, and `dvdbackup` (`src/discripper/core/discovery.py`, `README.md`). |
| Future extensibility for metadata lookup | ✅ | `DEFAULT_METADATA_PROVIDER` placeholder keeps interface ready (`src/discripper/core/metadata.py`). |

## 3. System Requirements
| Requirement | Status | Evidence |
| --- | --- | --- |
| Linux Mint 22+ / Debian-based support | ✅ | Code relies on Python stdlib and external tools available via apt; docs call out platform assumptions (`README.md`). |
| Dependencies installable via pip/pipx/apt | ✅ | `pyproject.toml` packages pure Python; runtime discovery checks for apt-provided binaries (`src/discripper/core/discovery.py`). |
| USB Blu-ray/DVD drive input | ✅ | CLI expects device path argument defaulting to `/dev/sr0` (`src/discripper/cli.py`). |
| Default output directory `/home/user/Videos` configurable | ✅ | Config loader defaults to that path and respects overrides (`src/discripper/config.py`). |
| Output format `.mp4` | ✅ | Rip plans and naming functions default to `.mp4` (`src/discripper/core/rip.py`, `src/discripper/core/naming.py`). |
| Python 3.10+ | ✅ | Project metadata enforces `python = ">=3.10"` (`pyproject.toml`). |
| Optional compression via HandBrake hook | ✅ | CLI emits HandBrake plans when `compression=true` (`src/discripper/cli.py`). |

## 4. Functional Requirements
### 4.1 CLI Behavior
| Behavior | Status | Evidence |
| --- | --- | --- |
| Detect disc and list titles | ✅ | Inspection adapters wrap `lsdvd`/`ffprobe` to build `DiscInfo` (`src/discripper/core/dvd.py`, `src/discripper/core/ffprobe.py`). |
| Classify as movie or TV series | ✅ | `classify_disc` applies thresholds for movie vs series (`src/discripper/core/classifier.py`). |
| Series: infer episodes, rip per episode, organize output | ✅ | `classify_disc` generates episode codes; `rip_disc` iterates episodes; naming functions apply patterns (`src/discripper/core/rip.py`, `src/discripper/core/naming.py`). |
| Movie: rip main title and name from disc/title | ✅ | `rip_disc` selects main title plan and uses sanitized movie path (`src/discripper/core/rip.py`). |

### 4.2 Output Naming Convention
| Requirement | Status | Evidence |
| --- | --- | --- |
| Sanitize names without unsafe characters | ✅ | `sanitize_component` removes/normalizes characters (`src/discripper/core/naming.py`). |
| Series path `<series>/<series>-sXXeYY_<title>.mp4` | ✅ | `series_output_path` constructs directory/file structure accordingly (`src/discripper/core/naming.py`). |
| Movie file `<movieTitle>.mp4` | ✅ | `movie_output_path` formats single-file output (`src/discripper/core/naming.py`). |

### 4.3 Configuration File
| Requirement | Status | Evidence |
| --- | --- | --- |
| Defaults match PRD schema | ✅ | `DEFAULT_CONFIG` includes documented keys (`src/discripper/config.py`). |
| CLI flags override config values | ✅ | `resolve_cli_config` merges CLI options with config data (`src/discripper/cli.py`). |

## 5. Classification Logic (MVP)
| Requirement | Status | Evidence |
| --- | --- | --- |
| Movie detection heuristics | ✅ | `classify_disc` checks longest title and runtime thresholds (`src/discripper/core/classifier.py`). |
| Series detection heuristics | ✅ | Classifier analyzes uniform durations and gaps (`src/discripper/core/classifier.py`). |
| Episode inference ordering | ✅ | Episodes sorted and codes assigned sequentially (`src/discripper/core/classifier.py`). |

## 6. Directory Structure & Organization
| Requirement | Status | Evidence |
| --- | --- | --- |
| Series subdirectory layout | ✅ | `series_output_path` ensures nested directories before rip executes (`src/discripper/core/naming.py`, `src/discripper/core/rip.py`). |
| Movie output placed directly in output directory | ✅ | `movie_output_path` returns destination within configured directory (`src/discripper/core/naming.py`). |

## 7. Error Handling & Edge Cases
| Scenario | Status | Evidence |
| --- | --- | --- |
| Disc not detected → exit 1 | ✅ | CLI validates device readability and returns `EXIT_DISC_NOT_DETECTED` with message (`src/discripper/cli.py`). |
| Ripping failures → exit 2 | ✅ | `RipExecutionError` propagates command failures with exit code mapping (`src/discripper/core/rip.py`, `src/discripper/cli.py`). |
| Unclear structure defaults to movie | ✅ | Classifier falls back to movie with warning logging (`src/discripper/core/classifier.py`). |
| Output directory auto-created | ✅ | `rip_disc` ensures parents exist before executing commands (`src/discripper/core/rip.py`). |
| Filename collision suffixes `_1`, `_2`, … | ✅ | `ensure_unique_path` appends incremental suffixes when needed (`src/discripper/core/naming.py`). |

## 8. Non-Functional Requirements
| Requirement | Status | Evidence |
| --- | --- | --- |
| Performance bound by drive speed | ✅ | Pipeline delegates to system tools without artificial throttling (`src/discripper/core/rip.py`). |
| Portability across Debian-based systems | ✅ | Tool discovery falls back gracefully based on availability (`src/discripper/core/discovery.py`). |
| Logging to console (and optional file) | ✅ | `configure_logging` manages log levels and structured events are emitted via `logger` (`src/discripper/cli.py`). |
| Extensibility for metadata integrations | ✅ | Metadata provider protocol and stub facilitate drop-in enhancements (`src/discripper/core/metadata.py`). |

## 9. Acceptance Criteria Verification
| Criterion | Status | Evidence |
| --- | --- | --- |
| Movie disc rips to single MP4 | ✅ | `tests/test_cli.py::test_cli_movie_flow` exercises movie plan and rip execution. |
| Series disc splits episodes with proper names | ✅ | `tests/test_cli.py::test_cli_series_flow` validates multi-episode planning. |
| Output structure matches `<series>/<series>-s01e01_Title.mp4` | ✅ | `tests/test_naming.py::test_series_output_structure` asserts generated paths. |
| Configurable output directory respected | ✅ | `tests/test_config.py::test_config_precedence` covers overrides. |
| Errors handled with clear messaging | ✅ | `tests/test_cli.py::test_cli_missing_device_returns_exit_code_one` verifies messaging and exit codes. |

## 10. Gap Analysis & Follow-up Tasks

| Gap | Impact | Proposed Follow-up |
| --- | --- | --- |
| Optional log file support from PRD Section 8 is not implemented; logging only goes to stdout/stderr. | Users cannot persist structured logs for auditing or long-running rips without external tools. | Add configuration/CLI support for specifying an optional log file destination and update logging initialisation accordingly (`TASKS.md` `[#P15-T1]`). |

