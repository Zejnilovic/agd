# Install for every project

A project's kit stays in that project. For what you want in every project on your machine, install a kit in your home folder:

```text
$ agd --home init
Installed agentic-home 0.1.0: 1 file from the packs kit-authoring.
```

Without a source, this installs [agentic-home](https://github.com/Zejnilovic/agentic-home), whose `kit-authoring` skill lands in `~/.claude/skills/`. To install another home kit, name it: `agd --home init your-org/team-home`.

Every command works the same way:

```bash
agd --home status
```

```bash
agd --home update
```

Nothing updates a home kit for you, so run `agd --home status` now and then.

`--home` is a way to name your home folder, like `-C ~`. Running agd in `~` counts too: the rules below follow the folder, whichever way you got there.

## What's different in your home folder

Whatever lands in your home folder can reach every project under it, so a few rules change there:

| Situation | In a project | In your home folder |
|---|---|---|
| `agd init` without a source | Installs agentic-defaults | Installs agentic-home |
| The kit has a file outside `.claude/`, or a `.claude/settings*` file | Installs it | [Stops and explains](#when-agd-stops) |
| A later release adds such a file | Installs it | Skips that file, with a notice, and updates the rest |
| `agd adopt` | Manages an existing copy | Stops |

Everything else works as it does in a project. A file you already have at a kit's path is `taken` and left alone, including your own `~/.claude/CLAUDE.md`. `.agd.lock` and `.agd-ignore` live in `~`, and agd gives no advice about git unless `~` is a git repository.

## Home kits

A home kit is a kit whose files are all under `.claude/`, with plain ASCII names and no `.claude/settings*` files, once `.agd-ignore` is applied. It needs no marker, because agd can tell from its paths. A kit of only skills and agents counts, whoever wrote it. [Create a kit](create-a-kit.md#a-kit-for-the-home-folder) shows how to make one.

## When agd stops

agd itself runs nothing, but in your home folder a kit's files could load or run later, without anyone asking:

- **A root `CLAUDE.md` or `AGENTS.md`**, as kits for projects have, loads in every project under `~`, because Claude Code reads those files from each folder above the one you work in. A `~/CLAUDE.md` would also stop it reading each project's `AGENTS.md`.
- **`.claude/settings.json`** can turn on hooks in every project.
- **Other files in your home folder** can run or give access: `.zshenv` at every shell start, `.ssh/authorized_keys` for logging in, `.local/bin/git` in place of the real `git`.

So agd installs nothing and explains:

```text
$ agd --home init Zejnilovic/agentic-defaults --with core
agd: agentic-defaults isn't a home kit, so agd won't install it in your home folder.
There, agd installs only under .claude/, and never a settings file, because other files could load or run in every project.
This kit has AGENTS.md, CLAUDE.md, .local_context/*.

Use a kit made for home:
  agd --home init

Or take only this kit's skills: add these lines to ~/.agd-ignore, then run this again:
agentic-defaults:AGENTS.md
agentic-defaults:CLAUDE.md
agentic-defaults:.claude/agents/*
agentic-defaults:.local_context/*
```

## Take only a kit's skills

Add the lines agd printed to `~/.agd-ignore`, and run the same command again:

```text
$ agd --home init Zejnilovic/agentic-defaults --with core
Installed agentic-defaults 0.5.3: 16 files from the packs core.
11 ignored, as .agd-ignore asks.
```

Only the skills are in `~/.claude/skills/` now. To take the agents too, remove their line. To stop ignoring a file later, remove its line and run `agd --home update`. A file agd refuses stays out, with a `skipped` notice.

A kit with no skills gets lines that leave out only the files agd refuses, so the rest installs.

Keep the `agentic-defaults:` at the start of each line. It limits the line to that kit. A plain `.claude/agents/*` would also leave out the agents of every other kit you install at home, without saying so.

Two things to know about skills taken this way:

- **They may mention files a project doesn't have.** Skills from a kit for projects often refer to `AGENTS.md`, `CONTEXT.md` or `.local_context/`.
- **They can override a project's copies.** See the next section.

## Next to a project's own kit

A project can have a file that your home folder also has. Which one you get depends on the file and the tool. For Claude Code, as of November 2026:

| File | With a copy in both | Docs |
|---|---|---|
| A skill | Your home folder's wins | [Skills](https://code.claude.com/docs/en/skills) |
| An agent | The project's wins | [Subagents](https://code.claude.com/docs/en/sub-agents) |
| `CLAUDE.md`, rules | Both load | [Memory](https://code.claude.com/docs/en/memory) |

So a skill at home can replace the version a project chose, without any sign. `agd status` in a project tells you when a skill or agent it installed differs from the copy in your home folder. It's only a notice: the exit code stays the same, and agd changes nothing.

```text
$ agd status
agentic-defaults 0.5.3 is installed, the latest release.
home     .claude/skills/context-md/SKILL.md: your home folder has a different copy, and your tools may use that one
```

## Good to know

- **Read a kit before you install it at home.** The limit keeps a kit inside `.claude/`, but it doesn't make the kit safe: its text reaches every project, and a skill or agent can hold scripts for an agent to run and [hooks of its own](https://code.claude.com/docs/en/hooks). `agd --home status` shows what an update would change before you run it.
- **Hooks in your settings.** agd never installs a `.claude/settings*` file in your home folder, so to turn on a hook for every project, add it to your own settings.
- **Older installs.** Files agd already manages in your home folder keep updating, even outside `.claude/`. `agd --home source list` and `.agd.lock` show what you have.
- **Skill folders.** When you already have a file in a kit's skill folder, agd installs none of that skill, so your copy and the kit's don't mix. `agd --home status` lists each `taken` file. A folder agd already manages part of, from before 0.5.1, keeps updating file by file.
- **Other tools and moved folders.** `--home` means `$HOME` and nothing else. The rules above are written for Claude Code, so other tools' folders, such as `~/.codex/`, count as outside `.claude/`. agd doesn't follow `CLAUDE_CONFIG_DIR`.
- **Git Bash on Windows.** `$HOME` is usually `%USERPROFILE%`, where Claude Code looks, but not always. Check with `echo $HOME`.
