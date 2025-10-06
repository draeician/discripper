# discripper

`discripper` is a command-line utility for inspecting optical discs and planning ripping workflows. The tool will detect whether a disc contains a movie or a TV series, recommend output naming, and coordinate ripping tools so collections stay organized.

## Status

This repository is under active development. Core functionality such as configuration loading, device inspection, and ripping orchestration is tracked in `PRD.md` and `TASKS.md`.

## Getting Started

```bash
pip install -e .
```

Once the CLI is implemented you will be able to run:

```bash
discripper --help
```

Configuration will default to `~/.config/discripper.yaml` with CLI flags to override key settings. See `PRD.md` for the planned feature roadmap.

## Ripping prerequisites

The initial ripping path relies on [`ffmpeg`](https://ffmpeg.org/) being available on the system `PATH`.  The command reads
directly from the supplied device node (for example `/dev/sr0`) and writes an MP4 file to the requested destination.  CSS or
advanced Blu-ray decryption is **not** handled by `discripper`; external tools or system packages must be used when discs
require additional decoding support.

## Contributing

1. Check the next open item in `TASKS.md`.
2. Implement the change with tests.
3. Run the local verification gates documented in `.codex/instructions/LOCAL_GATES.md`.
4. Open a pull request linking the task ID.

## License

This project is licensed under the terms of the [MIT License](LICENSE).
