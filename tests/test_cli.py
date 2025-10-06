"""Tests for the discripper command-line interface."""

from __future__ import annotations

import logging
import json
from datetime import timedelta
from pathlib import Path
from subprocess import CompletedProcess

import pytest
import yaml

from discripper import cli, config as config_module
from discripper.core import (
    BluRayNotSupportedError,
    ClassificationResult,
    DiscInfo,
    InspectionTools,
    RipExecutionError,
    RipPlan,
    TitleInfo,
    ToolAvailability,
)


def _write_config(tmp_path: Path, content: dict[str, object]) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(content), encoding="utf-8")
    return config_path


def _install_movie_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    use_fallback: bool = False,
    dry_run: bool = False,
):
    events: list[object] = []
    title = TitleInfo(label="Main Feature", duration=timedelta(minutes=95))
    disc = DiscInfo(label="Sample Disc", titles=(title,))
    classification = ClassificationResult("movie", (title,))

    tools = InspectionTools(
        dvd=None if use_fallback else ToolAvailability("lsdvd", "/usr/bin/lsdvd"),
        fallback=ToolAvailability("ffprobe", "/usr/bin/ffprobe") if use_fallback else None,
        blu_ray=None,
    )

    def fake_discover() -> InspectionTools:
        events.append(("discover", use_fallback))
        return tools

    monkeypatch.setattr(cli, "discover_inspection_tools", fake_discover)

    if use_fallback:
        def unexpected_dvd(*_args, **_kwargs):
            raise AssertionError("DVD inspector should not be used when only fallback exists")

        monkeypatch.setattr(cli, "inspect_dvd", unexpected_dvd)

        def fake_inspect(device: str, *, tool: ToolAvailability) -> DiscInfo:
            events.append(("inspect", tool.command))
            return disc

        monkeypatch.setattr(cli, "inspect_with_ffprobe", fake_inspect)
    else:
        def unexpected_ffprobe(*_args, **_kwargs):
            raise AssertionError("Fallback inspector should not be used when DVD tool exists")

        monkeypatch.setattr(cli, "inspect_with_ffprobe", unexpected_ffprobe)

        def fake_inspect(device: str, *, tool: ToolAvailability) -> DiscInfo:
            events.append(("inspect", tool.command))
            return disc

        monkeypatch.setattr(cli, "inspect_dvd", fake_inspect)

    def fake_classify(disc_info: DiscInfo, *, thresholds) -> ClassificationResult:
        events.append(("classify", disc_info.label))
        return classification

    monkeypatch.setattr(cli, "classify_disc", fake_classify)

    def fake_movie_output_path(title_info: TitleInfo, config: dict[str, object]) -> Path:
        events.append(("movie_output_path", title_info.label))
        return tmp_path / "output.mp4"

    monkeypatch.setattr(cli, "movie_output_path", fake_movie_output_path)

    def unexpected_series_output_path(*_args, **_kwargs):
        raise AssertionError("Series output path should not be used for movie classification")

    monkeypatch.setattr(cli, "series_output_path", unexpected_series_output_path)

    def fake_rip_disc(
        device: str,
        classification_value: ClassificationResult,
        destination_factory,
        *,
        dry_run: bool,
        which=None,
    ) -> tuple[RipPlan, ...]:
        events.append(("rip_disc", device, dry_run))
        destination = destination_factory(classification_value.episodes[0], None)
        plan = RipPlan(
            device=device,
            title=classification_value.episodes[0],
            destination=Path(destination),
            command=("echo", "rip"),
            will_execute=not dry_run,
        )
        return (plan,)

    monkeypatch.setattr(cli, "rip_disc", fake_rip_disc)

    def fake_run(plan: RipPlan):
        events.append(("run_rip_plan", plan.destination))
        if plan.will_execute and dry_run:
            raise AssertionError("Plan should respect dry-run flag")
        return None

    monkeypatch.setattr(cli, "run_rip_plan", fake_run)

    return events


