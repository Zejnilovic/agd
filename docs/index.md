---
template: home.html
title: agd
description: Your agentic setup, versioned like a dependency. agd installs instructions, agents, skills and hooks from git repositories into your projects, and updates them without overwriting what you changed.
hide:
  - navigation
  - toc
---

## Install it in a minute { #install }

=== "Homebrew"

    ```bash
    brew install zejnilovic/tap/agd
    ```

=== "Install script"

    ```bash
    curl -fsSL https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh | bash
    ```

=== "By hand"

    ```bash
    curl -fLo ~/.local/bin/agd https://github.com/Zejnilovic/agd/releases/latest/download/agd
    chmod +x ~/.local/bin/agd
    ```

agd needs bash 3.2 or newer and git, on macOS, Linux, or Windows with Git Bash. Then, in the root of your project:

```bash
agd init
```

That installs [agentic-defaults](https://github.com/Zejnilovic/agentic-defaults), a setup for Claude Code and GitHub Copilot. Any git repository laid out as a source works: `agd init your-org/your-setup`.

[Quick start](quick-start.md){ .md-button .md-button--primary } [All the ways to install](install.md){ .md-button }

## Publish your own setup

Your team's agents, skills and rules can be a source too: a git repository with release tags, and a `packs.txt` that groups its files. Projects install it alone, or on top of agentic-defaults. [Publish your own agentic setup](sources.md) shows how.
