# agd

Install, update and combine agentic setups (instructions, agents, skills, hooks) in a project, from git repositories. The default setup is [agentic-defaults](https://github.com/Zejnilovic/agentic-defaults); any repository laid out as a source works, and several can share a project.

agd copies files into your project and records them in `.agd.lock`, which you commit. Updates keep what belongs to the project, and never overwrite a file you changed.

## Install

```bash
brew install zejnilovic/tap/agd
```

Without Homebrew, clone this repository and run `bin/agd`, or put it on your `PATH`. It needs only bash (3.2 or newer, or Git Bash on Windows) and git.

## Quick start

```bash
agd init                               # agentic-defaults, every pack of its latest release
agd init --with flask,react            # only those packs, and the packs they require
agd init your-org/your-setup@1.2.0     # another source, at a release; @<commit> works too
agd status                             # what an update would do
agd update                             # move to the latest release
```

## What stays yours

Updates replace installed files, but keep three parts that belong to the project:

- an agent's `model:` line, so you can choose another model,
- an agent's `tools:` line, to limit what it may use,
- a `## This project` section at the end of a Markdown file, for your own additions.

A file you changed anywhere else is left alone. `agd status` shows it as edited, and as having a newer version when the source changed it too. Then:

- `agd diff <path>` shows your changes and the source's,
- `agd merge <path>` merges the source's changes into yours,
- `agd reset <path>` takes the source's version and drops every project change. `agd reset` does that for every installed file, and keeps only the "This project" section of `AGENTS.md`.

Files agd didn't install are never touched.

## Commands

| Command | Does |
|---|---|
| `agd init [<source>][@<version>\|@<commit>] [--with <packs>] [--yes]` | Installs a source: a GitHub `owner/repo`, a git URL or a local folder. In a project that is set up, adds another source, and asks before it replaces a file you changed. |
| `agd adopt [@<version>]` | Starts managing a copy of agentic-defaults made by hand or by its old `sync.sh`, without changing a file. |
| `agd status [--check]` | Shows what `agd update` would do. `--check` exits 1 when an update is due, for CI. |
| `agd update [--to <version>\|<commit>]` | Updates every source to its latest release, or to the given one. |
| `agd add <pack>`, `agd remove <pack>` | Installs or removes a pack. Removing keeps the files you changed, as yours. |
| `agd diff`, `agd merge`, `agd reset` | Settle a file you changed, as above. |
| `agd source list`, `agd source remove <name>` | List or remove sources. |

`-C <dir>` works in another folder, and `--offline` uses the cached copy of each source instead of fetching it. `agd --help` lists everything.

## Files in your project

- `.agd.lock`: written by agd. It records each source, its version, the packs and every installed file. Commit it, so the team gets the same files.
- `.agd-ignore`: written by you. One path or pattern per line keeps it out of every source; `<source>:<path>` keeps it out of one source, which also decides between two sources that ship the same path.

## Publish your own setup

Any git repository with release tags can be a source: your team's agents and skills, alone or on top of agentic-defaults. [Publish your own agentic setup](docs/sources.md) covers the layout, `packs.txt`, releases, and what projects may change.

## License

[MIT](LICENSE) © Sasa Zejnilovic
