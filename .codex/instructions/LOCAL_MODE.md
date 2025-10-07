# Local Sandbox Mode

This repository operates as a contained training sandbox for Codex agents. Treat every assignment as a self-guided tutorial that must be completed entirely within this project.

## Isolation requirements

- **Do not import or depend on external repositories.** All code, assets, and examples must originate from `codex-hello-world` itself. Mentions of other projects (such as `discripper`) are conceptual only and must not drive implementation decisions.
- **Work only on local files.** Tasks should update documentation, markdown guides, or configuration files inside this repository. Avoid cross-repo references, shared modules, or remote resources.
- **Keep experiments scoped.** Prototype safely within the sandbox, and reset state before finishing a task. No persistent services or network integrations should be introduced here.

## Workflow discipline

- Follow the developer workflow defined in `.codex/instructions/3-dev_process.md`.
- Respect all local gates, including `ruff`, `pytest`, and any others listed in `.codex/instructions/LOCAL_GATES.md`. They exist to reinforce clean habits even in tutorial mode.
- Document updates clearly so future Codex prompts can reference this guide for sandbox hygiene.

By adhering to these boundaries we keep the training environment predictable, reproducible, and safe for every Codex run.
