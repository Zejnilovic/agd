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

## Does agd work with skills.sh?

Partly. Both use `SKILL.md` files and `.claude/skills/`, but they find, install and update skills differently:

- **Installing a kit's skills with the [skills CLI](https://github.com/vercel-labs/skills).** Its search should find skills under `kit/.claude/skills/`, so `npx skills add <owner>/<kit>` can take them. You get only the skills, not the kit's `AGENTS.md` or agents, and agd doesn't track or update them.
- **Installing a skills.sh repository with agd.** Most keep their skills in `skills/<name>/`, and agd doesn't read that layout. Rewrite the repository as a source: [Move from skills.sh](guides/from-skills-sh.md) has the steps, and how to move projects over. It doesn't need release tags; projects can [follow its newest commit](guides/updates.md#follow-a-source-without-releases).
- **Using both in one project.** It works, but keep each skill with one tool. When the skills CLI already installed a skill with the same folder name, agd reports that folder's files as `taken` and installs none of them, so it doesn't mix the two.

## How does agd compare with similar tools?

Several tools share or distribute agent setups, and they solve different problems. This table comes from each project's own README, as of November 2026, and these tools change quickly, so check them yourself:

| Tool | What it does | From git repositories | Lockfile | Runs on |
|---|---|---|---|---|
| agd | Installs kits as ordinary repository files, and updates them without overwriting a project's changes | Any | `.agd.lock` | bash and git |
| [APM](https://github.com/microsoft/apm) | Dependency manager for instructions, skills, prompts, agents, hooks, plugins and MCP servers | Any | `apm.lock.yaml` | Python, or native binaries |
| [AGPM](https://docs.rs/crate/agpm-cli) | Git-based package manager for agents, snippets, commands, scripts, hooks and MCP servers | Any | `agpm.lock` | Rust, or prebuilt binaries |
| [skills CLI](https://github.com/vercel-labs/skills) | Installs skills only, and feeds the [skills.sh](https://www.skills.sh/) directory | GitHub sources | `skills-lock.json` | Node.js |
| [ai-rulez](https://github.com/Goldziher/ai-rulez) | Generates and validates rules, skills, agents and MCP configuration for many assistants | Can reuse git content | `ai-rulez.lock` | Go |
| [rulesync](https://github.com/dyoshikawa/rulesync) | Generates each tool's configuration from one set of rules | Fetches skills | Not stated | Node.js |
| [Ruler](https://github.com/intellectronica/ruler) | Distributes one set of instructions to each agent's files | Not stated | Not stated | Node.js |

APM and AGPM are the closest to agd: they also treat an agent setup as versioned dependencies. Consider one of them if you want to manage MCP servers as dependencies, or a generator such as ai-rulez, rulesync or Ruler if you use several assistants and want one source written in each one's format. agd copies files and doesn't convert them.

### What agd does extra

agd is built for a setup that a team shares and each project also changes. That's where it goes further than the closest tools. This table reflects what their docs say, as of November 2026:

| | agd | APM | AGPM | skills CLI |
|---|---|---|---|---|
| You edited an installed file, and an update changes it | Keeps your file, and tells you | Keeps edited skill files unless you pass `--force`; can replace other files, and `apm audit` reports the change | Not documented | Not documented |
| Merge the update into your edited file | [`agd merge`](guides/your-changes.md#settle-an-edited-file) | Not documented | Not documented | Not documented |
| Built-in places for project changes | An agent's `model:` and `tools:` lines, and a `## This project` section, all kept across updates | Not documented | Patches to an agent's fields, in `agpm.toml` | Not documented |
| Installed files | Committed, as ordinary repository files | Lockfile committed, `apm_modules/` ignored | `.claude/` ignored by default | Committed |
| What it needs | bash and git | Python, or native binaries | Rust, or prebuilt binaries | Node.js |

So with agd:

- **You can change what you install and still get updates.** `agd status` lists your edits, `agd diff` shows your change and the source's, and `agd merge` combines them. Your own files are never touched, even when a release ships a file at the same path.
- **Reviews see everything.** Installed files are ordinary files in your repository, so a change to an agent's instructions shows up in `git diff` and in the pull request, like any other code.
- **There's almost nothing to install.** agd is one bash script that needs only git, on Linux, macOS and Git Bash on Windows. It never runs code from a source.
- **Sources can build on each other.** A team's kit can sit on top of another source and [require its packs](guides/combine-sources.md), and agd stops when two sources ship the same path, until you choose one.

"Not documented" means we didn't find it in that tool's docs, not that it can't be done. The other tools do things agd doesn't: APM, for example, manages MCP servers and reports moved tags with `apm outdated`.

## Does agd run code from a source?

No. agd only copies files, and never runs anything it installs. Scripts and hooks a source ships run only when an agent or a person runs them, as with any file in your repository, so review a source's releases as you would review a dependency. If a source moves a release's tag after you installed it, agd stops and shows the change before using it: see [When a release changes](guides/updates.md#when-a-release-changes-after-you-installed-it). In your home folder, where a file could run without anyone asking, agd [installs only under `.claude/`](guides/home.md#when-agd-stops).

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

No. `agd init your-org/your-setup` installs any source, without agentic-defaults. To make another source the default for `agd init` and `agd adopt`, set `AGD_SOURCE` to its URL. In your home folder, that variable is `AGD_HOME_SOURCE`.

## Can I install a kit for every project on my machine?

Yes. `agd --home init` installs a kit in your home folder, and agd has a few special rules there. See [Install for every project](guides/home.md).

## How do I stop using agd?

Run `agd uninstall`. It deletes the installed files you haven't changed and `.agd.lock`, and asks about each file you changed: delete it, or keep it as yours. To remove one source instead, run `agd source remove <name>`. To keep every installed file as a project file that agd no longer manages, delete `.agd.lock`.

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
| `no files to install from ...` | The repository doesn't use the [source layout](sources.md#the-layout), or the packs you chose list no files. |
| `release ... needs agd ... or newer` | The source needs a newer agd. [Update agd](install.md). |
| `can't fetch ...` | Check the URL and your network or credentials, or work from the cache with `--offline`. |
| `... has no releases (tags like v1.2.3)` | The source has no release tags yet. Take its [newest commit](guides/updates.md#follow-a-source-without-releases) with `--latest`, install a commit, `<source>@<sha>`, or ask its maintainers to tag a release. |
| `... ships paths that another source already installed here` | Choose one source for each path in `.agd-ignore`. See [Combine sources](guides/combine-sources.md#when-two-sources-ship-the-same-path). |
| `... confirm in a terminal, or run it with --yes` | agd asks before it replaces or resets files. Run it in a terminal, or pass `--yes`. |

Something else? [Open an issue](https://github.com/Zejnilovic/agd/issues) with the command, its output and `agd --version`.