def _install_series_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    events: list[object] = []
    title_one = TitleInfo(label="Episode One", duration=timedelta(minutes=44))
    title_two = TitleInfo(label="Episode Two", duration=timedelta(minutes=45))
    disc = DiscInfo(label="Sample Series", titles=(title_one, title_two))
    classification = ClassificationResult(
        "series",
        (title_one, title_two),
        ("s01e01", "s01e02"),
    )

    tools = InspectionTools(
        dvd=ToolAvailability("lsdvd", "/usr/bin/lsdvd"),
        fallback=None,
        blu_ray=None,
    )

    def fake_discover() -> InspectionTools:
        events.append(("discover", "series"))
        return tools

    monkeypatch.setattr(cli, "discover_inspection_tools", fake_discover)

    def fake_inspect(device: str, *, tool: ToolAvailability) -> DiscInfo:
        events.append(("inspect", tool.command))
        return disc

    monkeypatch.setattr(cli, "inspect_dvd", fake_inspect)

    def fake_classify(disc_info: DiscInfo, *, thresholds) -> ClassificationResult:
        events.append(("classify", disc_info.label))
        return classification

    monkeypatch.setattr(cli, "classify_disc", fake_classify)

    def unexpected_movie_output_path(*_args, **_kwargs):
        raise AssertionError("Movie output path should not be used for series classification")

    monkeypatch.setattr(cli, "movie_output_path", unexpected_movie_output_path)

    def fake_series_output_path(
        series_label: str,
        title_info: TitleInfo,
        episode_code: str,
        config: dict[str, object],
    ) -> Path:
        events.append(("series_output_path", series_label, episode_code, title_info.label))
        return tmp_path / f"{episode_code}_{title_info.label}.mp4"

    monkeypatch.setattr(cli, "series_output_path", fake_series_output_path)

    def fake_rip_disc(
        device: str,
        classification_value: ClassificationResult,
        destination_factory,
        *,
        dry_run: bool,
        which=None,
    ) -> tuple[RipPlan, ...]:
        events.append(("rip_disc", device, dry_run))
        plans: list[RipPlan] = []
        for title_info, episode_code in zip(
            classification_value.episodes, classification_value.episode_codes
        ):
            destination = destination_factory(title_info, episode_code)
            plans.append(
                RipPlan(
                    device=device,
                    title=title_info,
                    destination=Path(destination),
                    command=("echo", episode_code),
                    will_execute=not dry_run,
                )
            )
        return tuple(plans)

    monkeypatch.setattr(cli, "rip_disc", fake_rip_disc)

    def fake_run(plan: RipPlan):
        events.append(("run_rip_plan", plan.destination, plan.command[-1]))
        return None

    monkeypatch.setattr(cli, "run_rip_plan", fake_run)

    return events


def test_parse_arguments_supports_expected_flags() -> None:
    """The CLI parser recognises the config, verbose, and dry-run flags."""

    args = cli.parse_arguments(["--config", "example.yaml", "--verbose", "--dry-run"])

    assert args.config_path == "example.yaml"
    assert args.verbose is True
    assert args.dry_run is True


def test_parse_arguments_supports_simulate_flag(tmp_path) -> None:
    """The CLI parser recognises the hidden --simulate option."""

    fixture = tmp_path / "disc.json"
    args = cli.parse_arguments(["--simulate", str(fixture)])

    assert args.simulate == str(fixture)


def test_parse_arguments_includes_device_with_default() -> None:
    """The parser exposes a device argument with the expected default value."""

    args = cli.parse_arguments([])

    assert args.device == "/dev/sr0"


def test_resolve_cli_config_uses_custom_config_path(tmp_path) -> None:
    """Providing --config loads and returns the specified configuration file."""

    config_path = _write_config(
        tmp_path,
        {
            "logging": {"level": "WARNING"},
            "dry_run": False,
        },
    )

    args = cli.parse_arguments(["--config", str(config_path)])
    resolved = cli.resolve_cli_config(args)

    assert resolved["logging"]["level"] == "WARNING"
    assert resolved["dry_run"] is False


def test_resolve_cli_config_sets_device_from_arguments(tmp_path) -> None:
    """The device argument is propagated into the resolved configuration."""

    config_path = _write_config(tmp_path, {})

    args = cli.parse_arguments(["--config", str(config_path), "/dev/dvd"])
    resolved = cli.resolve_cli_config(args)

    assert resolved["device"] == "/dev/dvd"


def test_resolve_cli_config_overrides_logging_with_verbose(tmp_path) -> None:
    """--verbose forces the logging level to DEBUG regardless of config value."""

    config_path = _write_config(tmp_path, {"logging": {"level": "INFO"}})

    args = cli.parse_arguments(["--config", str(config_path), "--verbose"])
    resolved = cli.resolve_cli_config(args)

    assert resolved["logging"]["level"] == "DEBUG"


