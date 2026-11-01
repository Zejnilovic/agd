# Create a kit

A **kit** is what agd installs in a project: instructions, agents, skills and hooks. A **kit source** is the git repository that holds a kit, with its `packs.txt` and release tags. This page takes you from an empty repository to a first release. [Kit sources](../sources.md) is the reference for the format.

## Let an agent do it

The `kit-authoring` skill guides an agent through this. It's part of [agentic-home](https://github.com/Zejnilovic/agentic-home), a kit for your home folder, so you install it once and it works in every project:

```bash
agd --home init
```

Then ask your agent to create the kit. The skill has it find out what the kit is for, split it into packs, write the files, run `agd check` and try the result.

The skill installs into `~/.claude/skills/`. If your tool doesn't read that folder, point your agent at the [skill's text](https://raw.githubusercontent.com/Zejnilovic/agentic-home/main/kit/.claude/skills/kit-authoring/SKILL.md).

## Do it yourself

This example builds a kit that reviews API changes, in a repository named `team-kit`. agd names the source after the repository, so choose a distinctive name.

### 1. Add the files

The files go in `kit/`, mirroring a project's root:

```bash
git init team-kit
```

```bash
cd team-kit
```

```bash
mkdir -p kit/.claude/agents kit/.claude/skills/api-review
```

`kit/.claude/agents/api-reviewer.md`:

```markdown
---
name: api-reviewer
description: Reviews API changes for breaking changes. Use before merging a change to a public API.
model: sonnet
---

<!-- From team-kit. Updates replace this file except its model: and tools: lines and a "## This project" section at the end. -->

You review API changes. Follow the api-review skill.
```

`kit/.claude/skills/api-review/SKILL.md`:

```markdown
---
name: api-review
description: What makes an API change breaking. Use when reviewing or changing a public API.
---

<!-- From team-kit. Updates replace this file except a "## This project" section at the end. -->

# API review

- A removed field is a breaking change.
```

### 2. List them in a pack

`packs.txt`, at the repository's root:

```text
pack review
  .claude/agents/api-reviewer.md
  .claude/skills/api-review/
```

### 3. Check it

```text
$ agd check
error    no release tag yet: tag one as v<major.minor.patch>, for example git tag v0.1.0
1 error and 0 warnings in /home/you/work/team-kit.
```

That error is the only one left, so commit and tag:

```bash
git add -A
```

```bash
git commit -m "First kit"
```

```bash
git tag v0.1.0
```

```text
$ agd check
No problems: 1 pack, 2 files.
```

### 4. Try it in a project

In a scratch git repository:

```text
$ agd init ~/work/team-kit
Installed team-kit 0.1.0: 2 files from the packs review.
The source is a local path, so .agd.lock works only on this machine.
Commit .agd.lock along with the new files.
```

To see what your next release does to an installed copy, commit a change in the source without tagging it, then update to that commit:

```text
$ agd update --to 6c25e6e
updated  .claude/skills/api-review/SKILL.md
team-kit is at commit 6c25e6e: 1 updated, 0 added, 0 removed.
Review the changes with git diff, and commit .agd.lock with them.
```

### 5. Publish it

Push the repository and its tags. Projects then install it by name:

```bash
agd init your-org/team-kit
```

For each later release, add a new tag and write release notes, including any manual steps a project needs. Never move a tag: projects that installed it stop until they accept the change.

## A kit for the home folder

A home kit applies to every project on a person's machine, installed with `agd --home init your-org/team-home`. Build it the same way, with a few differences:

- **Only files under `.claude/`.** [agd stops on anything else](home.md#when-agd-stops), including a root `CLAUDE.md` or `AGENTS.md`, which would load in every project under the home folder.
- **Put rules in `.claude/rules/<name>.md`.** Most people already have a `~/.claude/CLAUDE.md`, and agd leaves it alone, so a kit's copy wouldn't install for them.
- **No `.claude/settings.json`.** agd stops on that too, since its hooks would run in every project. Tell people what to add to their own settings instead.
- **Choose distinctive skill names.** A personal skill beats a project's skill with the same name.

To try it without touching your own home folder, point `HOME` at a scratch folder:

```bash
HOME=~/scratch-home agd --home init ~/work/team-home
```

## What makes a good kit

- **It has one purpose.** If you can't say what it's for in a sentence, it's probably two kits, or two packs.
- **It starts with one pack.** Add another only when some projects want a part that others don't, such as one framework.
- **It puts each thing where it costs least.** `AGENTS.md` is read every session, so it holds only rules for all work. A skill is read when its description matches, so it holds procedures. An agent runs in its own context, so it fits a role that needs one.
- **Its descriptions say when to use the file.** The description decides when an agent reads a skill or calls an agent.
- **Every rule changes what an agent does.** Leave out what agents do anyway and what the code already shows.
- **It holds no project facts.** Stacks, commands and names belong to each project, which adds them in [its own parts](../sources.md#what-projects-may-change).
- **It tells agents the rules.** A short comment at the top of each file names the source and the parts a project may change, so agents put a project's changes there.
- **It holds no secrets**, and a public kit holds no internal names or URLs.
