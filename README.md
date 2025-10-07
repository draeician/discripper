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

Use `lsdvd` to confirm the optical drive path before running `discripper`:

```bash
lsdvd -Oy -c /dev/sr0
```

Most Linux distributions expose the optical drive at `/dev/sr0`, but some utilities expect `/dev/dvd`. If `lsdvd` defaults to `/dev/dvd`, create a symlink that points to the actual device:

```bash
sudo ln -s /dev/sr0 /dev/dvd
```

`discripper` also accepts an explicit device argument, so you can pass a different path when launching the CLI (for example, `discripper /dev/sr1`).

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

## Configuration

`discripper` loads its settings from a YAML file. By default the loader targets
`~/.config/discripper.yaml`; pass `--config <path>` to point the CLI at an
alternate file. The override works for both absolute and relative paths:

```bash
discripper --config ./discripper.dev.yaml /dev/sr0
```

### Schema overview

The configuration file must define the following structure. Types are expressed
in YAML terms—strings may include `~` for home-directory expansion.

| Key | Type | Description |
| --- | ---- | ----------- |
| `output_directory` | string | Destination directory for ripped media (default: `~/Videos`). |
| `compression` | boolean | Enable the optional post-rip compression pipeline. |
| `dry_run` | boolean | Force dry-run behaviour regardless of the CLI flag. |
| `classification.movie_main_title_minutes` | number | Minimum runtime to treat a title as the movie feature. |
| `classification.movie_total_runtime_minutes` | number | Runtime threshold for classifying a disc as a movie. |
| `classification.series_min_duration_minutes` | number | Shortest duration considered an episode. |
| `classification.series_max_duration_minutes` | number | Longest duration considered an episode. |
| `classification.series_gap_limit` | number | Allowed variance (0-1) between episode durations. |
| `naming.separator` | string | Separator inserted between filename segments. |
| `naming.lowercase` | boolean | When true, lowercase all generated paths. |
| `naming.episode_title_strategy` | string | Episode title inference strategy (`label`, `episode-number`, or `module:callable`). |
| `logging.level` | string or integer | Logging level (e.g. `INFO`, `DEBUG`, or `20`). |

The `naming.episode_title_strategy` option controls how episode names are inferred for
series discs. Use the default `label` strategy to keep the source title labels, switch to
`episode-number` for generic `Episode 01` style names, or point to a custom callable using
the `module:callable` notation to plug in project-specific logic.

### Defaults & overrides

`discripper` resolves configuration in three tiers: built-in defaults,
values from the active YAML file, and finally CLI flags. Use the table below
to verify each setting's default and the available override surface.

| Setting | Default | Config key | CLI override | Notes |
| --- | --- | --- | --- | --- |
| Configuration file path | `~/.config/discripper.yaml` | — | `--config` | Expands `~`; accepts relative paths. |
| `output_directory` | `~/Videos` | `output_directory` | — | Created automatically. |
| `compression` | `false` | `compression` | — | Emits HandBrake commands. |
| `dry_run` | `false` | `dry_run` | `--dry-run`, `--simulate` | CLI flags override config. |
| `classification.movie_main_title_minutes` | `60` | `classification.movie_main_title_minutes` | — | Minutes for main title. |
| `classification.movie_total_runtime_minutes` | `180` | `classification.movie_total_runtime_minutes` | — | Max runtime for movies. |
| `classification.series_min_duration_minutes` | `20` | `classification.series_min_duration_minutes` | — | Episode minimum length. |
| `classification.series_max_duration_minutes` | `60` | `classification.series_max_duration_minutes` | — | Episode maximum length. |
| `classification.series_gap_limit` | `0.2` | `classification.series_gap_limit` | — | Allowed duration variance. |
| `naming.separator` | `_` | `naming.separator` | — | Filename segment joiner. |
| `naming.lowercase` | `false` | `naming.lowercase` | — | Lowercases destination paths. |
| `naming.episode_title_strategy` | `label` | `naming.episode_title_strategy` | — | Selects episode naming strategy. |
| `logging.level` | `INFO` | `logging.level` | `--verbose` | Flag forces `DEBUG` logging. |
| `logging.file` | None | `logging.file` | `--log-file` | Optional log file path; leave unset to disable. |

