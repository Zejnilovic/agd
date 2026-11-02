# Move from skills.sh

agd doesn't read the layout of [skills.sh](https://www.skills.sh/) repositories, where skills sit in `skills/<name>/`. To use such a repository with agd, rewrite it as a [kit source](../sources.md). It can keep serving the [skills CLI](https://github.com/vercel-labs/skills) at the same time, so projects can move one by one.

As of November 2026, this page relies on the skills CLI's docs and code for how that tool behaves. We didn't run it, so try the steps on one project first.

## Rewrite the repository

Move the skills to `.claude/skills/`, the path they should have in a project:

```bash
mkdir -p .claude
```

```bash
git mv skills .claude/skills
```

Keep them at the repository's root rather than in `kit/`. agd reads them there with `root .`, and `.claude/skills/` is one of the folders the skills CLI looks in. Add a `packs.txt` at the root, with a pack for each skill that projects should be able to choose:

```text
root .

pack api-review
  .claude/skills/api-review/

pack deploy
  .claude/skills/deploy/
```

agd installs files at the paths the source gives them, so skills in `.claude/skills/` reach tools that read that folder. If your team uses a tool that reads only `.agents/skills/`, check what it supports before you move.

## Decide how you ship changes

| Your team | Check the source with | Projects install with | Projects update with |
|---|---|---|---|
| Tags releases, `v1.2.3` | `agd check` | `agd init your-org/team-skills` | `agd update` |
| Works from the newest commit | `agd check --latest` | `agd init your-org/team-skills --latest` | `agd update --latest` |

```console
$ agd check --latest
No problems: 2 packs, 3 files.
```

Without tags, there are no release notes, and every commit to the default branch reaches a project on its next `agd update --latest`. Each project still records the commit in `.agd.lock` and reviews the change with `git diff`. You can [start tagging](updates.md#follow-a-source-without-releases) at any time; a plain `agd update` then moves to the latest release.

## Projects that stay on the skills CLI

According to its code, `npx skills update` finds a skill that moved within its repository by name, and records the new path, so these projects can wait. Entries with no recorded path or hash are listed as legacy instead. Try it on one project before you rely on it.

## Move a project

Commands below use `--latest`. If the source has tags, leave it out of `init`, and use `@<version>` instead of it with `adopt`.

### A new project

```console
$ agd init your-org/team-skills --latest
Installed team-skills commit 351ef5d: 3 files from the packs api-review deploy.
Commit .agd.lock along with the new files.
```

### A project with symlinks

By default, the skills CLI keeps a skill in `.agents/skills/<name>/` and links to it from each tool's folder. Look for links first:

```console
$ find .claude/skills -maxdepth 1 -type l
.claude/skills/deploy
```

Remove each linked skill with the skills CLI, then install:

```bash
npx skills remove deploy
```

```bash
agd init your-org/team-skills --latest
```

According to its code, `skills remove` keeps the `.agents/skills/<name>/` folder while another tool in the project still links to it. Delete the link yourself if it stays.

Don't use `agd adopt` on a linked skill. It succeeds, but later updates write through the link into `.agents/skills/`. Don't skip the removal either: `init` reports a skill it finds there as `taken` and leaves it as it is.

```console
$ agd init your-org/team-skills --latest
taken    .claude/skills/deploy/SKILL.md (a project file has this path; not installed)
Installed team-skills commit bdc9d7d: 2 files from the packs api-review deploy.
1 taken: project files already use those paths or their skill folders, so agd left them alone.
Commit .agd.lock along with the new files.
```

### A project with real copies

When `find` lists nothing, `agd adopt` takes over the copies without changing a file. A copy that differs from the source shows as an edit, which you can [settle](your-changes.md#settle-an-edited-file):

```console
$ agd adopt your-org/team-skills --latest
Adopted team-skills commit bdc9d7d: 1 file from the packs deploy. No file changed.
1 file differs from commit bdc9d7d: agd status shows whether it counts as an edit.
Commit .agd.lock, then run agd status.
```

```console
$ agd status
team-skills is installed at commit bdc9d7d, and it has no releases.
edited   .claude/skills/deploy/SKILL.md
```

`adopt` picks up only the packs the project has files of. Add the others if you want them:

```console
$ agd add api-review
added    .claude/skills/api-review/SKILL.md
added    .claude/skills/api-review/checklist.md
Added the packs api-review from team-skills commit bdc9d7d: 2 files.
Commit .agd.lock along with the new files.
```

Then remove the project's `skills-lock.json` if nothing else uses it, so the skills CLI no longer lists these skills, and commit the result. Don't run `npx skills update` on a skill agd now manages: agd would report its changes as edits.
