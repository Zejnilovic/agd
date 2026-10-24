# Keep it up to date

A project stays on the release it installed until you update it. `agd status` tells you what an update would do, and `agd update` does it.

## Check what would change

```bash
agd status
```

It fetches each source, and lists what `agd update` would do to each file. It writes nothing. For a source on GitHub, it links the notes of every release since yours: read them, since a release can ask projects for manual steps.

Each line starts with what happens to the file:

| Line | Means |
|---|---|
| `update` | The source changed the file, and you didn't. The update replaces it, keeping the project parts. |
| `new` | A new file in a pack you have. The update installs it. |
| `removed` | The source dropped the file. The update deletes it, or keeps it as yours when you changed it. |
| `edited` | You changed the file. With "newer version available", the source changed it too: [settle it](your-changes.md#settle-an-edited-file). |
| `deleted` | You deleted an installed file. It stays deleted. List it in `.agd-ignore` to stop the notice. |
| `ignored` | `.agd-ignore` lists an installed file. The update stops managing it, and the file stays. |
| `taken` | A project file has a path the source ships, so the source's file isn't installed. |
| `model`, `tools` | Your agent's own `model:` or `tools:` line, which the update keeps. |
| `pack` | A pack that is new in the release, or gone from it. |
| `notes` | The release notes of a release since yours. |

## Update

```bash
agd update
git diff
```

`agd update` moves every source to its latest release, and prints what it changed. Review it with `git diff`, run your checks, and commit the changes with `.agd.lock`.

When a release changes the default model of an agent whose model you chose, the update keeps yours and says so:

```text
model    .claude/agents/reviewer.md: kept opus; the kit now suggests sonnet (was haiku)
```

## Move to a given release or commit

```bash
agd update --to 0.2.0          # a release, newer or older than yours
agd update --to 3f2c1ab        # a commit, for example to try a change before its release
```

`--to` works when the project has one source. A project installed at a commit moves to the latest release with a plain `agd update`.

## Check for updates in CI

`agd status --check` exits with 1 when an update is due, so a scheduled job can tell you. Edited and deleted files alone don't make an update due. A GitHub Actions workflow:

```yaml title=".github/workflows/agentic-setup.yml"
name: Agentic setup
on:
  schedule:
    - cron: "0 7 * * 1" # Mondays
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - name: Install agd
        run: |
          curl -fsSL https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh | bash
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"
      - name: Check for a newer setup
        run: agd status --check
```

A failed run means an update is due; its log shows what `agd update` would do. For a private source, give git a token first, as [the FAQ shows](../faq.md#can-a-source-be-private).

## Work offline

agd keeps a bare clone of each source in `~/.cache/agd`. With `--offline`, it uses those instead of fetching:

```bash
agd status --offline
```

The source must have been fetched once on this machine.
