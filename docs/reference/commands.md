# Commands

```text
agd [-C <dir>] [--offline] <command> [<arguments>]
```

| Option | Does |
|---|---|
| `-C <dir>` | Works in `<dir>` instead of the current folder. |
| `--offline` | Uses the cached copy of each source instead of fetching it. Each source must have been fetched once. |
| `--version` | Prints agd's version. |
| `--help` | Lists the commands. |

## init

```text
agd init [<source>][@<version>|@<commit>] [--with <pack>,...] [--yes]
```

Installs a source in the project, and writes `.agd.lock`.

- **`<source>`** is a GitHub `owner/repo`, a git URL (`https://...`, `ssh://...`, `git@host:...`) or a local folder. Without it, agd installs agentic-defaults, or the URL in `AGD_SOURCE`.
- **`@<version>`** installs that release, such as `@1.2.0`; **`@<commit>`** a commit, by its SHA. A commit that isn't on a branch needs its full SHA. Without either, agd installs the latest release; a source without releases needs a commit.
- **Packs.** In a terminal, agd lists the source's packs, with their agents and skills, and asks which to install: numbers or names, or Enter for every pack. With [fzf](https://github.com/junegunn/fzf) installed, you pick them in fzf: Tab picks several, Ctrl-A all, Enter confirms, Esc installs nothing. A source with one pack isn't asked about. [Choose packs](../guides/packs.md) shows it.
- **`--with`** installs only the named packs, and the packs they require, without asking.
- **`--yes`** installs every pack without asking, and replaces files without asking where `.agd-ignore` gives a path from one source to another. Without a terminal, agd installs every pack too.

