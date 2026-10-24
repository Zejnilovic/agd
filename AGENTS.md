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
- `install.sh` follows the same rules. Its tests fake GitHub too.

## Docs

- The site, https://zejnilovic.github.io/agd, is built from `docs/` and `mkdocs.yml` by the Docs workflow on every push to `main`. `README.md` is its short version.
- Change the docs with the behavior, in the same commit. Show real output: run the commands rather than writing it by hand.
- `mkdocs build --strict` must pass (`pip install -r docs/requirements.txt`); it fails on a broken link.
- People copy these into their scripts, so keep them working: the install script's URL, `https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh`, and the release files `agd` and `SHA256SUMS` under `releases/latest/download/`.

## Contracts

Projects and sources depend on these. Changing one needs a major version, and a migration or manual steps in the notes:

- the lock format (`agd-lock 1` in `.agd.lock`) and the ignore file (`.agd-ignore`, plus reading `.agentic-defaults-ignore`),
- the source layout: `v<major.minor.patch>` tags, `kit/` or the `root` in `packs.txt`, and `packs.txt` itself (`min-agd`, `pack ... requires ...`, `<source>:<pack>`),
- the project parts: an agent's `model:` and `tools:` lines, and a closing `## This project` section.

## Versions and releases

- `VERSION` and the `version=` line in `bin/agd` always match; `bash scripts/bump.sh <version>` sets both and adds an "(unreleased)" entry to `CHANGELOG.md`. Replace its TODO with what changed.
- A source's `min-agd` names the oldest agd that can install it. Release agd before a source that needs the new version.
- To release: push everything to `main`, then run the **Release** workflow (Actions tab, or `gh workflow run release.yml`), first with `-f dry_run=true`. It dates the changelog entry (`scripts/release.sh`), tags `v<version>`, creates the GitHub release with `agd-<version>.tar.gz`, the plain `agd` and their `SHA256SUMS`, writes `Formula/agd.rb` in `Zejnilovic/homebrew-tap` (`scripts/formula.sh`, pushed with the `HOMEBREW_TAP_TOKEN` secret), and then installs the release from the tap on macOS, and with `install.sh` and the plain download on Linux, macOS and Windows. Don't release by hand.
