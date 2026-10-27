# Changelog

What changed in agd. The next version's changes are collected here; each released version's notes are on its GitHub release.

Version numbers: **major** when the lock or `packs.txt` format changes and projects or sources need manual steps, **minor** for new commands or options, **patch** for fixes.

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
