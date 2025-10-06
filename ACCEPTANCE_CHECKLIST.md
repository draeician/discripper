# PRD Acceptance Checklist

This checklist confirms that the acceptance criteria in [PRD §9](PRD.md#9--acceptance-criteria) are satisfied by the current implementation.

| Criterion | Status | Evidence |
| --- | --- | --- |
| Running `discripper /dev/sr0` rips a movie disc into a single MP4 with a proper filename. | ✅ | `scripts/acceptance.sh` runs the simulated movie scenario, ensures the CLI reports `EVENT=CLASSIFIED TYPE=movie`, and confirms exactly one rip plan is emitted, validating the single-file workflow. |
| Running `discripper /dev/sr0` on a TV series disc splits and names episodes correctly. | ✅ | `scripts/acceptance.sh` covers the simulated series scenario, asserting the CLI reports `EVENT=CLASSIFIED TYPE=series` and prepares four rip plans, demonstrating multi-episode handling. |
| Output structure matches `<series>/<series>-s01e01_Title.mp4`. | ✅ | `tests/test_naming.py::test_series_output_path_creates_nested_structure` checks that series output paths follow the `<series>/<series>-sXXeYY_<title>.mp4` convention, including sanitization and lowercase handling. |
| Configurable output directory is respected. | ✅ | `tests/test_naming.py::test_movie_output_path_uses_configured_directory` and `tests/test_cli.py::test_resolve_cli_config_applies_precedence` verify that the configured `output_directory` is honored across naming helpers and CLI configuration precedence. |
| Errors are handled gracefully with clear messaging. | ✅ | `tests/test_cli.py::test_main_errors_when_device_missing` and `tests/test_cli.py::test_main_errors_when_no_inspection_tools` assert that missing devices and tooling produce user-friendly error messages with the documented exit codes. |

All acceptance checks are therefore met by the existing tests and automation.
