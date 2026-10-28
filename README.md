<p align="center">
  <a href="https://zejnilovic.github.io/agd/"><img src="docs/assets/logo.svg" alt="" width="72" height="72"></a>
</p>

<h1 align="center">agd</h1>

<p align="center">
  <strong>Your agentic setup, versioned like a dependency.</strong><br>
  Install and update instructions, agents, skills and hooks from git repositories,<br>
  without overwriting what your project changed.
</p>

<p align="center">
  <a href="https://github.com/Zejnilovic/agd/actions/workflows/check.yml"><img src="https://github.com/Zejnilovic/agd/actions/workflows/check.yml/badge.svg" alt="Check agd"></a>
  <a href="https://github.com/Zejnilovic/agd/releases/latest"><img src="https://img.shields.io/github/v/release/Zejnilovic/agd?sort=semver&color=d33122" alt="Latest release"></a>
  <a href="https://zejnilovic.github.io/agd/"><img src="https://img.shields.io/badge/docs-zejnilovic.github.io%2Fagd-123a69" alt="Documentation"></a>
  <img src="https://img.shields.io/badge/needs-bash%203.2%2B%20and%20git-123a69" alt="Needs bash 3.2+ and git">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Zejnilovic/agd?color=123a69" alt="MIT license"></a>
</p>

<p align="center">
  <a href="https://zejnilovic.github.io/agd/">Docs</a> ·
  <a href="https://zejnilovic.github.io/agd/install/">Install</a> ·
  <a href="https://zejnilovic.github.io/agd/quick-start/">Quick start</a> ·
  <a href="https://zejnilovic.github.io/agd/concepts/">How it works</a> ·
  <a href="docs/sources.md">Publish your own setup</a>
</p>

---

A good agentic setup takes work: `AGENTS.md`, agents for each role, skills, hooks. You want it in every project, and you want every project to get its improvements. Copies drift, and copying a new version over an old one wipes out what each project changed, so nobody updates.

agd keeps a setup in a git repository, installs it into your projects at a version, and updates it while keeping each project's own changes. The default setup is [agentic-defaults](https://github.com/Zejnilovic/agentic-defaults); any repository laid out as a source works, and several can share a project.

```console
$ agd init @0.2.0
Installed agentic-defaults 0.2.0: 36 files from the packs core.
Commit .agd.lock along with the new files.

$ agd status        # weeks later: you chose opus for the reviewer, and edited a skill
agentic-defaults 0.2.0 is installed, and 0.3.0 is available: run agd update.
notes    https://github.com/Zejnilovic/agentic-defaults/releases/tag/v0.3.0
update   .claude/agents/analyst.md
...
model    .claude/agents/reviewer.md: opus (kit: sonnet)
edited   .claude/skills/tdd/SKILL.md, newer version available: see agd diff .claude/skills/tdd/SKILL.md, then agd merge or agd reset it
...

$ agd update
...
agentic-defaults is at 0.3.0: 30 updated, 1 added, 0 removed.
Review the changes with git diff, and commit .agd.lock with them.
```

- **Versioned.** Sources publish releases as git tags. A project installs one, records it in `.agd.lock`, and updates with one command, with links to the release notes.
- **Plain files in your repository.** Your agents read them as they are, people review them in pull requests. No plugin, no runtime, any assistant: Claude Code, GitHub Copilot, Cursor, Codex and others.
- **Never overwrites your work.** Updates keep an agent's `model:` and `tools:` lines and a `## This project` section. A file you changed elsewhere is left alone and reported, and `agd diff`, `agd merge` and `agd reset` settle it.
- **Composable.** Install only the packs you need, and stack your team's setup on top of agentic-defaults.
- **Small enough to trust.** One bash script that needs only git. It never runs code from a source.

## Install

```bash
brew install zejnilovic/tap/agd
```

Without Homebrew, on macOS, Linux, WSL or Git Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh | bash
```

The [install script](install.sh) puts the latest release in `~/.local/bin`; run it again to update. You can also download [`agd`](https://github.com/Zejnilovic/agd/releases/latest/download/agd) from the latest release, make it executable and put it on your `PATH`, or run `bin/agd` from a clone. [Install](https://zejnilovic.github.io/agd/install/) has every way, with checksums and Windows notes, and how to turn on tab completion: `source <(agd completion zsh)` or `bash` in your shell's profile; Homebrew sets it up.

## Quick start

```bash
agd init                               # agentic-defaults' latest release; asks which packs
agd init --with flask,react            # only those packs, and the packs they require
agd init your-org/your-setup@1.2.0     # another source, at a release; @<commit> works too
agd status                             # what an update would do
agd update                             # move to the latest release
```

Commit `.agd.lock` with the files, so your team gets the same setup. The [quick start](https://zejnilovic.github.io/agd/quick-start/) walks through a first install, making files your own and a first update.

## Commands

| Command | Does |
|---|---|
| `agd init [<source>][@<version>\|@<commit>] [--with <packs>] [--yes]` | Installs a source: a GitHub `owner/repo`, a git URL or a local folder. In a project that is set up, adds another source. |
| `agd adopt [@<version>]` | Starts managing a copy of agentic-defaults made by hand or by its old `sync.sh`, without changing a file. |
| `agd status [--check]` | Shows what `agd update` would do. `--check` exits 1 when an update is due, for CI. |
| `agd update [--to [<source>@]<version>\|<commit>]` | Updates every source to its latest release, or one source to the given one. |
| `agd add <pack>`, `agd remove <pack>` | Installs or removes a pack. Removing keeps the files you changed, as yours. |
| `agd diff`, `agd merge`, `agd reset` | Settle a file you changed: see both changes, merge the source's into yours, or take the source's file. |
| `agd source list`, `agd source remove <name>` | List or remove sources. |
| `agd uninstall [--yes]` | Removes every source and `.agd.lock`, deleting the files you haven't changed. Asks about each file you changed. |
| `agd feedback [<note>]` | Report a problem with kit files to the source that owns them, as an issue you review before posting. Without a note, it asks a few questions. |

`-C <dir>` works in another folder, and `--offline` uses the cached copy of each source. `agd --help` lists everything, and [the reference](https://zejnilovic.github.io/agd/reference/commands/) has the details.

## Learn more

- [How agd works](https://zejnilovic.github.io/agd/concepts/): the idea, the words it uses, and what an update does to each file.
- [Make installed files your own](https://zejnilovic.github.io/agd/guides/your-changes/): project parts, edits, and settling them.
- [Keep it up to date](https://zejnilovic.github.io/agd/guides/updates/), and [automatically](https://zejnilovic.github.io/agd/guides/automatic-updates/), with a weekly pull request from CI.
- [Mirrors, proxies and offline machines](https://zejnilovic.github.io/agd/guides/company-networks/): agd on company networks.
- [Combine sources](https://zejnilovic.github.io/agd/guides/combine-sources/): your team's setup on top of agentic-defaults.
- [Publish your own agentic setup](docs/sources.md): the layout, `packs.txt`, releases.
- [FAQ](https://zejnilovic.github.io/agd/faq/)

## Contributing

Issues and pull requests are welcome. [CONTRIBUTING.md](CONTRIBUTING.md) explains how agd is built and tested, and [CHANGELOG.md](CHANGELOG.md) what's coming in the next release.

## License

[MIT](LICENSE) © Sasa Zejnilovic
