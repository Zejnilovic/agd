# Files

## .agd.lock

agd writes `.agd.lock` at the project's root. Commit it, and don't edit it by hand: agd compares it with your files to tell your changes from a source's.

```text title=".agd.lock"
# Written by agd. Commit it, and don't edit it by hand.
agd-lock 1
source agentic-defaults https://github.com/Zejnilovic/agentic-defaults.git 0.3.0
pack agentic-defaults core
file agentic-defaults .claude/agents/analyst.md e1b12281e462c4424bd5b78bb8c4320d809f39f8
file agentic-defaults .claude/agents/architect.md 5d5bd7379bfe89bbd35c527f7930bfcd95f6711a
...
```

| Line | Records |
|---|---|
| `agd-lock 1` | The format's version. |
| `source <name> <url> <version>` | A source, and its installed release, or the full SHA of its installed commit. |
| `pack <source> <pack>` | An installed pack. |
| `file <source> <path> <blob>` | An installed file, and the git blob hash of the content agd installed. |

agd sorts the lines, so changes to the lock read well in a review.

## .agd-ignore

You write `.agd-ignore` at the project's root, and commit it. Each line is a path or a pattern; lines starting with `#` are comments.

```text title=".agd-ignore"
# No React agent or skill here.
.claude/agents/react-developer.md
.claude/skills/react/*

# The team's reviewer instead of agentic-defaults'.
agentic-defaults:.claude/agents/reviewer.md
```

- **A path or pattern** keeps the path out of every source. In a pattern, `*` matches any characters, `/` included, and `?` one character. To match a folder's files, end it with `/*`.
- **`<source>:<path or pattern>`** keeps it out of that source only. It decides between two sources that ship the same path.

agd doesn't install an ignored path. When it installed the file earlier, `agd update` stops managing it, and the file stays as a project file.

agd also reads `.agentic-defaults-ignore`, the file agentic-defaults' old `scripts/sync.sh` used.

## packs.txt

A source's `packs.txt` groups its files into packs, and says where they are and which agd it needs. It belongs to the people who maintain a source: see [Publish your own setup](../sources.md#packstxt).

## The cache

agd keeps a bare git clone of each source in `~/.cache/agd`, or in `$XDG_CACHE_HOME/agd`, or in `$AGD_CACHE`. It is safe to delete; agd fetches the sources again when it needs them.
