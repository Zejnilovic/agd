# Quick start

This page installs [agentic-defaults](https://github.com/Zejnilovic/agentic-defaults) in a project, makes it the project's own, and updates it. It takes five minutes. [Install agd](install.md) first.

## 1. Install a setup

In the root of your project, a git repository:

```console
$ agd init
Installed agentic-defaults 0.3.0: 37 files from the packs core.
Commit .agd.lock along with the new files.
```

That installs every pack of the latest release of agentic-defaults. Other ways to start:

```bash
agd init --with flask,react     # only those packs, and what they require
agd init @0.2.0                 # a given release
agd init your-org/your-setup    # another source
```

A source can be a GitHub `owner/repo`, any git URL, or a local folder.

## 2. Commit it

```bash
git add -A
git commit -m "Add agentic-defaults with agd"
```

Commit `.agd.lock` with the files. It records the source, its version and every file agd installed, so your team gets the same setup, and agd can later tell your changes from the source's.

## 3. Make it yours

Installed files are plain files in your repository: your agents read them, and you can change them. agd keeps three parts of them as the project's on every update:

- **An agent's `model:` line.** Choose another model for an agent:

    ```yaml title=".claude/agents/reviewer.md"
    ---
    name: reviewer
    model: opus
    ---
    ```

- **An agent's `tools:` line**, to limit what it may use.
- **A `## This project` section at the end of a Markdown file**, for your own rules. agentic-defaults' `AGENTS.md` ends with one, for your project's commands and profile.

A change anywhere else in a file is an edit. agd never overwrites it, and tells you when the source changed the same file. To drop a file you don't want, delete it and list it in `.agd-ignore`. [Make installed files your own](guides/your-changes.md) has the details.

## 4. Stay up to date

`agd status` shows what an update would do, and changes nothing:

```console
$ agd status
agentic-defaults 0.2.0 is installed, and 0.3.0 is available: run agd update.
notes    https://github.com/Zejnilovic/agentic-defaults/releases/tag/v0.3.0
update   .claude/agents/analyst.md
...
model    .claude/agents/reviewer.md: opus (kit: sonnet)
update   .claude/agents/reviewer.md
...
edited   .claude/skills/tdd/SKILL.md, newer version available: see agd diff .claude/skills/tdd/SKILL.md, then agd merge or agd reset it
...
new      .claude/skills/project-profile/SKILL.md
```

Read the release notes it links, then update:

```console
$ agd update
...
agentic-defaults is at 0.3.0: 30 updated, 1 added, 0 removed.
Review the changes with git diff, and commit .agd.lock with them.
```

The reviewer kept `model: opus`, and the edited skill was left alone. Review the changes with `git diff`, and commit them with `.agd.lock`.

## 5. Settle an edited file

When you changed a file and the source changed it too, `agd diff` shows both changes, and `agd merge` combines them:

```console
$ agd merge .claude/skills/tdd/SKILL.md
merged   .claude/skills/tdd/SKILL.md: your changes and the kit's up to agentic-defaults 0.3.0, without conflicts. Review it with git diff.
```

To drop your changes and take the source's file instead, use `agd reset <path>`.

## Next

- [How agd works](concepts.md): the idea, and what an update does to each file.
- [Keep it up to date](guides/updates.md), with a weekly check in CI.
- [Combine sources](guides/combine-sources.md): your team's setup on top of agentic-defaults.
- [Publish your own setup](sources.md).