def test_resolve_cli_config_sets_dry_run_flag(tmp_path) -> None:
    """--dry-run updates the configuration to reflect a dry run."""

    config_path = _write_config(tmp_path, {"dry_run": False})

    args = cli.parse_arguments(["--config", str(config_path), "--dry-run"])
    resolved = cli.resolve_cli_config(args)

    assert resolved["dry_run"] is True


def test_resolve_cli_config_applies_precedence(tmp_path) -> None:
    """Defaults are overridden by config file, which in turn yields to CLI flags."""

    config_path = _write_config(
        tmp_path,
        {
            "output_directory": "/mnt/custom",
            "logging": {"level": "WARNING"},
            "dry_run": False,
        },
    )

    args = cli.parse_arguments(
        ["--config", str(config_path), "--verbose", "--dry-run"]
    )
    resolved = cli.resolve_cli_config(args)

    assert resolved["output_directory"] == "/mnt/custom"
    assert resolved["logging"]["level"] == "DEBUG"
    assert resolved["dry_run"] is True


def test_resolve_cli_config_layers_defaults_config_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicitly verify precedence across defaults, config file, and CLI flags."""

    managed_config = tmp_path / "managed-config.yaml"
    monkeypatch.setattr(config_module, "CONFIG_PATH", managed_config)

    default_args = cli.parse_arguments([])
    resolved_defaults = cli.resolve_cli_config(default_args)

    assert resolved_defaults["output_directory"] == config_module.DEFAULT_CONFIG["output_directory"]
    assert resolved_defaults["dry_run"] is config_module.DEFAULT_CONFIG["dry_run"]

    managed_config.write_text(
        yaml.safe_dump(
            {
                "output_directory": "/mnt/config",
                "logging": {"level": "WARNING"},
                "dry_run": False,
            }
        ),
        encoding="utf-8",
    )

    config_args = cli.parse_arguments([])
    resolved_config = cli.resolve_cli_config(config_args)

    assert resolved_config["output_directory"] == "/mnt/config"
    assert resolved_config["logging"]["level"] == "WARNING"
    assert resolved_config["dry_run"] is False

    cli_args = cli.parse_arguments(["--verbose", "--dry-run"])
    resolved_cli = cli.resolve_cli_config(cli_args)

    assert resolved_cli["output_directory"] == "/mnt/config"
    assert resolved_cli["logging"]["level"] == "DEBUG"
    assert resolved_cli["dry_run"] is True


def test_cli_help_mentions_device_default() -> None:
    """The help output mentions the default device path."""

    help_text = cli.build_argument_parser().format_help()

    assert "/dev/sr0" in help_text


def test_cli_main_help_output_lists_expected_options(capsys) -> None:
    """Running the CLI with --help shows usage and all defined options."""

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0

    captured = capsys.readouterr().out

    assert "usage: discripper" in captured
    assert "--config" in captured
    assert "--verbose" in captured
    assert "--dry-run" in captured


def test_main_configures_info_logging_by_default(tmp_path, monkeypatch) -> None:
    """INFO logging is enabled when --verbose is not supplied."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    _install_movie_pipeline(monkeypatch, tmp_path)

    logging.basicConfig(level=logging.NOTSET, force=True)
    try:
        exit_code = cli.main([str(device)])
        assert exit_code == cli.EXIT_SUCCESS
        assert logging.getLogger().getEffectiveLevel() == logging.INFO
    finally:
        logging.basicConfig(level=logging.NOTSET, force=True)


