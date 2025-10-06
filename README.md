# discripper

`discripper` is a command-line utility for inspecting optical discs and planning ripping workflows. The tool will detect whether a disc contains a movie or a TV series, recommend output naming, and coordinate ripping tools so collections stay organized.

## Status

This repository is under active development. Core functionality such as configuration loading, device inspection, and ripping orchestration is tracked in `PRD.md` and `TASKS.md`.

## Prerequisites

`discripper` orchestrates several command-line tools that are typically available from Debian and Ubuntu package repositories. Install them before running the CLI:

```bash
sudo apt update
sudo apt install ffmpeg lsdvd dvdbackup
```

* `ffmpeg` provides the ripping backend and includes `ffprobe` for fallback inspection.
* `lsdvd` supplies the primary DVD title/duration metadata.
* `dvdbackup` is used when available to clone discs prior to transcoding.

Blu-ray discs that require decryption or CSS-protected DVDs may need additional third-party tooling; `discripper` does not perform circumvention.

## Installation

Install the project in editable mode while developing or testing:

```bash
pip install -e .
```

Alternatively, install into an isolated environment with [`pipx`](https://pypa.github.io/pipx/):

```bash
pipx install --suffix=@dev \
  --force --pip-args "--editable ." \
  .
```

After installation the `discripper` entry point is available on your `PATH`.

Configuration defaults to `~/.config/discripper.yaml`, and CLI flags can override key settings. See `PRD.md` for the broader feature roadmap.

## Usage

`discripper` inspects the provided optical device, classifies the contents, and plans rips into the configured output directory (default: `~/Videos`). The CLI exposes a consistent workflow for both movies and series.

### Movie workflow

Insert the disc and run:

```bash
discripper /dev/sr0
```

`discripper` discovers the primary title, logs a `TYPE=movie` classification event, and rips the main feature to `<output_directory>/<movieTitle>.mp4`.

### Series workflow

When the disc contains episodic content, the CLI automatically infers episode ordering and creates per-episode files. For example:

```bash
discripper /dev/sr0 --config ~/.config/discripper.yaml
```

The command emits structured logs such as `EVENT=CLASSIFIED TYPE=series EPISODES=6` and writes files following the pattern `<seriesName>/<seriesName>-s01eNN_<title>.mp4` inside the configured output directory.

## Dry-run mode

Use `--dry-run` when you want to verify the rip plan without performing any writes:

```bash
discripper /dev/sr0 --dry-run --verbose
```

The command prints the planned titles and destinations while leaving the filesystem untouched—ideal for validating configuration, naming rules, or tool availability.

## Exit codes

`discripper` communicates high-level failure modes via conventional process exit
codes:

| Code | Meaning                               |
| ---- | ------------------------------------- |
| 0    | Success                               |
| 1    | Disc could not be detected or read    |
| 2    | Ripping failed after planning         |
| 3    | Unexpected internal error during rip  |

Non-zero exit codes are accompanied by human-readable error messages on
standard error so scripts can both log and react to failures.

## Contributing

1. Check the next open item in `TASKS.md`.
2. Implement the change with tests.
3. Run the local verification gates documented in `.codex/instructions/LOCAL_GATES.md`.
4. Open a pull request linking the task ID.

## License

This project is licensed under the terms of the [MIT License](LICENSE).