### Example configuration

```yaml
# ~/.config/discripper.yaml
output_directory: ~/Videos/discripper
compression: false
dry_run: false
classification:
  movie_main_title_minutes: 60
  movie_total_runtime_minutes: 180
  series_min_duration_minutes: 20
  series_max_duration_minutes: 60
  series_gap_limit: 0.2
naming:
  separator: _
  lowercase: false
  episode_title_strategy: label
logging:
  level: INFO
  file: null
```

When `compression` is set to `true` the CLI logs a ready-to-run
`HandBrakeCLI` command for each ripped file. The hook does not execute the
command automatically; it simply assembles a safe default that you can copy
once the rip completes. Leave the option at its default of `false` to skip
generating the compression plans.

Set `logging.file` to a writable path—or pass `--log-file` on the CLI—to mirror
console output into a persistent log file.

CLI flags such as `--dry-run` and `--verbose` take precedence over values in the
configuration file, allowing quick one-off overrides without editing disk
settings.

## Usage

`discripper` inspects the provided optical device, classifies the contents, and plans rips into the configured output directory (default: `~/Videos`). The CLI exposes a consistent workflow for both movies and series.

### CLI help

Inspect the built-in help to review all supported flags and arguments:

```console
$ discripper --help
usage: discripper [-h] [--config CONFIG_PATH] [--verbose] [--dry-run] [device]

discripper command-line interface

positional arguments:
  device                Path to the optical media device (default: /dev/sr0).

options:
  -h, --help            show this help message and exit
  --config CONFIG_PATH  Path to the configuration file to use.
  --verbose             Enable verbose (DEBUG) logging output.
  --dry-run             Perform a dry run without executing side effects.
```

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

## Output naming examples

Run the simulation fixtures to see the slugged filenames that `discripper`
produces while respecting the PRD conventions:

```bash
bash scripts/demo.sh
```

The default configuration targets `~/Videos`, so a movie disc resolves to the
disc-title slug with numbered tracks:

```
~/Videos/simulation-feature-film/
└── simulation-feature-film_track01.mp4
```

Series discs follow the `{slug}/{slug}_trackNN.mp4` structure, where the slug
comes from the provided or detected disc title:

```
~/Videos/simulation-limited-series/
├── simulation-limited-series_track01.mp4
├── simulation-limited-series_track02.mp4
├── simulation-limited-series_track03.mp4
└── simulation-limited-series_track04.mp4
```

These examples come directly from the `samples/simulated_*.json` fixtures and are asserted by `tests/test_samples_naming.py`, keeping the documentation in lockstep with the implementation.

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

## Troubleshooting

Jump directly to a common issue:

- [Device not detected (`exit code 1`)](#device-not-detected-exit-code-1)
- [Required tools missing from `PATH`](#required-tools-missing-from-path)
- [Output directory cannot be created](#output-directory-cannot-be-created)

### Device not detected (`exit code 1`)

If the CLI exits with code 1, verify that the optical drive path is correct
(`/dev/sr0` by default) and readable by your user. You may need to run
`sudo usermod -a -G cdrom $USER` and log out/in so the process can access the
device without elevated privileges.

### Required tools missing from `PATH`

`discripper` depends on utilities such as `ffmpeg`, `lsdvd`, and `dvdbackup`.
If inspection fails with a "tool not found" error, re-run the install commands
from [Prerequisites](#prerequisites) and ensure the binaries resolve via
`which <tool>`.

### Output directory cannot be created

When the configured output directory is unwritable, the rip plan will abort
before running external tools. Double-check the `output_directory` setting in
your config file, ensure the parent folders exist, and confirm you have write
permissions (e.g. `chmod u+w <path>`).

## Contributing

1. Check the next open item in `TASKS.md`.
2. Implement the change with tests.
3. Run the local verification gates documented in `.codex/instructions/LOCAL_GATES.md`.
4. Open a pull request linking the task ID.

## License

This project is licensed under the terms of the [MIT License](LICENSE).
