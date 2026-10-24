# Contributing to agd

Thanks for helping. Bug reports, ideas, documentation fixes and code are all welcome.

## Report a bug or ask for something

[Open an issue](https://github.com/Zejnilovic/agd/issues/new/choose). For a bug, include the command, its output, `agd --version`, your OS and `bash --version`. If the source is public, name it; a source's `packs.txt` and tags often explain what agd did.

## How agd is built

agd is one bash script, [`bin/agd`](bin/agd). [`AGENTS.md`](AGENTS.md) has the rules for anyone changing it, person or coding agent. In short:

- **Test first.** Add or change a test in [`tests/test_agd.py`](tests/test_agd.py), watch it fail, then change the script. The tests build temporary source repositories and never use the network.
- **Bash 3.2 and Git Bash.** No associative arrays, `mapfile` or `${var,,}`. Only git and POSIX tools.
- **agd never runs code from a source.** It only copies files.
- **Read-only commands write nothing,** and commands that drop a project's changes ask first.
- **Contracts need a major version:** the lock format, `.agd-ignore`, the source layout and `packs.txt`, and the project parts of a file.

Run the tests, as CI does on Linux and macOS:

```bash
python3 -m unittest discover -s tests
```

For a change that affects installs, also try it on a real project, for example with agentic-defaults as the source.

## Documentation

The site at https://zejnilovic.github.io/agd is built from [`docs/`](docs/) and [`mkdocs.yml`](mkdocs.yml). Preview it while you write:

```bash
python3 -m venv .venv && .venv/bin/pip install -r docs/requirements.txt
.venv/bin/mkdocs serve
```

Keep the pages true to the script: show real output, and change the docs in the same pull request as the behavior. `mkdocs build --strict` must pass; it fails on a broken link.

## Pull requests

- Keep one change per pull request, with its tests and docs.
- Add a line describing it to the "(unreleased)" entry at the top of [`CHANGELOG.md`](CHANGELOG.md). If there is none, the maintainer adds the next version with `bash scripts/bump.sh`.
- The maintainer releases with the Release workflow; see "Versions and releases" in `AGENTS.md`.
