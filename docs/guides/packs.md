# Choose packs

A source groups its files into packs, such as agentic-defaults' `core`, `flask` and `react`. A project installs the packs it needs, and each pack brings the packs it requires.

## Install only some packs

`agd init` installs every pack. To start with fewer, name them:

```bash
agd init --with flask,react
```

That installs `flask`, `react` and `core`, which both require. An unknown name stops agd before it writes anything, and lists the source's packs.

## See what is installed

```console
$ agd source list
agentic-defaults 0.3.0 https://github.com/Zejnilovic/agentic-defaults.git (packs: core)
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
