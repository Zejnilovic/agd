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
- **`--with`** installs only the named packs, and the packs they require. Without it, agd installs every pack.
- **`--yes`** replaces files without asking, where `.agd-ignore` gives a path from one source to another.

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
agd update [--to <version>|<commit>]
```

Updates every source to its latest release, keeping the project parts of each file and leaving edited files alone. `--to` moves to the given release, newer or older, or to a commit; it works when the project has one source.

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
