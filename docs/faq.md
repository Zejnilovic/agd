# FAQ

## Which assistants does agd work with?

Any that reads files from your repository. agd copies a source's files to the paths the source gives them, and doesn't know which tool reads them. agentic-defaults targets Claude Code and GitHub Copilot; a source for Cursor, Codex, Gemini CLI or several at once works the same way.

## Does agentic-defaults work in Cursor?

Mostly. Cursor reads the folders agentic-defaults installs, but not every line in them, according to [Cursor's docs](https://cursor.com/docs/context/subagents):

- `AGENTS.md` at the root: read, as project rules.
- Skills in `.claude/skills/`: read. Cursor loads them for compatibility with Claude Code.
- Agents in `.claude/agents/`: read, also for compatibility. An agent of the same name in `.cursor/agents/` wins.
- `CLAUDE.md`: not read. It only imports `AGENTS.md`, which Cursor reads anyway.
- An agent's `model:` line: Cursor expects `inherit` or one of its model IDs, and doesn't document short names such as `sonnet`. Set the line to `inherit` or a Cursor model ID; it belongs to the project, so updates keep it.
- An agent's `tools:` line: ignored. Cursor's agents get all of the parent's tools, and only `readonly: true` limits them.

## Does agd run code from a source?

No. agd only copies files, and never runs anything it installs. Scripts and hooks a source ships run only when an agent or a person runs them, as with any file in your repository, so review a source's releases as you would review a dependency.

## Why not copy the files, or use a git submodule?

Copies drift, and copying a new version over an old one wipes out the project's changes, which is why agd exists. A submodule puts the setup in a subfolder, but assistants read files at fixed paths, such as `AGENTS.md` at the root and `.claude/agents/`, next to the project's own files. agd installs files where they belong, lets you take only some packs, and keeps the project's parts of each file.

## Why not a plugin or extension system?

Those belong to one assistant each, and usually keep the files outside your repository, where reviews and git history don't see them. agd's files are ordinary repository files, for any assistant, versioned with your code. The two can live side by side.

## Can a source be private?

Yes. agd fetches sources with git, so any repository your git can clone works, with the credentials git already has: SSH keys, a credential helper, or `gh auth setup-git`. Use an SSH URL if that's how you reach it:

```bash
agd init git@github.com:your-org/team-kit.git
```

In GitHub Actions, give git a token that can read the source before you run agd:

```bash
git config --global url."https://x-access-token:${TOKEN}@github.com/".insteadOf "https://github.com/"
```

## Does agd work behind a company mirror or proxy?

Yes, since it fetches with git: `url.<mirror>.insteadOf` and git's proxy settings apply to it, and `--offline` works from a cache copied from a connected machine. [Mirrors, proxies and offline machines](guides/company-networks.md) has each recipe, and how to install agd there.

## Do I have to use agentic-defaults?

No. `agd init your-org/your-setup` installs any source, without agentic-defaults. To make another source the default for `agd init` and `agd adopt`, set `AGD_SOURCE` to its URL.

## How do I stop using agd?

Delete `.agd.lock`. The installed files stay, as project files that agd no longer manages. To remove one source and its unchanged files instead, run `agd source remove <name>`.

## Does agd work on Windows?

Yes, in Git Bash or WSL. See [Install](install.md#windows). Line endings don't count as edits, so a checkout with CRLF line endings doesn't make every file look changed.

## Can several projects share a cache, or work without a network?

Every project on a machine shares the cache in `~/.cache/agd`. With `--offline`, agd works from it without fetching; each source must have been fetched once. A machine without a network can use a cache copied from another: see [offline machines](guides/company-networks.md#a-machine-without-a-network).

## How do I report a problem with an agent or skill a source installed?

Run `agd feedback` and answer its questions, or write what happened in a Markdown note that names the file, for example `.claude/agents/reviewer.md`, and run `agd feedback <note>`. agd finds the source that owns the file and opens a pre-filled issue on it, with the versions and whether you changed the file. You review it and submit it yourself; agd sends nothing. See [feedback](reference/commands.md#feedback).

## Something went wrong

agd's messages say what to do next. The common ones:

| Message | What to do |
|---|---|
| `no .agd.lock in ...: run agd init` | The folder isn't set up with agd. Run `agd init`, or use `-C` to point at the project. |
| `this project has a copy of agentic-defaults ...: run agd adopt` | The project copied agentic-defaults before agd. [Adopt it](guides/adopt.md). |
| `release ... needs agd ... or newer` | The source needs a newer agd. [Update agd](install.md). |
| `can't fetch ...` | Check the URL and your network or credentials, or work from the cache with `--offline`. |
| `... has no releases (tags like v1.2.3)` | The source has no release tags yet. Install a commit, `<source>@<sha>`, or ask its maintainers to tag a release. |
| `... ships paths that another source already installed here` | Choose one source for each path in `.agd-ignore`. See [Combine sources](guides/combine-sources.md#when-two-sources-ship-the-same-path). |
| `... confirm in a terminal, or run it with --yes` | agd asks before it replaces or resets files. Run it in a terminal, or pass `--yes`. |

Something else? [Open an issue](https://github.com/Zejnilovic/agd/issues) with the command, its output and `agd --version`.
