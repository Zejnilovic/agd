# Make installed files your own

Installed files are plain files in your repository, and you can change any of them. agd sorts each change into one of two kinds: a project part, which updates keep, or an edit, which updates never overwrite.

## Project parts

These three parts belong to the project. Change them freely; every update keeps them.

### An agent's model

The `model:` line in an agent's frontmatter. Choose a stronger model for a reviewer, or a cheaper one for routine work:

```yaml title=".claude/agents/reviewer.md"
---
name: reviewer
description: Reviews a change for bugs and broken contracts.
model: opus
---
```

`agd status` lists your choice, with the source's suggestion: `model .claude/agents/reviewer.md: opus (kit: sonnet)`.

### An agent's tools

The `tools:` entry in an agent's frontmatter, on one line or as a list, limits what the agent may use:

```yaml
tools: Read, Grep, Glob
```

Your entry always wins over the source's.

### A "This project" section

Everything from a `## This project` heading to the end of a Markdown file. Put your project's rules, commands and facts there:

```markdown title="AGENTS.md"
## This project

- `make test` runs the tests; `make check` runs everything CI runs.
- Never change files under `migrations/` that are already released.
```

When the source's file has this heading, as agentic-defaults' `AGENTS.md` does, your section replaces it. Otherwise agd keeps your section at the end of the file.

## Edits

Any other change to an installed file is an edit. agd never overwrites an edit: `agd update` leaves the file as it is, and `agd status` lists it as `edited`. Line endings and trailing blank lines don't count.

That is safe, but an edited file no longer gets the source's improvements on its own. So put what you can in project parts or in new files, and keep edits for what can't go there.

### Settle an edited file

When the source changes a file you edited, `agd status` says a newer version is available. Settle it with one of three commands.

**See both changes:**

```bash
agd diff .claude/skills/implementation/SKILL.md
```

It shows your changes since the file was installed, then the source's changes up to its latest release.

**Merge the source's changes into yours:**

```bash
agd merge .claude/skills/implementation/SKILL.md
```

agd merges the file the way git merges branches, and records it as at the latest release, with your edits. Your model choice never conflicts. When both changed the same lines, agd writes conflict markers, exits with 1, and you resolve them as in any git merge:

```console
$ agd merge .claude/skills/implementation/SKILL.md
merged   .claude/skills/implementation/SKILL.md with 1 conflict: resolve the <<<<<<< markers, then review it with git diff.
```

```text
<<<<<<< yours
## Deploys

Deploy only from main, after the checks pass.
=======
## Live systems

Infrastructure, deployments and data outside a local or test setup are changed by the user, never by you.
...
>>>>>>> agentic-defaults 0.5.2
```

**Drop your changes:**

```bash
agd reset .claude/skills/implementation/SKILL.md
```

agd puts the file back as the installed release has it. It drops your edits and your `model:` and `tools:` lines, and keeps a "This project" section where the source's file has one. A file you deleted comes back. `agd update` then brings the newer version. `agd reset` without a path resets every installed file. It lists what it would drop and asks first; pass `--yes` to run it without a terminal.

## Files you don't want

- **Don't install a file:** list it in [`.agd-ignore`](../reference/files.md#agd-ignore) before `agd init` or `agd add`.
- **Remove an installed file:** delete it and list it in `.agd-ignore`. Without the list entry, `agd status` reminds you that it's deleted.
- **Take a file over:** list it in `.agd-ignore` and keep it. agd stops managing it, and it is a project file from then on.

## Your own agents and skills

Add them as new files with their own names, such as `.claude/agents/billing-expert.md`. agd never touches a file it didn't install. When a later release ships a file at the same path, agd leaves yours alone and reports the path as `taken`.

## Tell your agents

Agents edit files too. Tell them where project changes go, so they don't edit installed files. agentic-defaults does it with a comment at the top of each file and a rule in `AGENTS.md`:

```markdown
<!-- agentic-defaults 0.5.2. From agentic-defaults down to "This project": kit updates replace it, so don't edit it. The rest belongs to the project. -->
```
