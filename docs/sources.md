# Publish your own agentic setup

Any git repository can be an agd source: your team's agents, skills and instructions, published so projects install and update them with agd, alone or on top of another source such as [agentic-defaults](https://github.com/Zejnilovic/agentic-defaults). This page is for the people who maintain a source.

## The layout

A source is a git repository with release tags, `v1.0.0` and so on. The files it installs mirror a project's root, in one of two places:

- **In `kit/`** (the default). `kit/AGENTS.md` lands as `AGENTS.md` in a project, and `kit/.claude/agents/reviewer.md` as `.claude/agents/reviewer.md`. Everything else in the repository, such as its README, tests and scripts, stays out.
- **At the repository's root**, with `root .` in `packs.txt`. Use it when the repository already keeps its setup at its root, for example because it uses it itself. Only files listed in a pack are installed, so the README and the code stay out.

Paths can't contain spaces or quotes.

## packs.txt

`packs.txt` sits at the repository's root and groups the files into packs. Projects choose packs with `agd init --with`, `agd add` and `agd remove`.

```text
# Lines starting with # are comments.
min-agd 0.1.0
root .

pack review requires agentic-defaults:core
  .claude/agents/api-reviewer.md
  .claude/skills/api-review/

pack release requires review
  .claude/agents/release-manager.md
```

- **`pack <name>`** starts a pack. Its files follow, indented, one path per line, relative to the root. A path ending in `/` takes every file under that folder.
- **Every file is in at most one pack.** Files in no pack aren't installed. Keep a skill folder in one pack, since its files belong together.
- **`requires`** names packs this one needs. A plain name is a pack of this source, installed along with it. `<source>:<pack>` is another source's pack: agd refuses this pack until that one is installed, and refuses to remove that source while this pack needs it.
- **`min-agd <version>`** is the oldest agd that can install this release. agd stops with an upgrade hint when it is older.
- **`root <folder>`** is where the files are. The default is `kit/`.

Without `packs.txt`, every file under `kit/` is one pack, `core`.

## Releases

agd installs the newest tag that looks like `v<major.minor.patch>`, and `agd status` tells projects when a newer one exists. For sources on GitHub, it links the release notes of every release in between, so write notes, and list the manual steps a project needs.

Projects can also install a release with `@1.2.0`, or a commit with `@<sha>`. A commit is useful for trying a change before you tag it.

## What projects may change

agd replaces a source's files when they update, but keeps three parts that belong to the project:

1. **An agent's `model:` line**, so a project can choose another model. When your release changes an agent's default model, projects that chose their own are told, and keep theirs.
2. **An agent's `tools:` entry**, single line or list, to limit what the agent may use. Leave it out of your files; a project's entry always wins.
3. **Everything from a `## This project` heading to the end of a Markdown file**, for a project's own additions. Don't put that heading in your files, except where a project should fill in a section of its own, like the end of agentic-defaults' `AGENTS.md`: agd keeps everything from it down as the project's.

Any other change a project makes to your file is an edit. agd never overwrites it: `agd status` reports the file, and `agd diff`, `agd merge` and `agd reset` settle it. Tell agents about these rules in your files, for example with a short comment at the top of each, as agentic-defaults does, so they put project changes in the project's parts.

## How agd decides what is yours

A project's `.agd.lock` lists every file agd installed, the source it came from, and the version installed. agd writes only files in the lock, or new files at free paths:

- an unchanged file gets your new version,
- a file you removed from your source is deleted when the project hasn't changed it, and is left to the project when it has,
- a new file in a pack the project has is installed, unless a project file already uses that path.

Files a project wrote itself are never touched, even when your release ships a file at the same path.

## Next to other sources

A project can install your source next to others with `agd init your-org/your-setup`. The source is named after its repository, so keep the name distinctive.

- **Pack names** can repeat across sources. Projects then name one as `<source>:<pack>`.
- **A path another source also ships** stops agd until the project chooses with a line in `.agd-ignore`: `<other-source>:<path>` to take yours, or `<your-source>:<path>` to keep theirs. When the project changed their copy, agd lists it and asks before replacing it with yours.

## Try it before you release

In a scratch project, install your source from its folder or a commit, and look:

```bash
agd init ~/work/your-setup
```

```bash
agd status
```

Change a file in your source, commit it, then `agd update --to <sha>` in the scratch project shows what your next release does to an installed copy.

agd only copies files; it never runs code from a source. Scripts you ship run only when an agent or a person runs them.