def test_main_configures_debug_logging_with_verbose(tmp_path, monkeypatch) -> None:
    """DEBUG logging is enabled when --verbose is provided."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    _install_movie_pipeline(monkeypatch, tmp_path)

    logging.basicConfig(level=logging.NOTSET, force=True)
    try:
        exit_code = cli.main(["--verbose", str(device)])
        assert exit_code == cli.EXIT_SUCCESS
        assert logging.getLogger().getEffectiveLevel() == logging.DEBUG
    finally:
        logging.basicConfig(level=logging.NOTSET, force=True)


def test_main_simulate_uses_fixture_and_forces_dry_run(tmp_path, monkeypatch) -> None:
    """Simulation mode loads the fixture without touching the device."""

    fixture = tmp_path / "simulation.json"
    fixture.write_text(
        json.dumps(
            {
                "label": "Simulated Disc",
                "titles": [
                    {
                        "label": "Simulated Feature",
                        "duration": 5400,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    events: list[object] = []

    def unexpected_discover():
        raise AssertionError("discover_inspection_tools should not run in simulation mode")

    monkeypatch.setattr(cli, "discover_inspection_tools", unexpected_discover)

    def fake_classify(disc_info: DiscInfo, *, thresholds) -> ClassificationResult:
        events.append(("classify", disc_info.label))
        return ClassificationResult("movie", disc_info.titles)

    monkeypatch.setattr(cli, "classify_disc", fake_classify)

    def fake_movie_output_path(title_info: TitleInfo, config: dict[str, object]) -> Path:
        events.append(("movie_output_path", title_info.label))
        return tmp_path / "output.mp4"

    monkeypatch.setattr(cli, "movie_output_path", fake_movie_output_path)

    def fake_rip_disc(
        device: str,
        classification_value: ClassificationResult,
        destination_factory,
        *,
        dry_run: bool,
        which=None,
    ) -> tuple[RipPlan, ...]:
        events.append(("rip_disc", device, dry_run))
        destination = destination_factory(classification_value.episodes[0], None)
        return (
            RipPlan(
                device=device,
                title=classification_value.episodes[0],
                destination=Path(destination),
                command=("echo", "rip"),
                will_execute=not dry_run,
            ),
        )

    monkeypatch.setattr(cli, "rip_disc", fake_rip_disc)

    def fake_run(plan: RipPlan):
        events.append(("run_rip_plan", plan.destination))
        return None

    monkeypatch.setattr(cli, "run_rip_plan", fake_run)

    exit_code = cli.main(["--simulate", str(fixture)])

    assert exit_code == cli.EXIT_SUCCESS
    assert ("classify", "Simulated Disc") in events
    assert any(event[0] == "rip_disc" and event[2] is True for event in events)


def test_main_executes_pipeline(monkeypatch, tmp_path) -> None:
    """The CLI orchestrates discovery, inspection, planning, and ripping."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    events = _install_movie_pipeline(monkeypatch, tmp_path)

    exit_code = cli.main([str(device)])

    assert exit_code == cli.EXIT_SUCCESS
    assert events == [
        ("discover", False),
        ("inspect", "lsdvd"),
        ("classify", "Sample Disc"),
        ("rip_disc", str(device), False),
        ("movie_output_path", "Main Feature"),
        ("run_rip_plan", tmp_path / "output.mp4"),
    ]


def test_main_uses_fallback_inspector_when_dvd_missing(monkeypatch, tmp_path) -> None:
    """When :command:`lsdvd` is unavailable, the CLI falls back to ffprobe."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    events = _install_movie_pipeline(monkeypatch, tmp_path, use_fallback=True)

    exit_code = cli.main([str(device)])

    assert exit_code == cli.EXIT_SUCCESS
    assert ("inspect", "ffprobe") in events


def test_main_honors_dry_run_flag(monkeypatch, tmp_path) -> None:
    """The CLI propagates the dry-run flag down to the ripping plans."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    events = _install_movie_pipeline(monkeypatch, tmp_path, dry_run=True)

    exit_code = cli.main(["--dry-run", str(device)])

    assert exit_code == cli.EXIT_SUCCESS
    assert ("rip_disc", str(device), True) in events


def test_main_dry_run_prints_plan(monkeypatch, tmp_path, capsys) -> None:
    """Dry-run mode reports the planned commands instead of executing them."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    title = TitleInfo(label="Main Feature", duration=timedelta(minutes=95))
    disc = DiscInfo(label="Sample Disc", titles=(title,))
    classification = ClassificationResult("movie", (title,))

    tools = InspectionTools(
        dvd=ToolAvailability("lsdvd", "/usr/bin/lsdvd"),
        fallback=None,
        blu_ray=None,
    )

    monkeypatch.setattr(cli, "discover_inspection_tools", lambda: tools)
    monkeypatch.setattr(cli, "inspect_dvd", lambda *_args, **_kwargs: disc)
    monkeypatch.setattr(cli, "classify_disc", lambda *_args, **_kwargs: classification)
    monkeypatch.setattr(
        cli,
        "movie_output_path",
        lambda *_args, **_kwargs: tmp_path / "planned.mp4",
    )
    def unexpected_series_path(*_args, **_kwargs):
        raise AssertionError("Series output path should not be used for movie plans")

    monkeypatch.setattr(cli, "series_output_path", unexpected_series_path)

    def fake_rip_disc(
        device_path,
        classification_value,
        destination_factory,
        *,
        dry_run,
        which=None,
    ) -> tuple[RipPlan, ...]:
        destination = destination_factory(classification_value.episodes[0], None)
        return (
            RipPlan(
                device=device_path,
                title=classification_value.episodes[0],
                destination=destination,
                command=("echo", "rip"),
                will_execute=not dry_run,
            ),
        )

    monkeypatch.setattr(cli, "rip_disc", fake_rip_disc)

    exit_code = cli.main(["--dry-run", str(device)])

    assert exit_code == cli.EXIT_SUCCESS

    captured = capsys.readouterr().out
    assert "[dry-run] Would execute: echo rip" in captured


def test_main_uses_series_output_paths_for_series_classification(
    monkeypatch, tmp_path
) -> None:
    """Series classifications use the series naming helpers for destinations."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    events = _install_series_pipeline(monkeypatch, tmp_path)

    exit_code = cli.main([str(device)])

    assert exit_code == cli.EXIT_SUCCESS
    assert (
        "series_output_path",
        "Sample Series",
        "s01e01",
        "Episode One",
    ) in events
    assert (
        "series_output_path",
        "Sample Series",
        "s01e02",
        "Episode Two",
    ) in events
    run_events = [event for event in events if event[0] == "run_rip_plan"]
    assert [entry[2] for entry in run_events] == ["s01e01", "s01e02"]


