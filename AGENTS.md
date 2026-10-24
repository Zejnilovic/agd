# Maintaining agd

agd is one bash script, `bin/agd`, that installs and updates agentic setups from git repositories (sources) into projects. agentic-defaults (github.com/Zejnilovic/agentic-defaults) is its default source and its main user.

## Before committing

- Run `python3 -m unittest discover -s tests`. CI runs it on Linux and macOS.
- Changes are test-first: add or change a test in `tests/test_agd.py`, watch it fail, then change the script.
- Tests never use the network: they build temporary source repositories and point `AGD_CACHE` at a temporary folder. To fake a GitHub URL, set git's `url.<path>.insteadOf` through `GIT_CONFIG_*` variables.
- Try a change that affects installs on real projects, for example with agentic-defaults as the source.

## Script rules

- Bash 3.2 (macOS) and Git Bash (Windows): no associative arrays, `mapfile` or `${var,,}`. Keep state in temporary files and line-based lists. The tests run the script with `/bin/bash` on macOS.
- Only git and POSIX tools. Detect optional tools with `command -v`.
- agd never runs code from a source. It only copies files.
- Read-only commands (`status`, `diff`, `source list`) write nothing in the project. Commands that delete a project's text (`reset`) ask first, and need `--yes` without a terminal.

## Contracts

Projects and sources depend on these. Changing one needs a major version, and a migration or manual steps in the notes:

- the lock format (`agd-lock 1` in `.agd.lock`) and the ignore file (`.agd-ignore`, plus reading `.agentic-defaults-ignore`),
- the source layout: `v<major.minor.patch>` tags, `kit/` or the `root` in `packs.txt`, and `packs.txt` itself (`min-agd`, `pack ... requires ...`, `<source>:<pack>`),
- the project parts: an agent's `model:` and `tools:` lines, and a closing `## This project` section.

## Versions and releases

- `VERSION` and the `version=` line in `bin/agd` always match; `bash scripts/bump.sh <version>` sets both and adds an "(unreleased)" entry to `CHANGELOG.md`. Replace its TODO with what changed.
- A source's `min-agd` names the oldest agd that can install it. Release agd before a source that needs the new version.
