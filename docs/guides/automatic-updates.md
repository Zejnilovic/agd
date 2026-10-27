# Keep projects up to date automatically

A project stays on its release until someone runs `agd update`. A scheduled GitHub Actions workflow can do it for you: each week it checks for a newer release, runs the update, and opens a pull request with the changes.

## The workflow

agd keeps its own repository's setup up to date with this file, so it is the one in use. Copy it to `.github/workflows/agd-update.yml` in your project:

```yaml title=".github/workflows/agd-update.yml"
--8<-- ".github/workflows/agd-update.yml"
```

It runs on Mondays, and whenever you start it from the Actions tab (**Run workflow**). Each run:

1. Installs a pinned agd release and checks the file against the checksum from the release's [`SHA256SUMS`](../install.md#check-a-download), so a changed download fails the run.
2. Runs `agd status --check`. Exit 0 means nothing is due, and the run ends there. Any exit above 1 is an error, which fails the run.
3. On exit 1, runs `agd update`, commits the result to the `agd-update` branch, and opens a pull request, or updates the body of the one that is open. The body is what `agd update` printed.

To move to a newer agd, change `AGD_VERSION` and `AGD_SHA256`: the checksum is the `agd` line of that release's `SHA256SUMS`.

## Permissions

The job needs `contents: write` to push the branch, and `pull-requests: write` to open the pull request; the workflow asks for both. GitHub still forbids workflows to open pull requests until you allow it. The branch is pushed, then the run fails with:

```text
pull request create failed: GraphQL: GitHub Actions is not permitted to create or approve pull requests (createPullRequest)
```

In **Settings → Actions → General**, under "Workflow permissions", turn on **Allow GitHub Actions to create and approve pull requests**, and run the workflow again. In an organization, the organization's settings may have to allow it first.

For a private source, give git a token that can read it before the update step, as [the FAQ shows](../faq.md#can-a-source-be-private).

## Why a pull request, not a push

The files an update changes are instructions for your agents: what they do, which tools they may run, which model they use. Someone should read a new release of them before every agent in the project follows it, as with a dependency update. The pull request is that review, and your checks run on it.

!!! note "Checks on the pull request"
    GitHub doesn't start workflows for a pull request that a workflow opened with its own token. To run your checks on it, close and reopen the pull request, or give the update step a token of a GitHub App or a person as `GH_TOKEN`, and push with it.

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