def test_main_logs_structured_classification_summary(monkeypatch, tmp_path) -> None:
    """Classification results are emitted as structured log messages."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    _install_series_pipeline(monkeypatch, tmp_path)

    messages: list[str] = []

    class _RecordingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - simple
            messages.append(record.getMessage())

    handler: logging.Handler = _RecordingHandler(level=logging.INFO)
    cli.logger.addHandler(handler)
    try:
        exit_code = cli.main([str(device)])
    finally:
        cli.logger.removeHandler(handler)

    assert exit_code == cli.EXIT_SUCCESS
    assert (
        "EVENT=CLASSIFIED TYPE=series EPISODES=2 LABEL=\"Sample Series\""
        in messages
    )


def test_main_returns_rip_failure_exit_code(monkeypatch, tmp_path, capsys) -> None:
    """When ripping fails the CLI surfaces the message and exit code 2."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    _install_movie_pipeline(monkeypatch, tmp_path)

    def failing_run(_plan: RipPlan):
        raise RipExecutionError("command failed", exit_code=cli.EXIT_RIP_FAILED)

    monkeypatch.setattr(cli, "run_rip_plan", failing_run)

    exit_code = cli.main([str(device)])

    assert exit_code == cli.EXIT_RIP_FAILED

    captured = capsys.readouterr()
    assert "command failed" in captured.err


def test_execute_rip_plans_propagates_rip_exit_code(monkeypatch, tmp_path) -> None:
    """The rip plan executor surfaces the exit code from RipExecutionError."""

    plan = RipPlan(
        device="/dev/sr0",
        title=TitleInfo(label="Sample", duration=timedelta(minutes=5)),
        destination=tmp_path / "sample.mp4",
        command=("echo", "rip"),
        will_execute=False,
    )

    def fail_with_custom_code(_plan: RipPlan):
        raise RipExecutionError("custom failure", exit_code=7)

    monkeypatch.setattr(cli, "run_rip_plan", fail_with_custom_code)

    exit_code = cli._execute_rip_plans((plan,), enable_compression=False)

    assert exit_code == 7


def test_execute_rip_plans_handles_unexpected_exception(monkeypatch, tmp_path, capsys) -> None:
    """Unexpected exceptions during ripping map to the unexpected error exit code."""

    plan = RipPlan(
        device="/dev/sr0",
        title=TitleInfo(label="Sample", duration=timedelta(minutes=5)),
        destination=tmp_path / "sample.mp4",
        command=("echo", "rip"),
        will_execute=False,
    )

    def raise_unexpected(_plan: RipPlan):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "run_rip_plan", raise_unexpected)

    exit_code = cli._execute_rip_plans((plan,), enable_compression=False)

    assert exit_code == cli.EXIT_UNEXPECTED_ERROR
    assert "Unexpected ripping failure" in capsys.readouterr().err


