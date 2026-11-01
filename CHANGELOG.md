# Changelog

What changed in agd. The next version's changes are collected here; each released version's notes are on its GitHub release.

Version numbers: **major** when the lock or `packs.txt` format changes and projects or sources need manual steps, **minor** for new commands or options, **patch** for fixes.

A bullet can end with the issues it touches: `(#12)` means this release fixes #12, `(ref #20)` means a related change that leaves #20 open, and they combine as `(ref #20, ref #11, #12)`. When the release is out, each issue gets a comment, and the fixed ones are closed.

## 0.5.0 (unreleased)

- `--home` works in your home folder, for every project on your machine: `agd --home init`, `agd --home update` and so on. It's a way to name the folder, so `-C ~` and running in `~` get the same rules. [Install for every project](https://zejnilovic.github.io/agd/guides/home/) explains them.
- In your home folder, `agd init` without a source installs [agentic-home](https://github.com/Zejnilovic/agentic-home), a kit made for it, whose `kit-authoring` skill guides an agent through creating a kit. `AGD_HOME_SOURCE` replaces its URL.
- In your home folder, agd installs only under `.claude/`, and never `.claude/settings.json`, because other files could load or run in every project: a root `CLAUDE.md`, `.zshenv`, `.ssh/authorized_keys`. `init` and `add` stop on a kit with such a file, and print the `.agd-ignore` lines that take only the kit's skills. A release that adds one skips it, with a notice, and updates the rest; files agd already manages there keep updating. `agd adopt` stops there too.
- `agd status` in a project notes each skill or agent it installed that differs from the copy in your home folder, which your tools may use instead. It doesn't change the exit code.
- Outside a git work tree, agd no longer advises you to commit or to use `git diff`. In your home folder, `taken` says "your file".
- A new guide, [Create a kit](https://zejnilovic.github.io/agd/guides/create-a-kit/), goes from an empty repository to a first release, with what makes a good kit. The docs now use one set of words: a kit is what agd installs, and a kit source, or source, is the repository that holds it.
- `agd check` warns about a `tools:` entry in a kit file, and about a `## This project` section in a file other than an `AGENTS.md`, since both belong to the project.

## 0.4.0 (2026-10-28)

- `agd init` in a terminal asks which packs to install, unless `--with` names them. It lists each pack with its file count, the packs it needs and its agents and skills; you type numbers or names, or press Enter for every pack. With fzf installed, you pick them in fzf (Esc installs nothing). Packs come with the packs they require, and agd says which it added. Without a terminal, or with `--yes`, agd installs every pack as before, so scripts are unchanged.
- agd notices when a source moves a release's tag. `.agd.lock` records the commit behind each installed release in a new `commit <source> <sha>` line, and `status`, `update`, `add`, `remove`, `diff`, `merge` and `reset` stop when the tag points elsewhere, printing both commits and the change to the installed files. `agd update --to <version>` accepts the release as it is now. A lock without the line gets it the next time agd writes the lock, without a warning. It stays `agd-lock 1`: older agd reads it, and drops the line when it rewrites the lock.
- `agd update --to` works in a project with several sources: `--to <source>@<version>` (or `@<commit>`) moves that source and leaves the others as they are. A bare `--to <version>` there still stops, and says how to name the source. Tab completion offers `<source>@<version>` when there are several sources.
- `agd check [<folder>]` checks a source before you release it, so a mistake shows up there rather than in a project's install. It reads the working tree with the parsing installs use, and reports a path that doesn't exist, a folder without its `/`, a file in two packs, a `requires` that names no pack, a `requires` cycle, a path with spaces or quotes, a missing release tag and a `min-agd` newer than agd, one line each, with the line of `packs.txt`. It exits with 1 on an error. Lines it doesn't know, packs without files and, under a kit folder, files in no pack are warnings. It writes nothing and fetches nothing.
- Each release's `agd`, `agd-<version>.tar.gz` and `SHA256SUMS` have a build provenance attestation, so `gh attestation verify agd --repo Zejnilovic/agd` shows that this repository's Release workflow built the file you downloaded. The workflow checks it on Linux, macOS and Windows; `install.sh` is unchanged.
- `agd uninstall` takes agd out of a project in one step: it removes every source, deletes the installed files you haven't changed and `.agd.lock`, and leaves `.agd-ignore` and the cache. It lists what it will do first, asks about each file you changed (delete it, or keep it as yours) and asks once more before writing anything. Without a terminal it needs `--yes`, which keeps every changed file.

## 0.3.0 (2026-10-27)

- Tab completion for bash and zsh: `agd completion bash|zsh` prints the script, for example `source <(agd completion zsh)` in `~/.zshrc`, and Homebrew installs it. It completes commands, options, packs to add or remove, installed paths and source names from the lock, and the releases of any source, asking it with `git ls-remote` (only cached ones with `--offline`). It writes nothing, not even to the cache.

## 0.2.0 (2026-10-25)

- `agd feedback [<note>]` reports a problem with installed kit files to the source that owns them, without telemetry. It finds the source from the kit files the note names, adds the source version, the agd version, the OS and whether the project changed each file, and opens a pre-filled issue in the browser with `gh`, or prints a link to one. Nothing is posted until you submit it. Without a note, it asks which kit files (picked in fzf when it is installed, or by number), what went wrong, what you expected and how the task ended; when you're not sure of the file and several sources are installed, it asks which source. For a source not on GitHub, it prints the report.
- The release archive leaves out agd's own agentic setup (`AGENTS.md`, `CLAUDE.md`, `.claude/`, `.local_context/`, `.agd.lock`, `CONTEXT.md`).

## 0.1.2 (2026-10-24)

- Install agd without Homebrew: `install.sh` installs or updates it with only bash and git (`curl -fsSL https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh | bash`), and each release now has the plain `agd` script and `SHA256SUMS` to download by hand.
- agd has a documentation site, https://zejnilovic.github.io/agd, with the idea behind agd, guides and a reference. `agd --help` links it, and the hint to upgrade agd for a newer source covers installs without Homebrew.

## 0.1.1 (2026-10-24)

- `agd status` no longer calls every pack "new" after a project moves from a release without `packs.txt`, such as agentic-defaults 0.3.0, and doesn't mention a new pack whose files `.agd-ignore` keeps out.
- Replacing a file with another source's copy no longer dead-ends. When the file has your changes, or `.agd-ignore` gave it away from another source after an update, `agd init <source>` lists it and asks first; `--yes` skips the question.

## 0.1.0 (2026-10-24)

- First release. `agd init`, `adopt`, `status`, `update`, `add`, `remove`, `diff`, `merge`, `reset`, `source list` and `source remove`, for any git repository laid out as a source, with agentic-defaults as the default.
- Updates keep a project's own parts of installed files: an agent's `model:` and `tools:` lines, and a `## This project` section at the end of a Markdown file. Files changed anywhere else are reported, never overwritten.
- Sources install at a release (`@1.2.0`) or a commit (`@<sha>`), and several sources can share a project, with `.agd-ignore` choosing between them where they ship the same path.
- Bash 3.2 and Git Bash, with only git and POSIX tools.
