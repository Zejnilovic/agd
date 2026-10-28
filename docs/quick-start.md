# Quick start

This page installs [agentic-defaults](https://github.com/Zejnilovic/agentic-defaults) in a project, makes it the project's own, and updates it. It takes five minutes. [Install agd](install.md) first.

## 1. Install a setup

In the root of your project, a git repository:

```console
$ agd init
Which packs of agentic-defaults 0.5.2?
   1) core (27 files): analyst agent, architect agent, developer agent, documenter agent, reviewer agent, security-reviewer agent, tester agent, commits-and-prs skill, context-md skill, debugging skill, diagrams skill, implementation skill, project-profile skill, project-scan skill, session-retro skill, task-plans skill, tdd skill
   2) research (3 files, needs core): research-collector agent, researcher agent, research skill
   3) flask (2 files, needs core): flask-developer agent, flask skill
   4) spring (2 files, needs core): spring-developer agent, spring skill
   5) react (2 files, needs core): react-developer agent, react skill
   6) relational-database (2 files, needs core): relational-database-developer agent, relational-database skill
   7) terraform (2 files, needs core): terraform-developer agent, terraform skill
   8) heroku (1 file, needs core): heroku skill
   9) aws (1 file, needs core): aws skill
  10) copilot-hook (1 file, needs core)
Numbers or names, such as 2 3 or flask, or Enter for every pack:
Installed agentic-defaults 0.5.2: 43 files from the packs aws copilot-hook core flask heroku react relational-database research spring terraform.
Commit .agd.lock along with the new files.
```

That installs the latest release of agentic-defaults, with the packs you pick: Enter takes them all, as here, and so does a run without a terminal. With [fzf](https://github.com/junegunn/fzf) installed, you pick them in fzf. Other ways to start:

```bash
agd init --with flask,react     # only those packs, and what they require
agd init @0.5.1                 # a given release
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
agentic-defaults 0.4.0 is installed, and 0.5.2 is available: run agd update.
notes    https://github.com/Zejnilovic/agentic-defaults/releases/tag/v0.5.0
notes    https://github.com/Zejnilovic/agentic-defaults/releases/tag/v0.5.1
notes    https://github.com/Zejnilovic/agentic-defaults/releases/tag/v0.5.2
pack     aws is new in agentic-defaults 0.5.2: agd add aws installs it
...
update   .claude/agents/developer.md
model    .claude/agents/reviewer.md: opus (kit: sonnet)
update   .claude/agents/security-reviewer.md
...
edited   .claude/skills/implementation/SKILL.md, newer version available: see agd diff .claude/skills/implementation/SKILL.md, then agd merge or agd reset it
...
new      .claude/skills/session-retro/SKILL.md
new      .claude/skills/session-retro/stats.sh
```

Here the project installed core from 0.4.0, then chose opus for the reviewer and edited the implementation skill.

Read the release notes it links, then update:

```console
$ agd update
...
agentic-defaults is at 0.5.2: 8 updated, 2 added, 0 removed.
Review the changes with git diff, and commit .agd.lock with them.
```

The reviewer kept `model: opus`, and the edited skill was left alone. Review the changes with `git diff`, and commit them with `.agd.lock`.

## 5. Settle an edited file

When you changed a file and the source changed it too, `agd diff` shows both changes, and `agd merge` combines them:

```console
$ agd merge .claude/skills/implementation/SKILL.md
merged   .claude/skills/implementation/SKILL.md: your changes and the kit's up to agentic-defaults 0.5.2, without conflicts. Review it with git diff.
```

To drop your changes and take the source's file instead, use `agd reset <path>`.

## Next

- [How agd works](concepts.md): the idea, and what an update does to each file.
- [Keep it up to date](guides/updates.md), with a weekly check in CI.
- [Combine sources](guides/combine-sources.md): your team's setup on top of agentic-defaults.
- [Publish your own setup](sources.md).
