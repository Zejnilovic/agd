# Choose packs

A source groups its files into packs, such as agentic-defaults' `core`, `flask` and `react`. A project installs the packs it needs, and each pack brings the packs it requires.

## Install only some packs

In a terminal, `agd init` lists the source's packs and asks which to install:

```text
Which packs of agentic-defaults 0.5.2?
   1) core (27 files): analyst agent, architect agent, developer agent, ...
   2) research (3 files, needs core): research-collector agent, researcher agent, research skill
   3) flask (2 files, needs core): flask-developer agent, flask skill
   ...
  10) copilot-hook (1 file, needs core)
Numbers or names, such as 2 3 or flask, or Enter for every pack: flask
Installing core too: flask needs it.
Installed agentic-defaults 0.5.2: 29 files from the packs core flask.
```

Each pack brings the packs it needs. With [fzf](https://github.com/junegunn/fzf) installed, you pick them in fzf instead: Tab picks several, Ctrl-A all of them, Enter confirms, and Esc installs nothing.

To choose without the question, for example in a script, name the packs:

```bash
agd init --with flask,react
```

That installs `flask`, `react` and `core`, which both require. An unknown name stops agd before it writes anything, and lists the source's packs. Without a terminal, or with `--yes`, agd installs every pack.

## See what is installed

```console
$ agd source list
agentic-defaults 0.5.2 https://github.com/Zejnilovic/agentic-defaults.git (packs: core flask)
```

To see every pack a source has, read its `packs.txt`, or its README.

## Add a pack

```bash
agd add spring
```

agd installs the pack and the packs it requires, from the release the project has installed, and records them in `.agd.lock`. When two sources here have a pack of that name, name the source too: `agd add agentic-defaults:spring`.

A new release can bring new packs. `agd update` doesn't install them on its own, but `agd status` and `agd update` mention them:

```text
pack     release is new in team-kit 1.2.0: agd add release installs it
```

## Remove a pack

```bash
agd remove react
```

agd deletes the pack's files that you haven't changed. A file you changed stays, as a project file that agd no longer manages. agd refuses to remove a pack that another installed pack requires; remove that one first.

## Leave out single files

To keep a pack but not one of its files, list the file in `.agd-ignore` at the project's root:

```text
# We don't use the React agent.
.claude/agents/react-developer.md
```

Patterns work too, such as `.claude/skills/react/*`. See [`.agd-ignore`](../reference/files.md#agd-ignore).
