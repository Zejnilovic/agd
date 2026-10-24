# Changelog

What changed in agd. The next version's changes are collected here; each released version's notes are on its GitHub release.

Version numbers: **major** when the lock or `packs.txt` format changes and projects or sources need manual steps, **minor** for new commands or options, **patch** for fixes.

## 0.1.0 (2026-10-24)

- First release. `agd init`, `adopt`, `status`, `update`, `add`, `remove`, `diff`, `merge`, `reset`, `source list` and `source remove`, for any git repository laid out as a source, with agentic-defaults as the default.
- Updates keep a project's own parts of installed files: an agent's `model:` and `tools:` lines, and a `## This project` section at the end of a Markdown file. Files changed anywhere else are reported, never overwritten.
- Sources install at a release (`@1.2.0`) or a commit (`@<sha>`), and several sources can share a project, with `.agd-ignore` choosing between them where they ship the same path.
- Bash 3.2 and Git Bash, with only git and POSIX tools.
