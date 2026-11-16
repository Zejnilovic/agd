# Keep projects up to date automatically

A project stays on its release until someone runs `agd update`. The GitHub Action [agd-action](https://github.com/Zejnilovic/agd-action) can do it for you: on a schedule, it checks for a newer release, runs the update, and opens a pull request with the changes.

## The workflow

agd keeps its own repository's setup up to date with this file, so it is the one in use. Copy it to `.github/workflows/agd-update.yml` in your project:

```yaml title=".github/workflows/agd-update.yml"
--8<-- ".github/workflows/agd-update.yml"
```

It runs on Mondays, and whenever you start it from the Actions tab (**Run workflow**). Each run:

1. Installs the agd release that this version of the action pins, and checks the download against its SHA-256, so a changed download fails the run.
2. Runs `agd status --check`. When nothing is due, the run ends there. An error, such as a [moved tag](updates.md#when-a-release-changes-after-you-installed-it), fails the run.
3. When an update is due, runs `agd update`, commits the result to the `agd-update` branch, and opens a pull request, or updates the body of the one that is open. The body is what `agd update` printed.

A source you follow with `--latest` is never due, so the action doesn't move it: [Follow a source without releases](updates.md#follow-a-source-without-releases) says why.

The action's [README](https://github.com/Zejnilovic/agd-action#readme) lists its inputs, such as another branch name, and its outputs. With `mode: check`, it only tells you whether an update is due.

## Which agd it runs

Each release of the action pins one agd release, and agd's own release moves it: a new agd patch release makes a patch release of the action, a minor one a minor release. A new agd major version, which may need manual steps in projects, comes as a new major version of the action, so `@v1` never jumps a major.

`@v1` follows each release. To review each new agd version before your project runs it, pin the action to a commit and let Dependabot propose the next one:

```yaml
      - uses: Zejnilovic/agd-action@<commit sha> # v1.0.0
```

```yaml title=".github/dependabot.yml"
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

If your organization runs only actions it allows, fork agd-action into it and use the fork.

## Permissions

The job needs `contents: write` to commit to the branch, and `pull-requests: write` to open the pull request; the workflow asks for both. GitHub still forbids workflows to open pull requests until you allow it. The branch is updated, then the run fails with:

```text
pull request create failed: GraphQL: GitHub Actions is not permitted to create or approve pull requests (createPullRequest)
```

In **Settings → Actions → General**, under "Workflow permissions", turn on **Allow GitHub Actions to create and approve pull requests**, and run the workflow again. In an organization, the organization's settings may have to allow it first.

For a private source, give git a token that can read it in a step before the action, as [the FAQ shows](../faq.md#can-a-source-be-private).

## Signed commits

The action makes its commit with GitHub's API (`createCommitOnBranch`), not with `git push`, and GitHub signs a commit made that way. So it works in a repository whose ruleset requires signed commits on every branch, and the commit shows as **Verified**. The commit goes to a temporary branch first, and `agd-update` then moves to it, so an open pull request stays open.

The API commits files without their mode. A kit file agd installs as executable may lose its executable bit on the branch, and the pull request lists those files. A kit whose scripts are run with `bash <script>` isn't affected.

## Why a pull request, not a push

The files an update changes are instructions for your agents: what they do, which tools they may run, which model they use. Someone should read a new release of them before every agent in the project follows it, as with a dependency update. The pull request is that review, and your checks run on it.

!!! note "Checks on the pull request"
    GitHub doesn't run your checks on its own for a commit the workflow made with its own token. In agd's repository, the check runs wait with the status **Action required**. Open one and click **Approve and run**. To have the checks run without that step, give the action a GitHub App's or a person's token as its `token` input. If no check run shows up at all, close and reopen the pull request.

## What the pull request shows

The body lists every file, as `agd update` printed it. Shortened, for this repository's update to agentic-defaults 0.5.1 with one skill edited:

```text
notes    https://github.com/Zejnilovic/agentic-defaults/releases/tag/v0.5.0
notes    https://github.com/Zejnilovic/agentic-defaults/releases/tag/v0.5.1
pack     aws is new in agentic-defaults 0.5.1: agd add aws installs it
updated  .claude/agents/developer.md
updated  AGENTS.md
added    .claude/skills/session-retro/SKILL.md
edited   .claude/skills/implementation/SKILL.md: left alone, and a newer version is available (see agd diff .claude/skills/implementation/SKILL.md, then agd merge or agd reset it)
agentic-defaults is at 0.5.1: 8 updated, 2 added, 0 removed.
```

Read the release notes it links: a release can ask for manual steps. New packs aren't installed; add one with `agd add <pack>` if you want it.

An `edited` line is a file your project changed. The update leaves it alone, so the pull request doesn't touch it: that file is the reviewer's to settle. After you merge, run `agd diff <path>`, then `agd merge <path>` or `agd reset <path>`, as [Make files your own](your-changes.md#settle-an-edited-file) shows. Settle it on your main branch rather than on `agd-update`, since the next run replaces that branch.

Until you settle it, `agd status --check` keeps reporting the update as due. When such files are all that is due, the update changes nothing, and the run ends without a pull request.
