# Adopt a copy you already have

Projects that copied agentic-defaults by hand, or with its old `scripts/sync.sh`, can move to agd without changing a file:

```bash
agd adopt
```

agd reads the release from the first line of `AGENTS.md`, which says `agentic-defaults 0.3.0` or similar. When it doesn't, name the release:

```bash
agd adopt @0.2.0
```

It then writes `.agd.lock` with every file of that release the project has, and the packs they belong to:

```console
$ agd adopt
Adopted agentic-defaults 0.2.0: 36 files from the packs core. No file changed.
2 files differ from 0.2.0: agd status shows which count as edits.
Commit .agd.lock, then run agd status.
```

A file of an adopted pack that the project doesn't have is listed as `missing`: the next `agd update` installs it, unless `.agd-ignore` lists it. agd still reads `.agentic-defaults-ignore`, which `scripts/sync.sh` used.

Then commit `.agd.lock`, and look at `agd status`. Files that differ from the release because the project changed them are edits, and you can [settle them](your-changes.md#settle-an-edited-file) like any other.

## Other sources

`agd adopt` works for any source, given its release:

```bash
agd adopt your-org/team-kit@1.2.0
```
