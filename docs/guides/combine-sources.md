# Combine sources

A project can install several sources, for example agentic-defaults for the basics and your team's setup for your own agents and rules. agd keeps them apart in `.agd.lock`, updates them together, and makes you choose where two sources ship the same path.

## Add another source

In a project that is already set up, `agd init` with a source adds it:

```bash
agd init your-org/team-kit
```

A source can be a GitHub `owner/repo`, any git URL, or a local folder:

```bash
agd init your-org/team-kit@1.2.0                       # a given release
agd init git@gitlab.example.com:platform/team-kit.git  # any git URL
agd init ~/work/team-kit                               # a local folder, to try it
```

agd names the source after its repository, here `team-kit`. A local folder works only on your machine, so publish the source before your team needs it.

```console
$ agd source list
agentic-defaults 0.3.0 https://github.com/Zejnilovic/agentic-defaults.git (packs: core)
team-kit 1.2.0 https://github.com/your-org/team-kit.git (packs: core review)
```

## When two sources ship the same path

If `team-kit` also ships `.claude/agents/reviewer.md`, `agd init` stops before it writes anything:

```text
agd: team-kit ships paths that another source already installed here:
  .claude/agents/reviewer.md, also from agentic-defaults: add agentic-defaults:.claude/agents/reviewer.md to take team-kit's copy, or team-kit:.claude/agents/reviewer.md to keep agentic-defaults's
Choose one source for each path with a line in .agd-ignore, then run agd init again.
```

Choose with a line in `.agd-ignore`. A line `<source>:<path>` keeps that path out of that source only:

```text title=".agd-ignore"
# The team's reviewer replaces the default one.
agentic-defaults:.claude/agents/reviewer.md
```

Run `agd init your-org/team-kit` again. When your copy of the file from the other source has changes, agd lists it and asks before replacing it; `--yes` answers for you.

## Packs that need another source

A source's pack can require another source's pack, written `<source>:<pack>` in its `packs.txt`, such as `requires agentic-defaults:core`. agd refuses to install that pack until the required pack is installed, and refuses to remove the required source while the pack needs it.

When two sources have a pack of the same name, name the source with it: `agd add team-kit:review`.

## Update and remove

`agd update` and `agd status` work on every source at once. To move one source to a given release or commit, name it: `agd update --to team-kit@1.3.0`. The other sources stay as they are.

To remove a source and its files:

```bash
agd source remove team-kit
```

agd deletes its files that you haven't changed, and keeps the ones you changed, as project files. It refuses while another source's installed packs require one of its packs. Removing the last source removes `.agd.lock` too.

## Publish your team's setup

Any git repository with release tags can be a source. [Publish your own agentic setup](../sources.md) covers the layout, `packs.txt` and releases.