def test_execute_rip_plans_emits_compression_plan(monkeypatch, tmp_path, caplog) -> None:
    """When compression is enabled a HandBrake plan is logged for each rip."""

    destination = tmp_path / "sample.mp4"
    plan = RipPlan(
        device="/dev/sr0",
        title=TitleInfo(label="Sample", duration=timedelta(minutes=5)),
        destination=destination,
        command=("echo", "rip"),
        will_execute=True,
    )

    def fake_run(_plan: RipPlan) -> CompletedProcess[str]:
        destination.write_bytes(b"data")
        return CompletedProcess(plan.command, 0)

    monkeypatch.setattr(cli, "run_rip_plan", fake_run)

    with caplog.at_level("INFO"):
        exit_code = cli._execute_rip_plans((plan,), enable_compression=True)

    assert exit_code == cli.EXIT_SUCCESS
    message = next(msg for msg in caplog.messages if "EVENT=COMPRESS_PLAN" in msg)
    assert "STATUS=ready" in message
    assert str(destination) in message
    assert "HandBrakeCLI" in message
    compressed = destination.with_name(f"{destination.stem}-compressed{destination.suffix}")
    assert str(compressed) in message


def test_execute_rip_plans_marks_dry_run_compression(monkeypatch, tmp_path, caplog) -> None:
    """Dry-run rip plans still surface the compression command with a status."""

    destination = tmp_path / "sample.mp4"
    plan = RipPlan(
        device="/dev/sr0",
        title=TitleInfo(label="Sample", duration=timedelta(minutes=5)),
        destination=destination,
        command=("echo", "rip"),
        will_execute=False,
    )

    def fake_run(_plan: RipPlan) -> None:
        return None

    monkeypatch.setattr(cli, "run_rip_plan", fake_run)

    with caplog.at_level("INFO"):
        exit_code = cli._execute_rip_plans((plan,), enable_compression=True)

    assert exit_code == cli.EXIT_SUCCESS
    message = next(msg for msg in caplog.messages if "EVENT=COMPRESS_PLAN" in msg)
    assert "STATUS=dry-run" in message
    assert str(destination) in message


def test_main_maps_bluray_errors_to_disc_not_detected(
    monkeypatch, tmp_path, capsys
) -> None:
    """Blu-ray support errors are treated as disc detection failures."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    monkeypatch.setattr(
        cli,
        "discover_inspection_tools",
        lambda: InspectionTools(
            dvd=ToolAvailability("lsdvd", "/usr/bin/lsdvd"),
            fallback=None,
            blu_ray=None,
        ),
    )

    def raise_bluray(*_args, **_kwargs):
        raise BluRayNotSupportedError("Blu-ray not supported")

    monkeypatch.setattr(cli, "_inspect_disc", raise_bluray)

    exit_code = cli.main([str(device)])

    assert exit_code == cli.EXIT_DISC_NOT_DETECTED
    assert "Blu-ray not supported" in capsys.readouterr().err


def test_main_errors_when_no_inspection_tools(monkeypatch, tmp_path, capsys) -> None:
    """A helpful error is shown when neither lsdvd nor ffprobe are available."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    def fake_discover() -> InspectionTools:
        return InspectionTools(dvd=None, fallback=None, blu_ray=None)

    monkeypatch.setattr(cli, "discover_inspection_tools", fake_discover)

    exit_code = cli.main([str(device)])

    assert exit_code == cli.EXIT_DISC_NOT_DETECTED

    captured = capsys.readouterr()
    assert "No supported inspection tools" in captured.err


def test_main_errors_when_device_missing(capsys) -> None:
    """A helpful error is emitted when the configured device does not exist."""

    code = cli.main(["/path/that/does/not/exist"])

    assert code == cli.EXIT_DISC_NOT_DETECTED

    captured = capsys.readouterr()
    assert "Error: device path '/path/that/does/not/exist'" in captured.err


def test_main_errors_when_device_unreadable(tmp_path, capsys, monkeypatch) -> None:
    """The CLI refuses to proceed if the device exists but lacks read access."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    monkeypatch.setattr(cli.os, "access", lambda *_: False)

    code = cli.main([str(device)])

    assert code == cli.EXIT_DISC_NOT_DETECTED

    captured = capsys.readouterr()
    assert f"Error: device path '{device}'" in captured.err


def test_main_hides_traceback_for_unexpected_errors(
    tmp_path, monkeypatch, capsys
) -> None:
    """Unexpected exceptions are converted into a friendly error message."""

    device = tmp_path / "device"
    device.write_text("ready", encoding="utf-8")

    _install_movie_pipeline(monkeypatch, tmp_path)

    def raise_unexpected(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "classify_disc", raise_unexpected)

    code = cli.main([str(device)])

    assert code == cli.EXIT_UNEXPECTED_ERROR

    captured = capsys.readouterr()
    assert "An unexpected error occurred" in captured.err
    assert "Traceback" not in captured.err
