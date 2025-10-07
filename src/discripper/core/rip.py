"""Ripping helpers for turning inspected titles into actionable plans."""

from __future__ import annotations

import logging
import queue
import shlex
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from os import fspath
from pathlib import Path
from shutil import which as default_which
from subprocess import (
    PIPE,
    CalledProcessError,
    CompletedProcess,
    Popen,
    run as subprocess_run,
)
from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from . import ClassificationResult, TitleInfo


logger = logging.getLogger(__name__)


def _log_rip_failure(plan: RipPlan, reason: str, exit_code: int) -> None:
    """Emit a structured log entry describing a failed rip attempt."""

    logger.error(
        'EVENT=RIP_FAILED FILE="%s" EXIT_CODE=%d REASON="%s"',
        plan.destination,
        exit_code,
        reason,
    )


@dataclass(frozen=True, slots=True)
class RipPlan:
    """Structured description of how a single title should be ripped."""

    device: str
    title: "TitleInfo"
    destination: Path
    command: Tuple[str, ...]
    will_execute: bool


class RipExecutionError(RuntimeError):
    """Error raised when executing an external ripping command fails."""

    exit_code: int

    def __init__(self, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _ffmpeg_command(device: str, destination: Path) -> Tuple[str, ...]:
    return (
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "error",
        "-progress",
        "pipe:2",
        "-i",
        device,
        str(destination),
    )


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class _ProgressReporter:
    def handle_line(self, source: str, line: str) -> None:
        pass

    def handle_idle(self) -> None:
        pass

    def finalize(self, success: bool) -> None:
        pass


class _FfmpegProgressReporter(_ProgressReporter):
    def __init__(self, plan: RipPlan) -> None:
        self._duration_seconds = plan.title.duration.total_seconds()
        self._have_duration = self._duration_seconds > 0
        self._start_time = time.monotonic()
        self._frame_state: dict[str, str] = {}
        self._last_pct: float | None = None

    def handle_line(self, source: str, line: str) -> None:
        if source != "stderr":
            return

        if "=" not in line:
            return

        key, value = line.split("=", 1)
        self._frame_state[key] = value
        if key == "progress":
            self._emit_progress(value)
            self._frame_state.clear()

    def finalize(self, success: bool) -> None:
        if success and self._have_duration and (self._last_pct or 0) < 100:
            elapsed = time.monotonic() - self._start_time
            logger.info(
                "EVENT=PROGRESS BACKEND=ffmpeg PCT=100.0 ELAPSED=%s",
                _format_duration(elapsed),
            )

    def _emit_progress(self, progress_state: str) -> None:
        now = time.monotonic()
        elapsed = now - self._start_time
        out_time_ms = self._parse_int(self._frame_state.get("out_time_ms"))
        total_size = self._parse_int(self._frame_state.get("total_size"))
        speed_label = self._frame_state.get("speed")
        speed_value = self._parse_speed(speed_label) if speed_label else None

        pct_value: float | None = None
        eta_value: Optional[str] = None
        spinner = False

        if self._have_duration and out_time_ms is not None:
            pct_value = min(
                100.0,
                (out_time_ms / (self._duration_seconds * 1000)) * 100,
            )
            remaining_seconds = max(
                self._duration_seconds - (out_time_ms / 1000),
                0.0,
            )
            if progress_state == "end":
                pct_value = 100.0
                remaining_seconds = 0.0

            if speed_value and speed_value > 0:
                eta_value = _format_duration(remaining_seconds / speed_value)
            elif remaining_seconds:
                eta_value = _format_duration(remaining_seconds)
        elif not self._have_duration:
            spinner = True

        fields = ["EVENT=PROGRESS", "BACKEND=ffmpeg"]
        if pct_value is not None:
            fields.append(f"PCT={pct_value:.1f}")
            self._last_pct = pct_value
        if eta_value:
            fields.append(f"ETA={eta_value}")
        if speed_label:
            fields.append(f"SPEED={speed_label}")
        fields.append(f"ELAPSED={_format_duration(elapsed)}")
        if total_size is not None:
            fields.append(f"BYTES_DONE={total_size}")
        if spinner:
            fields.append("SPINNER=true")

        logger.info(" ".join(fields))

        if progress_state == "end" and pct_value is None and self._have_duration:
            # Duration known but out_time_ms missing, still emit 100% once.
            fields = [
                "EVENT=PROGRESS",
                "BACKEND=ffmpeg",
                "PCT=100.0",
                f"ELAPSED={_format_duration(elapsed)}",
            ]
            logger.info(" ".join(fields))
            self._last_pct = 100.0

    @staticmethod
    def _parse_int(raw: Optional[str]) -> Optional[int]:
        if raw is None:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    @staticmethod
    def _parse_speed(raw: str) -> Optional[float]:
        value = raw.rstrip("x") if raw.endswith("x") else raw
        try:
            return float(value)
        except ValueError:
            return None


def _probe_dvd_volume_size(device: str) -> Optional[int]:
    try:
        result = subprocess_run(
            ("isoinfo", "-d", "-i", device),
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, CalledProcessError, OSError):
        return None

    for line in result.stdout.splitlines():
        if "Volume size is:" in line:
            parts = line.strip().split(":", 1)
            if len(parts) != 2:
                continue
            try:
                blocks = int(parts[1].strip())
            except ValueError:
                continue
            return blocks * 2048
    return None


def _directory_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for entry in path.rglob("*"):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except OSError:
                continue
    return total


class _DvdBackupProgressReporter(_ProgressReporter):
    def __init__(self, plan: RipPlan) -> None:
        self._target_dir = _dvdbackup_output_directory(plan)
        self._total_bytes = _probe_dvd_volume_size(plan.device)
        self._last_emit = 0.0
        self._last_bytes = -1
        self._start = time.monotonic()

    def handle_idle(self) -> None:
        now = time.monotonic()
        if now - self._last_emit < 0.3:
            return
        self._emit_progress()
        self._last_emit = now

    def finalize(self, success: bool) -> None:
        if success:
            self._emit_progress(force=True)

    def _emit_progress(self, force: bool = False) -> None:
        bytes_done = _directory_size(self._target_dir)
        if not force and bytes_done == self._last_bytes:
            return

        self._last_bytes = bytes_done
        elapsed = time.monotonic() - self._start
        fields = [
            "EVENT=PROGRESS",
            "BACKEND=dvdbackup",
            f"BYTES_DONE={bytes_done}",
            f"ELAPSED={_format_duration(elapsed)}",
        ]

        if self._total_bytes is not None and self._total_bytes > 0:
            fields.append(f"BYTES_TOTAL={self._total_bytes}")
            pct = min(100.0, (bytes_done / self._total_bytes) * 100)
            fields.append(f"PCT={pct:.1f}")
        else:
            fields.append("BYTES_TOTAL=unknown")
            fields.append("SPINNER=true")

        logger.info(" ".join(fields))


def _dvdbackup_output_directory(plan: RipPlan) -> Path:
    command = plan.command
    try:
        output_index = command.index("-o")
        label_index = command.index("-n")
    except ValueError:
        return plan.destination.parent

    output_dir = Path(command[output_index + 1])
    label = command[label_index + 1]
    return output_dir / label


def _create_progress_reporter(plan: RipPlan) -> Optional[_ProgressReporter]:
    backend = plan.command[0]
    if backend == "ffmpeg":
        return _FfmpegProgressReporter(plan)
    if backend == "dvdbackup":
        return _DvdBackupProgressReporter(plan)
    return None


def _execute_plan_with_progress(
    plan: RipPlan, *, popen: Callable[..., Popen[Any]]
) -> CompletedProcess[Any]:
    progress = _create_progress_reporter(plan)

    try:
        process = popen(
            plan.command,
            stdout=PIPE,
            stderr=PIPE,
            bufsize=1,
            text=True,
        )
    except FileNotFoundError:
        raise

    stdout_finished = process.stdout is None
    stderr_finished = process.stderr is None
    line_queue: queue.Queue[tuple[str, Optional[str]]] = queue.Queue()

    threads: list[threading.Thread] = []

    def _reader(stream_name: str, stream: Any) -> None:
        try:
            for raw_line in stream:
                line_queue.put((stream_name, raw_line.rstrip("\r\n")))
        finally:
            line_queue.put((stream_name, None))

    if process.stdout is not None:
        thread = threading.Thread(
            target=_reader, args=("stdout", process.stdout), name="rip-stdout-reader"
        )
        thread.start()
        threads.append(thread)
    if process.stderr is not None:
        thread = threading.Thread(
            target=_reader, args=("stderr", process.stderr), name="rip-stderr-reader"
        )
        thread.start()
        threads.append(thread)

    returncode: Optional[int] = None

    try:
        while True:
            if stdout_finished and stderr_finished and line_queue.empty():
                if process.poll() is not None:
                    break

            try:
                source, line = line_queue.get(timeout=0.25)
            except queue.Empty:
                if progress is not None:
                    try:
                        progress.handle_idle()
                    except Exception:
                        logger.debug("Progress idle handler failed", exc_info=True)
                continue

            if line is None:
                if source == "stdout":
                    stdout_finished = True
                elif source == "stderr":
                    stderr_finished = True
                continue

            logger.debug("%s: %s", source.upper(), line)
            if progress is not None:
                try:
                    progress.handle_line(source, line)
                except Exception:
                    logger.debug("Progress line handler failed", exc_info=True)

        returncode = process.wait()
    finally:
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        for thread in threads:
            thread.join(timeout=1)

    if returncode is None:
        returncode = process.wait()

    if progress is not None:
        try:
            progress.finalize(returncode == 0)
        except Exception:
            logger.debug("Progress finalizer failed", exc_info=True)

    if returncode != 0:
        raise CalledProcessError(returncode, plan.command)

    return CompletedProcess(plan.command, returncode)


def _dvdbackup_command(device: str, title_info: "TitleInfo", destination: Path) -> Tuple[str, ...]:
    output_dir = destination.parent
    label = destination.stem or title_info.label or "title"
    return (
        "dvdbackup",
        "-i",
        device,
        "-o",
        str(output_dir),
        "-n",
        label,
        "-F",
    )


def _select_rip_command(
    device: str,
    title_info: "TitleInfo",
    destination: Path,
    which: Callable[[str], Optional[str]],
) -> Tuple[str, ...]:
    if which("dvdbackup"):
        return _dvdbackup_command(device, title_info, destination)

    if which("ffmpeg"):
        return _ffmpeg_command(device, destination)

    raise RuntimeError("No supported ripping tools found on PATH")


def rip_title(
    device: str | Path,
    title_info: "TitleInfo",
    dest_path: str | Path,
    *,
    dry_run: bool = False,
    which: Callable[[str], Optional[str]] = default_which,
) -> RipPlan:
    """Return the rip plan for ``title_info`` from ``device`` to ``dest_path``.

    The function does not execute any external commands yet; it only prepares
    the command that future tasks will run.  When ``dry_run`` is :data:`True`,
    the plan records that the command should not be executed.
    """

    device_path = fspath(device)
    destination = Path(dest_path)

    command = _select_rip_command(device_path, title_info, destination, which)

    return RipPlan(
        device=device_path,
        title=title_info,
        destination=destination,
        command=command,
        will_execute=not dry_run,
    )


def run_rip_plan(
    plan: RipPlan,
    *,
    popen: Callable[..., Popen[Any]] = Popen,
) -> Optional[CompletedProcess[Any]]:
    """Execute *plan* using the configured external command.

    The :class:`RipPlan` returned by :func:`rip_title` describes a full command
    tuple that reads from the optical device and writes to the destination.  This
    helper runs that command by spawning a :class:`subprocess.Popen` instance
    with line-buffered text streams so progress output can be consumed while the
    process executes.  Non-zero exit codes still result in an exception being
    raised for callers.

    When ``plan.will_execute`` is :data:`False` (e.g., for ``--dry-run``), the
    function does nothing and returns :data:`None`.
    """

    if not plan.will_execute:
        print(f"[dry-run] Would execute: {shlex.join(plan.command)}")
        logger.info('EVENT=RIP_SKIPPED FILE="%s" REASON=dry-run', plan.destination)
        return None

    if plan.destination.exists():
        logger.warning(
            'EVENT=RIP_GUARD FILE="%s" REASON=destination-exists',
            plan.destination,
        )
        raise RipExecutionError(
            (
                "Refusing to overwrite existing file "
                f"'{plan.destination}'. Remove the file or choose a different output path."
            ),
            exit_code=2,
        )

    plan.destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = _execute_plan_with_progress(plan, popen=popen)

        size_bytes: Optional[int]
        try:
            size_bytes = plan.destination.stat().st_size
        except FileNotFoundError:
            size_bytes = None
        except OSError:
            size_bytes = None

        if size_bytes is not None:
            logger.info(
                'EVENT=RIP_DONE FILE="%s" BYTES=%d STATUS=success',
                plan.destination,
                size_bytes,
            )
        else:
            logger.info(
                'EVENT=RIP_DONE FILE="%s" BYTES=unknown STATUS=success',
                plan.destination,
            )

        return result
    except FileNotFoundError as exc:  # pragma: no cover - defensive on Python <3.11
        _log_rip_failure(plan, "tool-not-found", 2)
        raise RipExecutionError(
            f"Ripping tool '{plan.command[0]}' was not found on PATH.",
            exit_code=2,
        ) from exc
    except PermissionError as exc:
        _log_rip_failure(plan, "permission-denied", 2)
        raise RipExecutionError(
            f"Permission denied while executing '{plan.command[0]}'.",
            exit_code=2,
        ) from exc
    except CalledProcessError as exc:
        _log_rip_failure(plan, f"subprocess-exit-{exc.returncode}", 2)
        raise RipExecutionError(
            (
                "Ripping command failed with exit code "
                f"{exc.returncode}: {' '.join(plan.command)}"
            ),
            exit_code=2,
        ) from exc
    except OSError as exc:  # pragma: no cover - generic OS error guard
        _log_rip_failure(plan, exc.strerror or str(exc), 2)
        raise RipExecutionError(
            f"Unexpected I/O error executing '{plan.command[0]}': {exc.strerror or exc}.",
            exit_code=2,
        ) from exc


def rip_disc(
    device: str | Path,
    classification: "ClassificationResult",
    destination_factory: Callable[["TitleInfo", str | None, int], str | Path],
    *,
    dry_run: bool = False,
    which: Callable[[str], Optional[str]] = default_which,
) -> Tuple[RipPlan, ...]:
    """Return rip plans for all titles selected by *classification*.

    The *destination_factory* callback receives each :class:`TitleInfo` and the
    associated episode code (``s01eNN``) when available.  It must return the
    output path where the resulting file should be written.  The function does
    not perform any I/O; it simply prepares plans by delegating to
    :func:`rip_title` for every relevant title.
    """

    episodes = classification.episodes
    episode_codes: Tuple[str | None, ...]
    if classification.episode_codes:
        episode_codes = classification.episode_codes
    else:
        episode_codes = tuple(None for _ in episodes)

    plans = []
    for index, (title, code) in enumerate(zip(episodes, episode_codes), start=1):
        destination = destination_factory(title, code, index)
        plans.append(
            rip_title(
                device,
                title,
                destination,
                dry_run=dry_run,
                which=which,
            )
        )

    return tuple(plans)

