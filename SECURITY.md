# Security

## What agd does and doesn't do

agd copies files from git repositories into a project. It never runs code from a source: not at install, not at update. It writes only files listed in the project's `.agd.lock`, and new files at paths no project file uses. A release with a path that would leave the project or reach into `.git` can't be installed, and in your home folder agd installs only under `.claude/`, and never a settings file.

A source can still ship files that run later: hook configurations, scripts that skills use, instructions that tell an agent to run a command. Those run when an agent, a tool or a person runs them. Treat a source like any dependency: install sources you trust, read the release notes `agd status` links, and review what `agd update` changed with `git diff` before you commit it.

## Supported versions

Fixes go into the latest release. Update with `brew upgrade agd`, or by running the [install script](https://zejnilovic.github.io/agd/install/) again.

## Report a vulnerability

Please report it privately, not in a public issue: use **Report a vulnerability** on the repository's [Security tab](https://github.com/Zejnilovic/agd/security). Include what an attacker controls (a source, a project file, a URL), what agd does as a result, and the steps to reproduce it with `agd --version`.