In a project that is already set up, `init <source>` adds another source. It stops when the new source ships a path another source installed; [choose one in `.agd-ignore`](../guides/combine-sources.md#when-two-sources-ship-the-same-path). Paths where the project already has its own file are skipped and listed as `taken`.

## adopt

```text
agd adopt [<source>][@<version>]
```

Starts managing a copy of a source made by hand or by agentic-defaults' old `scripts/sync.sh`, without changing a file. Without `@<version>`, agd reads agentic-defaults' release from the first line of `AGENTS.md`. See [Adopt a copy](../guides/adopt.md).

## status

```text
agd status [--check]
```

Shows what `agd update` would do, file by file, and links the release notes of GitHub sources. It writes nothing in the project. With `--check`, it exits with 1 when an update is due, for CI. [The lines it prints](../guides/updates.md#check-what-would-change).

## update

```text
agd update [--to [<source>@]<version>|<commit>]
```

Updates every source to its latest release, keeping the project parts of each file and leaving edited files alone. `--to` moves to the given release, newer or older, or to a commit. When the project has several sources, `--to` names the one to move, as `<source>@<version>` or `<source>@<commit>`, and leaves the others as they are.

If an installed release's tag has moved to another commit since it was installed, `update` stops and shows the change, as do `status`, `add`, `remove`, `diff`, `merge` and `reset`. `--to <version>`, or `--to <source>@<version>` with several sources, accepts the release as it is now. See [When a release changes after you installed it](../guides/updates.md#when-a-release-changes-after-you-installed-it).

## add

```text
agd add [<source>:]<pack>
```

Installs a pack, and the packs it requires, from the installed release. Name the source when two sources have a pack of that name.

## remove

```text
agd remove [<source>:]<pack>
```

Removes a pack. Files you changed stay, as project files. Refuses while another installed pack requires it.

## diff

```text
agd diff <path>
```

Shows your changes to an installed file since it was installed, then the source's changes to it up to its latest release.

## merge

```text
agd merge <path>
```

Merges the source's latest version of a file into your edited copy, and records the file as at that version. Exits with 1 when the merge has conflicts, which it marks in the file.

## reset

```text
agd reset [<path>] [--yes]
```

Puts installed files back as the installed release has them, dropping edits, `model:` and `tools:` lines, but keeping a "This project" section where the source's file has one. Brings back deleted files. Without a path, resets every installed file. Lists what it would drop and asks first; without a terminal, it needs `--yes`.

## source

```text
agd source list
agd source remove <name>
```

`list` shows each source with its version, URL and installed packs. `remove` removes a source and its files; files you changed stay, as project files. It refuses while another source's installed packs require the source.

## uninstall

```text
agd uninstall [--yes]
```

Takes agd out of the project: removes every source, deletes the installed files you haven't changed (and folders left empty), and removes `.agd.lock`. It leaves `.agd-ignore` and the cache. It lists what it would do first, and writes nothing before you answer. For each file you changed, it asks whether to delete it or keep it as a project file (Enter keeps it; `a` deletes it and the rest, `k` keeps it and the rest), then asks once more for the whole change. Without a terminal it needs `--yes`, which keeps every file you changed. It doesn't fetch anything, so it works offline.

## feedback

```text
agd feedback [<note>]
```

Reports a problem with installed files to the source that owns them, as a GitHub issue you review before posting. `<note>` is a Markdown file anywhere, describing what went wrong, for example `notes.md`. Without a note, agd asks a few questions in the terminal instead. agd never posts anything itself.

- **Which source.** agd looks for installed paths in the note, such as `.claude/agents/reviewer.md` (but not `reviewer.md.bak`), and sends the report to their source. A note that names no installed file goes to the only source; with several sources, name a file. A note that names files of two sources stops: split it.
- **The issue.** The title is the note's first `# ` heading, or "Feedback on" the first file it names. The body lists the source and its version, the agd version, the OS, each named file and whether the project changed it, and then the note.
- **With `gh` installed,** agd runs `gh issue create --web`, which opens the issue in your browser to edit and submit; if gh fails, for example before `gh auth login`, agd prints the link instead. **Without it,** agd prints a link to a pre-filled new issue. When the report is too long for a link, agd prints the body to paste and a link with only the title.
- **A source not on GitHub** gets the title and body printed, with the source's URL.

```text
$ agd feedback notes.md
Open this link to file the report on Zejnilovic/agentic-defaults. Nothing is posted until you submit it there.

https://github.com/Zejnilovic/agentic-defaults/issues/new?title=The%20reviewer%20skips%20the%20context%20check&body=Source%3A%20agentic-defaults%200.4.0%0Aagd%3A%200.2.0%0AOS%3A%20Darwin%2025.6.0%0A...
```

### Without a note

In a terminal, `agd feedback` asks which installed files the problem is about, what went wrong, which becomes the title, what you expected, and how the task ended. It builds the report from the answers and writes nothing in the project. Without a terminal, it stops and asks for a note.

- **Picking files.** With [fzf](https://github.com/junegunn/fzf) installed, agd lets you search the installed files in fzf: Tab picks several, Enter confirms. Without it, agd lists them by number, and you type one or more, such as `5 7`.
- **Files of two sources.** agd asks again: pick the files of one source, and report the others separately.
- **Not sure which file.** Press Esc in fzf, or Enter at the numbers. With several sources installed, agd then asks which source the report is for.

```text
$ agd feedback
Which kit files is it about?
  1) .claude/agents/analyst.md
  ...
  7) .claude/agents/tester.md
  ...
  25) CLAUDE.md
Numbers, such as 2 or 2 5, or Enter if you're not sure: 7
What went wrong? One line; it becomes the title: It wrote 40 tests for one small function
What did you expect? Enter to skip: A few tests for the behavior that matters
How did the task end? 1) done, 2) partly done, 3) failed, Enter to skip: 2

Open this link to file the report on Zejnilovic/agentic-defaults. Nothing is posted until you submit it there.

https://github.com/Zejnilovic/agentic-defaults/issues/new?title=It%20wrote%2040%20tests%20for%20one%20small%20function&body=Source%3A%20agentic-defaults%200.4.0%0A...
```

Notes and answers can hold private code or names. Read the issue before you submit it.

## completion

```text
agd completion bash
agd completion zsh
```

Prints the shell's tab completion script. It completes commands and options; from the project's `.agd.lock`, the packs to add or remove, installed paths for `diff`, `merge` and `reset`, and source names; and the releases for `update --to` (as `<source>@<version>` when the project has several sources) and `init <source>@`, which it asks each source for with `git ls-remote`, for up to 3 seconds, adding the cached ones. With `--offline`, it offers only the cached releases. Completing writes nothing, not even to the cache, so it doesn't offer the packs of a source that isn't installed yet. Homebrew installs the scripts; otherwise [turn it on in your shell](../install.md#tab-completion).

## Environment

| Variable | Does |
|---|---|
| `AGD_SOURCE` | The URL of the default source, instead of agentic-defaults. |
| `AGD_CACHE` | The folder for cached sources. The default is `$XDG_CACHE_HOME/agd`, or `~/.cache/agd`. |

## Exit codes

| Code | Means |
|---|---|
| `0` | Done. |
| `1` | `status --check`: an update is due. `merge`: the merge left conflicts. |
| `2` | An error, such as a wrong argument, a missing lock or a source agd can't fetch. The message says what to do. |
