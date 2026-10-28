"""Behavior tests for bin/agd. Run: python3 -m unittest discover -s tests"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
AGD = REPO / "bin/agd"
INSTALL = REPO / "install.sh"
# macOS ships bash 3.2 as /bin/bash; agd must keep working with it.
BASH = "/bin/bash" if sys.platform == "darwin" else "bash"

GIT_ENV = {
    **os.environ,
    # Ignore the user's and the system's git settings, such as signed tags.
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, env=GIT_ENV, capture_output=True, text=True)


def write(root, rel, text="x\n"):
    path = pathlib.Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


class VersionTest(unittest.TestCase):
    """bin/agd's version line and scripts/bump.sh."""

    def test_version_line_matches_version_file(self):
        version = (REPO / "VERSION").read_text().strip()
        self.assertIn(f"\nversion={version}\n", AGD.read_text())

    def test_script_has_no_syntax_errors(self):
        result = subprocess.run([BASH, "-n", str(AGD)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bump_sets_version_line_and_changelog(self):
        with tempfile.TemporaryDirectory() as root:
            for rel in ("VERSION", "bin/agd", "CHANGELOG.md", "scripts/bump.sh"):
                write(root, rel, (REPO / rel).read_text())
            current = (REPO / "VERSION").read_text().strip()
            major, minor, patch = (int(part) for part in current.split("."))
            new = f"{major}.{minor + 1}.0"
            result = run(["bash", "scripts/bump.sh", new], root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(pathlib.Path(root, "VERSION").read_text(), new + "\n")
            self.assertIn(f"\nversion={new}\n", pathlib.Path(root, "bin/agd").read_text())
            self.assertIn(f"## {new} (unreleased)", pathlib.Path(root, "CHANGELOG.md").read_text())
            self.assertNotEqual(run(["bash", "scripts/bump.sh", current], root).returncode, 0)


class ReleaseTest(unittest.TestCase):
    """scripts/release.sh and scripts/formula.sh, which the Release workflow runs."""

    CHANGELOG = "# Changelog\n\nWhat changed.\n\n## 0.1.0 (unreleased)\n\n- First release.\n- Fast.\n"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        write(self.root, "scripts/release.sh", (REPO / "scripts/release.sh").read_text())
        write(self.root, "VERSION", "0.1.0\n")
        write(self.root, "CHANGELOG.md", self.CHANGELOG)

    def tearDown(self):
        self._tmp.cleanup()

    def release(self):
        return run(["bash", "scripts/release.sh", "--date", "2026-02-02", "--notes", "notes.md"], self.root)

    def read(self, rel):
        return pathlib.Path(self.root, rel).read_text()

    def test_release_dates_the_entry_and_writes_its_notes(self):
        result = self.release()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "0.1.0")
        self.assertIn("\n## 0.1.0 (2026-02-02)\n", self.read("CHANGELOG.md"))
        self.assertNotIn("unreleased", self.read("CHANGELOG.md"))
        self.assertEqual(self.read("notes.md"), "- First release.\n- Fast.\n")

    def test_release_refuses_an_entry_with_a_todo_or_no_entry(self):
        for changelog in (self.CHANGELOG.replace("- Fast.", "- TODO: describe the change"),
                          self.CHANGELOG.replace("## 0.1.0 (unreleased)", "## 0.0.9 (2026-01-01)")):
            write(self.root, "CHANGELOG.md", changelog)
            result = self.release()
            self.assertNotEqual(result.returncode, 0, changelog)
            self.assertIn("0.1.0", result.stderr)
            self.assertEqual(self.read("CHANGELOG.md"), changelog)
            self.assertFalse(pathlib.Path(self.root, "notes.md").exists())

    def test_formula_installs_the_release_archive(self):
        result = run(["bash", str(REPO / "scripts/formula.sh"), "0.1.0", "ab" * 32], self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        formula = result.stdout
        for expected in ("class Agd < Formula",
                         'url "https://github.com/Zejnilovic/agd/releases/download/v0.1.0/agd-0.1.0.tar.gz"',
                         f'sha256 "{"ab" * 32}"', 'license "MIT"', 'bin.install "bin/agd"',
                         'generate_completions_from_executable(bin/"agd", "completion", shells: [:bash, :zsh])',
                         "agd --version"):
            self.assertIn(expected, formula)
        if shutil.which("ruby"):
            write(self.root, "agd.rb", formula)
            check = run(["ruby", "-c", "agd.rb"], self.root)
            self.assertEqual(check.returncode, 0, check.stderr)

    def test_archive_leaves_out_the_agentic_setup(self):
        # The Release workflow builds the archive with git archive; .gitattributes decides what it holds.
        shutil.copy(REPO / ".gitattributes", self.root)
        setup = (".agd.lock", "AGENTS.md", "CLAUDE.md", "CONTEXT.md", "bin/CONTEXT.md",
                 ".claude/agents/developer.md", ".local_context/README.md")
        kept = ("bin/agd", "README.md", "LICENSE", "docs/index.md")
        for rel in setup + kept:
            write(self.root, rel)
        for args in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-qm", "release"]):
            self.assertEqual(run(args, self.root).returncode, 0)
        archive = run(["git", "archive", "--format=tar", "--prefix=agd-0.1.0/", "-o", "agd.tar", "HEAD"], self.root)
        self.assertEqual(archive.returncode, 0, archive.stderr)
        listed = run(["tar", "tf", "agd.tar"], self.root).stdout.split()
        for rel in kept:
            self.assertIn("agd-0.1.0/" + rel, listed)
        for rel in setup:
            self.assertNotIn("agd-0.1.0/" + rel, listed)


class InstallTest(unittest.TestCase):
    """install.sh against a temporary agd repository, without network."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.repo, self.home = base / "agd", base / "home"
        self.repo.mkdir()
        self.home.mkdir()
        run(["git", "init", "-q", "-b", "main"], self.repo)
        self.env = {k: v for k, v in GIT_ENV.items() if k != "AGD_INSTALL_DIR"}
        # install.sh fetches https://github.com/Zejnilovic/agd.git; make that the temporary repository.
        self.env.update({"HOME": str(self.home), "GIT_CONFIG_COUNT": "1",
                         "GIT_CONFIG_KEY_0": f"url.file://{self.repo}.insteadOf",
                         "GIT_CONFIG_VALUE_0": "https://github.com/Zejnilovic/agd.git"})

    def tearDown(self):
        self._tmp.cleanup()

    def release(self, version, tag=None):
        write(self.repo, "bin/agd", f'#!/usr/bin/env bash\nversion={version}\n'
                                    f'[ "${{1:-}}" = --version ] && echo "agd $version"\n')
        run(["git", "add", "-A"], self.repo)
        self.assertEqual(run(["git", "commit", "-q", "-m", version], self.repo).returncode, 0)
        run(["git", "tag", tag or f"v{version}"], self.repo)

    def install(self, *args, piped=False):
        """Runs install.sh, or pipes it into bash the way curl ... | bash does."""
        if piped:
            return subprocess.run([BASH, "-s", "--", *args], input=INSTALL.read_text(), env=self.env,
                                  capture_output=True, text=True)
        return subprocess.run([BASH, str(INSTALL), *args], env=self.env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True)

    def installed(self, folder):
        agd = pathlib.Path(folder) / "agd"
        self.assertTrue(os.access(agd, os.X_OK), agd)
        return subprocess.run([BASH, str(agd), "--version"], capture_output=True, text=True).stdout.strip()

    def test_script_has_no_syntax_errors(self):
        result = subprocess.run([BASH, "-n", str(INSTALL)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_piped_install_takes_the_latest_release_into_local_bin_and_says_how_to_reach_it(self):
        self.release("0.1.0")
        self.release("0.2.0")
        self.release("0.3.0", tag="v0.3.0-rc.1")
        result = self.install(piped=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.installed(self.home / ".local/bin"), "agd 0.2.0")
        self.assertIn("Installed agd 0.2.0", result.stdout)
        self.assertIn('export PATH="$HOME/.local/bin:$PATH"', result.stdout)

    def test_installs_a_given_release_then_updates_it(self):
        self.release("0.1.0")
        self.release("0.2.0")
        folder = self.home / "tools"
        self.env["PATH"] = f"{folder}:{self.env['PATH']}"
        result = self.install("--version", "0.1.0", "--dir", str(folder))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed(folder), "agd 0.1.0")
        self.assertNotIn("export PATH", result.stdout)
        result = self.install("--dir", str(folder))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed(folder), "agd 0.2.0")
        self.assertIn("Replaced agd 0.1.0 with 0.2.0", result.stdout)
        result = self.install("--dir", str(folder))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("agd 0.2.0 is already installed", result.stdout)

    def test_unknown_release_is_refused_and_nothing_is_written(self):
        self.release("0.1.0")
        self.release("0.2.0")
        result = self.install("--version", "9.9.9")
        self.assertEqual(result.returncode, 2)
        self.assertIn("9.9.9", result.stderr)
        self.assertIn("0.1.0 0.2.0", result.stderr)
        self.assertFalse((self.home / ".local").exists())

    def test_install_dir_from_the_environment_and_a_note_when_another_agd_comes_first(self):
        self.release("0.1.0")
        first, folder = self.home / "first", self.home / "tools"
        write(first, "agd", "#!/usr/bin/env bash\necho other\n")
        (first / "agd").chmod(0o755)
        self.env.update({"AGD_INSTALL_DIR": str(folder), "PATH": f"{first}:{folder}:{self.env['PATH']}"})
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed(folder), "agd 0.1.0")
        self.assertIn(f"{first}/agd comes first", result.stdout)


class AgdCase(unittest.TestCase):
    """bin/agd against a temporary source repo and cache, without network."""

    PACKS = ("min-agd 0.1.0\n\npack core\n  AGENTS.md\n  CLAUDE.md\n  .claude/agents/developer.md\n"
             "  .claude/skills/implementation/\n\npack flask requires core\n  .claude/agents/flask-developer.md\n"
             "  .claude/skills/flask/\n\npack react requires core\n  .claude/agents/react-developer.md\n"
             "  .claude/skills/react/\n")
    KIT = {
        "AGENTS.md": "<!-- agentic-defaults {v}. From agentic-defaults down to \"This project\". -->\n\n"
                     "# Working agreement\n\n- Rule one.\n\n## This project\n\n- `make test`: ...\n",
        "CLAUDE.md": "@AGENTS.md\n",
        ".claude/agents/developer.md": "---\nname: developer\ndescription: Builds things.\nmodel: haiku\n"
                                       "skills:\n  - implementation\n---\n\nDeveloper rules.\n",
        ".claude/skills/implementation/SKILL.md": "---\nname: implementation\ndescription: How to build.\n---\n\nBuild.\n",
        ".claude/skills/implementation/check.sh": "#!/usr/bin/env bash\necho ok\n",
        ".claude/agents/flask-developer.md": "---\nname: flask-developer\ndescription: Flask.\nmodel: haiku\n---\n\nFlask.\n",
        ".claude/skills/flask/SKILL.md": "---\nname: flask\ndescription: Flask practices.\n---\n\nFlask.\n",
        ".claude/agents/react-developer.md": "---\nname: react-developer\ndescription: React.\nmodel: haiku\n---\n\nReact.\n",
        ".claude/skills/react/SKILL.md": "---\nname: react\ndescription: React practices.\n---\n\nReact.\n",
    }

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.source, self.project, self.cache = base / "source", base / "project", base / "cache"
        self.source.mkdir()
        self.project.mkdir()
        run(["git", "init", "-q", "-b", "main"], self.source)
        self.env = {**GIT_ENV, "AGD_SOURCE": str(self.source), "AGD_CACHE": str(self.cache)}

    def tearDown(self):
        self._tmp.cleanup()

    def release(self, version, changes=None, packs=None):
        """Commits KIT with changes and tags it v<version>. A change of None deletes the file; files added by
        earlier changes stay until deleted. packs=False releases without packs.txt."""
        for rel, text in {**self.KIT, **(changes or {})}.items():
            if text is None:
                (self.source / "kit" / rel).unlink()
            else:
                write(self.source, f"kit/{rel}", text.replace("{v}", version))
        if packs is False:
            (self.source / "packs.txt").unlink(missing_ok=True)
        else:
            write(self.source, "packs.txt", packs or self.PACKS)
        write(self.source, "VERSION", version + "\n")
        run(["git", "add", "-A"], self.source)
        run(["git", "update-index", "--chmod=+x", "kit/.claude/skills/implementation/check.sh"], self.source)
        self.assertEqual(run(["git", "commit", "-q", "-m", version], self.source).returncode, 0)
        run(["git", "tag", f"v{version}"], self.source)

    def agd(self, *args):
        return subprocess.run([BASH, str(AGD), "-C", str(self.project), *args], env=self.env,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True)

    def agd_answering(self, answer, *args):
        """Runs agd with a terminal as its input, and types answer into it."""
        import pty

        terminal, agd_side = pty.openpty()
        try:
            process = subprocess.Popen([BASH, str(AGD), "-C", str(self.project), *args], env=self.env,
                                       stdin=agd_side, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            os.close(agd_side)
            os.write(terminal, (answer + "\n").encode())
            out, err = process.communicate(timeout=60)
        finally:
            os.close(terminal)
        return subprocess.CompletedProcess(process.args, process.returncode, out, err)

    def lock_lines(self, kind):
        lines = (self.project / ".agd.lock").read_text().splitlines()
        return [line for line in lines if line.startswith(kind + " ")]

    def blob(self, version, rel):
        return run(["git", "rev-parse", f"v{version}:kit/{rel}"], self.source).stdout.strip()


class AgdInitTest(AgdCase):
    def test_init_installs_every_pack_of_the_latest_release_and_writes_a_sorted_lock(self):
        self.release("1.0.0")
        self.release("1.1.0", {".claude/agents/developer.md": self.KIT[".claude/agents/developer.md"] + "New rule.\n"})
        result = self.agd("init")
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in self.KIT:
            self.assertTrue((self.project / rel).is_file(), rel)
        self.assertIn("New rule.", (self.project / ".claude/agents/developer.md").read_text())
        self.assertTrue(os.access(self.project / ".claude/skills/implementation/check.sh", os.X_OK))
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.1.0"])
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core", "pack agentic-defaults flask",
                                                   "pack agentic-defaults react"])
        files = self.lock_lines("file")
        self.assertEqual(files, sorted(files))
        self.assertEqual(len(files), len(self.KIT))
        developer = ".claude/agents/developer.md"
        self.assertIn(f"file agentic-defaults {developer} {self.blob('1.1.0', developer)}", files)

    def test_with_installs_only_the_named_packs_and_what_they_require(self):
        self.release("1.0.0")
        result = self.agd("init", "--with", "flask")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.project / ".claude/agents/flask-developer.md").exists())
        self.assertTrue((self.project / ".claude/agents/developer.md").exists())
        self.assertFalse((self.project / ".claude/agents/react-developer.md").exists())
        self.assertFalse((self.project / ".claude/skills/react").exists())
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core", "pack agentic-defaults flask"])

    def test_unknown_pack_is_refused_and_nothing_is_written(self):
        self.release("1.0.0")
        result = self.agd("init", "--with", "flask,vue")
        self.assertEqual(result.returncode, 2)
        self.assertIn("vue", result.stderr)
        self.assertIn("react", result.stderr)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_taken_path_is_skipped_and_reported(self):
        self.release("1.0.0")
        write(self.project, ".claude/agents/developer.md", "Our own developer.\n")
        result = self.agd("init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"taken\s+\.claude/agents/developer\.md")
        self.assertEqual((self.project / ".claude/agents/developer.md").read_text(), "Our own developer.\n")
        self.assertFalse([line for line in self.lock_lines("file") if " .claude/agents/developer.md " in line])

    def test_ignored_paths_are_not_installed(self):
        self.release("1.0.0")
        write(self.project, ".agd-ignore", "# No React agent here\n.claude/agents/react-developer.md\n")
        result = self.agd("init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.project / ".claude/agents/react-developer.md").exists())
        self.assertTrue((self.project / ".claude/skills/react/SKILL.md").exists())
        self.assertFalse([line for line in self.lock_lines("file") if "react-developer" in line])

    def test_release_without_packs_file_is_one_core_pack(self):
        self.release("1.0.0", packs=False)
        result = self.agd("init")
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in self.KIT:
            self.assertTrue((self.project / rel).is_file(), rel)
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core"])

    def test_kit_needing_a_newer_agd_is_refused(self):
        self.release("1.0.0", packs=self.PACKS.replace("min-agd 0.1.0", "min-agd 99.0.0"))
        result = self.agd("init")
        self.assertEqual(result.returncode, 2)
        self.assertIn("99.0.0", result.stderr)
        self.assertIn("https://zejnilovic.github.io/agd/install/", result.stderr)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_init_refuses_a_project_that_is_set_up(self):
        self.release("1.0.0")
        self.assertEqual(self.agd("init").returncode, 0)
        result = self.agd("init")
        self.assertEqual(result.returncode, 2)
        self.assertIn("agd status", result.stderr)

    def test_init_points_a_copied_kit_to_adopt(self):
        self.release("1.0.0")
        write(self.project, "AGENTS.md", "<!-- agentic-defaults 0.3.0. From agentic-defaults down. -->\n# Rules\n")
        result = self.agd("init")
        self.assertEqual(result.returncode, 2)
        self.assertIn("agd adopt", result.stderr)
        self.assertFalse((self.project / ".agd.lock").exists())

    def test_status_after_init_has_nothing_to_do(self):
        self.release("1.0.0")
        self.agd("init")
        result = self.agd("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing to do", result.stdout)

    def test_status_reports_a_newer_release(self):
        self.release("1.0.0")
        self.agd("init")
        self.release("1.1.0", {".claude/skills/flask/SKILL.md": "---\nname: flask\ndescription: New.\n---\n"})
        result = self.agd("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1.1.0", result.stdout)
        self.assertIn("agd update", result.stdout)
        self.assertNotIn("Nothing to do", result.stdout)

    def test_status_reports_edited_and_deleted_kit_files(self):
        self.release("1.0.0")
        self.agd("init")
        write(self.project, ".claude/skills/flask/SKILL.md", "changed\n")
        os.remove(self.project / ".claude/agents/react-developer.md")
        result = self.agd("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"edited\s+\.claude/skills/flask/SKILL\.md")
        self.assertRegex(result.stdout, r"deleted\s+\.claude/agents/react-developer\.md")
        self.assertNotIn("Nothing to do", result.stdout)

    def test_offline_works_from_the_cache_and_needs_one(self):
        self.release("1.0.0")
        result = self.agd("--offline", "init")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--offline", result.stderr)
        self.assertEqual(self.agd("init").returncode, 0)
        self.source.rename(self.source.with_name("moved"))
        result = self.agd("status")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--offline", result.stderr)
        result = self.agd("status", "--offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing to do", result.stdout)

    def test_version_matches_and_help_lists_the_commands(self):
        result = self.agd("--version")
        self.assertEqual(result.stdout.strip(), "agd " + (REPO / "VERSION").read_text().strip())
        result = self.agd("--help")
        self.assertEqual(result.returncode, 0)
        for command in ("init", "status", "--offline", "-C", "https://zejnilovic.github.io/agd"):
            self.assertIn(command, result.stdout)

    def test_unknown_command_points_to_help(self):
        result = self.agd("frobnicate")
        self.assertEqual(result.returncode, 2)
        self.assertIn("agd --help", result.stderr)


class AgdAnySourceTest(AgdCase):
    """agd with sources other than agentic-defaults, and the project file names."""

    def github(self, repo, path):
        """Makes https://github.com/<repo>.git fetch from the local path."""
        url = f"https://github.com/{repo}.git"
        self.env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": f"url.{path}.insteadOf", "GIT_CONFIG_VALUE_0": url})
        return url

    def root_source(self):
        """A repository that keeps its setup at its root, next to files that aren't part of it."""
        repo = pathlib.Path(self._tmp.name) / "team-kit"
        repo.mkdir()
        run(["git", "init", "-q", "-b", "main"], repo)
        write(repo, "README.md", "About our setup.\n")
        write(repo, "packs.txt", "root .\n\npack core\n  .claude/agents/team-reviewer.md\n  .claude/skills/team/\n")
        write(repo, ".claude/agents/team-reviewer.md", "---\nname: team-reviewer\ndescription: Reviews.\nmodel: sonnet\n---\n\nReview.\n\nCheck the tests.\n")
        write(repo, ".claude/skills/team/SKILL.md", "---\nname: team\ndescription: Our ways.\n---\n\nOur ways.\n")
        run(["git", "add", "-A"], repo)
        run(["git", "commit", "-q", "-m", "1.0.0"], repo)
        run(["git", "tag", "v1.0.0"], repo)
        return repo

    def test_project_files_have_agd_names(self):
        self.release("1.0.0")
        self.assertEqual(self.agd("init").returncode, 0)
        self.assertTrue((self.project / ".agd.lock").is_file())
        self.assertFalse((self.project / ".agentic-defaults.lock").exists())

    def test_init_from_owner_repo_names_the_source_after_the_repository(self):
        self.release("1.0.0")
        url = self.github("example/team-kit", self.source)
        result = self.agd("init", "example/team-kit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lock_lines("source"), [f"source team-kit {url} 1.0.0"])
        self.assertTrue((self.project / ".claude/agents/developer.md").is_file())

    def test_init_from_a_local_path_says_it_works_only_here(self):
        self.release("1.0.0")
        result = self.agd("init", str(self.source))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lock_lines("source"), [f"source source {self.source} 1.0.0"])
        self.assertIn("only on this machine", result.stdout)

    def test_unknown_source_form_is_refused(self):
        result = self.agd("init", "not a source")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a source isn't a git URL, a local path or a GitHub owner/repo", result.stderr)

    def test_source_with_its_setup_at_its_root_installs_only_its_packs(self):
        repo = self.root_source()
        result = self.agd("init", str(repo))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.project / ".claude/agents/team-reviewer.md").is_file())
        self.assertTrue((self.project / ".claude/skills/team/SKILL.md").is_file())
        self.assertFalse((self.project / "README.md").exists())
        self.assertFalse((self.project / "packs.txt").exists())
        self.assertIn("Nothing to do", self.agd("status").stdout)

        reviewer = ".claude/agents/team-reviewer.md"
        write(self.project, reviewer, (self.project / reviewer).read_text() + "Our line.\n")
        write(repo, reviewer, (repo / reviewer).read_text().replace("Review.", "Review carefully."))
        run(["git", "commit", "-q", "-am", "1.1.0"], repo)
        run(["git", "tag", "v1.1.0"], repo)
        diff = self.agd("diff", reviewer)
        self.assertEqual(diff.returncode, 0, diff.stderr)
        self.assertIn("+Review carefully.", diff.stdout)
        merged = self.agd("merge", reviewer)
        self.assertEqual(merged.returncode, 0, merged.stderr)
        text = (self.project / reviewer).read_text()
        self.assertIn("Review carefully.", text)
        self.assertIn("Our line.", text)

    def test_old_ignore_file_still_keeps_paths_out(self):
        self.release("1.0.0")
        write(self.project, ".agentic-defaults-ignore", ".claude/agents/react-developer.md\n")
        self.assertEqual(self.agd("init").returncode, 0)
        self.assertFalse((self.project / ".claude/agents/react-developer.md").exists())
        self.assertTrue((self.project / ".claude/agents/flask-developer.md").exists())


class AgdSourceTest(AgdCase):
    """A team's source on top of agentic-defaults."""

    DEV = ".claude/agents/developer.md"
    TEAM_REVIEWER = ".claude/agents/team-reviewer.md"

    def setUp(self):
        super().setUp()
        self.release("1.0.0")

    def team(self, files=None, packs=None, version="1.0.0", folder="team"):
        """Creates or releases a team source that keeps its setup at its root."""
        repo = pathlib.Path(self._tmp.name) / folder
        if not repo.exists():
            repo.mkdir(parents=True)
            run(["git", "init", "-q", "-b", "main"], repo)
        for rel, text in (files or {self.TEAM_REVIEWER: "---\nname: team-reviewer\ndescription: Ours.\n---\n\nReview.\n"}).items():
            write(repo, rel, text)
        write(repo, "packs.txt", packs or ("root .\n\npack review requires agentic-defaults:core\n"
                                           f"  {self.TEAM_REVIEWER}\n"))
        run(["git", "add", "-A"], repo)
        run(["git", "commit", "-q", "-m", version], repo)
        run(["git", "tag", f"v{version}"], repo)
        return repo

    def init(self, *args):
        result = self.agd("init", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def read(self, rel):
        return (self.project / rel).read_text()

    def lock(self):
        return (self.project / ".agd.lock").read_text()

    def test_init_of_a_second_source_adds_it_next_to_ours(self):
        self.init()
        team = self.team()
        self.init(str(team))
        self.assertTrue((self.project / self.TEAM_REVIEWER).is_file())
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.0.0",
                                                     f"source team {team} 1.0.0"])
        self.assertIn("pack team review", self.lock_lines("pack"))
        self.assertIn("Nothing to do", self.agd("status").stdout)

    def test_a_pack_that_requires_another_sources_pack_needs_it_installed(self):
        result = self.agd("init", str(self.team()))
        self.assertEqual(result.returncode, 2)
        self.assertIn("agentic-defaults:core", result.stderr)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_a_shared_path_stops_with_both_names_until_one_is_ignored(self):
        self.init()
        team = self.team({self.DEV: "---\nname: developer\ndescription: Team developer.\n---\n\nTeam rules.\n"},
                         "root .\n\npack devs requires agentic-defaults:core\n  .claude/agents/developer.md\n")
        before = self.lock()
        result = self.agd("init", str(team))
        self.assertEqual(result.returncode, 2)
        for text in (self.DEV, "agentic-defaults", "team:", "agentic-defaults:"):
            self.assertIn(text, result.stderr)
        self.assertEqual(self.lock(), before)

        write(self.project, ".agd-ignore", f"team:{self.DEV}\n")
        self.init(str(team))
        self.assertIn("Developer rules.", self.read(self.DEV))

        write(self.project, ".agd-ignore", f"agentic-defaults:{self.DEV}\n")
        (self.project / ".agd.lock").write_text(before)
        self.init(str(team))
        self.assertIn("Team rules.", self.read(self.DEV))
        self.assertIn(f"file team {self.DEV} ", self.lock())
        self.assertNotIn(f"file agentic-defaults {self.DEV} ", self.lock())
        self.assertIn("Nothing to do", self.agd("status").stdout)

    def team_developer(self):
        return self.team({self.DEV: "---\nname: developer\ndescription: Team developer.\n---\n\nTeam rules.\n"},
                         "root .\n\npack devs requires agentic-defaults:core\n  .claude/agents/developer.md\n")

    def test_replacing_a_changed_file_asks_first(self):
        self.init()
        write(self.project, self.DEV, self.read(self.DEV).replace("model: haiku", "model: opus"))
        write(self.project, ".agd-ignore", f"agentic-defaults:{self.DEV}\n")
        changed, before, team = self.read(self.DEV), self.lock(), self.team_developer()

        result = self.agd("init", str(team))
        self.assertEqual(result.returncode, 2)
        self.assertIn(self.DEV, result.stdout + result.stderr)
        self.assertIn("--yes", result.stderr)
        self.assertEqual((self.read(self.DEV), self.lock()), (changed, before))

        result = self.agd_answering("n", "init", str(team))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.read(self.DEV), self.lock()), (changed, before))

        result = self.agd("init", str(team), "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Team rules.", self.read(self.DEV))
        self.assertIn(f"file team {self.DEV} ", self.lock())
        self.assertNotIn(f"file agentic-defaults {self.DEV} ", self.lock())

    def test_a_file_given_away_after_an_update_is_replaced_after_asking(self):
        self.init()
        write(self.project, self.DEV, self.read(self.DEV).replace("Developer rules.", "Our rules."))
        write(self.project, ".agd-ignore", f"agentic-defaults:{self.DEV}\n")
        self.assertEqual(self.agd("update").returncode, 0)
        self.assertNotIn(f" {self.DEV} ", self.lock())
        team = self.team_developer()
        self.assertEqual(self.agd("init", str(team)).returncode, 2)
        result = self.agd("init", str(team), "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Team rules.", self.read(self.DEV))
        self.assertIn(f"file team {self.DEV} ", self.lock())

    def test_a_second_source_with_the_same_name_is_refused(self):
        self.init()
        self.init(str(self.team()))
        result = self.agd("init", str(self.team(folder="other/team")))
        self.assertEqual(result.returncode, 2)
        self.assertIn("already has a source named team", result.stderr)

    def test_update_moves_every_source(self):
        self.init()
        team = self.team()
        self.init(str(team))
        self.team({self.TEAM_REVIEWER: "---\nname: team-reviewer\ndescription: Ours.\n---\n\nReview twice.\n"},
                  version="1.1.0")
        self.assertRegex(self.agd("status").stdout, r"update\s+\.claude/agents/team-reviewer\.md")
        result = self.agd("update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Review twice.", self.read(self.TEAM_REVIEWER))
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.0.0",
                                                     f"source team {team} 1.1.0"])

    def test_source_list_and_source_remove(self):
        self.init()
        team = self.team()
        self.init(str(team))
        listing = self.agd("source", "list")
        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertIn("agentic-defaults", listing.stdout)
        self.assertIn(f"team 1.0.0 {team}", listing.stdout)
        result = self.agd("source", "remove", "agentic-defaults")
        self.assertEqual(result.returncode, 2)
        self.assertIn("team", result.stderr)
        result = self.agd("source", "remove", "team")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.project / self.TEAM_REVIEWER).exists())
        self.assertNotIn(" team ", self.lock().replace("\n", " \n"))
        self.assertIn("Nothing to do", self.agd("status").stdout)

    def test_update_to_moves_the_named_source_and_leaves_the_others(self):
        self.init()
        team = self.team()
        self.init(str(team))
        self.release("1.1.0", {self.DEV: self.KIT[self.DEV].replace("Developer rules.", "New rules.")})
        self.team({self.TEAM_REVIEWER: "---\nname: team-reviewer\ndescription: Ours.\n---\n\nReview twice.\n"},
                  version="1.1.0")
        before = self.lock()

        result = self.agd("update", "--to", "1.1.0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--to team@1.1.0", result.stderr)
        result = self.agd("update", "--to", "nobody@1.1.0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no source named nobody", result.stderr)
        self.assertEqual(self.lock(), before)

        completion = subprocess.run([BASH, str(AGD), "__complete", "update", "--to", ""], cwd=self.project,
                                    env=self.env, stdin=subprocess.DEVNULL, capture_output=True, text=True)
        self.assertEqual(completion.stdout.split(), ["agentic-defaults@1.0.0", "agentic-defaults@1.1.0",
                                                     "team@1.0.0", "team@1.1.0"])

        result = self.agd("update", "--to", "team@1.1.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Review twice.", self.read(self.TEAM_REVIEWER))
        self.assertIn("Developer rules.", self.read(self.DEV))
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.0.0",
                                                     f"source team {team} 1.1.0"])
        for kind in ("commit", "pack", "file"):
            self.assertEqual([l for l in self.lock_lines(kind) if " agentic-defaults " in l + " "],
                             [l for l in before.splitlines() if l.startswith(f"{kind} agentic-defaults ")])

    def test_a_moved_tag_of_one_of_several_sources_is_accepted_by_name(self):
        self.init()
        team = self.team()
        self.init(str(team))
        self.team({self.TEAM_REVIEWER: "---\nname: team-reviewer\ndescription: Ours.\n---\n\nApprove.\n"})
        run(["git", "tag", "-f", "v1.0.0"], team)
        result = self.agd("status")
        self.assertEqual(result.returncode, 2)
        self.assertIn("agd update --to team@1.0.0", result.stderr)
        result = self.agd("update", "--to", "team@1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Approve.", self.read(self.TEAM_REVIEWER))
        self.assertEqual(self.agd("status").returncode, 0)

    FLASK = ".claude/agents/flask-developer.md"

    def uninstallable(self):
        """Both sources installed, the developer and flask agents changed, and an ignore file."""
        self.init()
        self.init(str(self.team()))
        write(self.project, self.DEV, self.read(self.DEV).replace("Developer rules.", "Our rules."))
        write(self.project, self.FLASK, self.read(self.FLASK).replace("Flask.\n", "Our Flask.\n"))
        write(self.project, ".agd-ignore", ".claude/agents/react-developer.md\n")
        return self.lock()

    def assert_uninstalled(self, kept):
        for rel in ("AGENTS.md", "CLAUDE.md", self.TEAM_REVIEWER, ".claude/skills/implementation/SKILL.md"):
            self.assertFalse((self.project / rel).exists(), rel)
        self.assertFalse((self.project / ".claude/skills").exists())
        self.assertFalse((self.project / ".agd.lock").exists())
        self.assertTrue((self.project / ".agd-ignore").is_file())
        self.assertEqual([rel for rel in (self.DEV, self.FLASK) if (self.project / rel).exists()], kept)
        if self.DEV in kept:
            self.assertIn("Our rules.", self.read(self.DEV))

    def test_uninstall_without_a_terminal_lists_everything_and_needs_yes(self):
        before = self.uninstallable()
        result = self.agd("uninstall")
        self.assertEqual(result.returncode, 2)
        self.assertRegex(result.stdout, r"delete\s+\.claude/agents/team-reviewer\.md")
        self.assertRegex(result.stdout, r"changed\s+\.claude/agents/developer\.md")
        self.assertRegex(result.stdout, r"delete\s+\.agd\.lock")
        self.assertIn("--yes", result.stderr)
        self.assertEqual(self.lock(), before)
        self.assertTrue((self.project / "AGENTS.md").is_file())

        result = self.agd("uninstall", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_uninstalled([self.DEV, self.FLASK])
        self.assertRegex(result.stdout, r"kept\s+\.claude/agents/developer\.md")
        self.assertIn("2 kept", result.stdout)

    def test_uninstall_asks_about_each_changed_file(self):
        self.uninstallable()
        result = self.agd_answering("y\n\ny", "uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_uninstalled([self.FLASK])

    def test_uninstall_answers_for_the_rest_of_the_changed_files(self):
        self.uninstallable()
        result = self.agd_answering("a\ny", "uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_uninstalled([])

        self.uninstallable()
        result = self.agd_answering("k\ny", "uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_uninstalled([self.DEV, self.FLASK])

    def test_uninstall_answered_no_changes_nothing(self):
        before = self.uninstallable()
        result = self.agd_answering("y\ny\nn", "uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing uninstalled", result.stdout)
        self.assertEqual(self.lock(), before)
        self.assertIn("Our rules.", self.read(self.DEV))
        self.assertTrue((self.project / "AGENTS.md").is_file())


class AgdAdoptTest(AgdCase):
    """agd adopt, for copies made by hand or by scripts/sync.sh before agd."""

    DEV = ".claude/agents/developer.md"
    REACT = (".claude/agents/react-developer.md", ".claude/skills/react/SKILL.md")

    def setUp(self):
        super().setUp()
        self.release("1.0.0")

    def copy(self, skip=()):
        """Copies the 1.0.0 kit into the project, as sync.sh did."""
        for rel, text in self.KIT.items():
            if rel not in skip:
                write(self.project, rel, text.replace("{v}", "1.0.0"))

    def snapshot(self):
        return {path.relative_to(self.project).as_posix(): path.read_bytes()
                for path in self.project.rglob("*") if path.is_file()}

    def test_adopt_locks_a_copy_without_changing_any_file(self):
        self.copy()
        write(self.project, self.DEV, self.KIT[self.DEV].replace("Developer rules.", "Our developer rules."))
        before = self.snapshot()
        result = self.agd("adopt")
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.snapshot()
        self.assertEqual(after.pop(".agd.lock").count(b"\nfile "), len(self.KIT))
        self.assertEqual(after, before)
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.0.0"])
        status = self.agd("status").stdout
        self.assertRegex(status, r"(?m)^edited\s+\.claude/agents/developer\.md$")
        self.assertEqual(status.count("edited"), 1)

    def test_packs_are_those_with_files_here(self):
        self.copy(skip=self.REACT)
        self.assertEqual(self.agd("adopt").returncode, 0)
        self.assertEqual([line.split()[2] for line in self.lock_lines("pack")], ["core", "flask"])
        self.assertIn("Nothing to do", self.agd("status").stdout)

    def test_missing_files_of_a_pack_here_are_reported(self):
        self.copy(skip=self.REACT[1:])
        result = self.agd("adopt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"missing\s+\.claude/skills/react/SKILL\.md")
        self.assertRegex(self.agd("status").stdout, r"new\s+\.claude/skills/react/SKILL\.md")

    def test_old_ignore_file_keeps_paths_out_of_the_lock(self):
        self.copy()
        write(self.project, self.REACT[0], "Our own React agent.\n")
        write(self.project, ".agentic-defaults-ignore", "# Ours\n" + self.REACT[0] + "\n")
        self.assertEqual(self.agd("adopt").returncode, 0)
        self.assertFalse([line for line in self.lock_lines("file") if self.REACT[0] in line])
        self.assertEqual((self.project / self.REACT[0]).read_text(), "Our own React agent.\n")

    def test_a_copy_without_a_marker_needs_a_version(self):
        self.copy()
        write(self.project, "AGENTS.md", "# Our rules\n")
        result = self.agd("adopt")
        self.assertEqual(result.returncode, 2)
        self.assertIn("agd adopt @<version>", result.stderr)
        result = self.agd("adopt", "@1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.0.0"])

    def test_adopt_refuses_a_set_up_project_and_an_empty_one(self):
        result = self.agd("adopt", "@1.0.0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("agd init", result.stderr)
        self.assertEqual(self.agd("init").returncode, 0)
        result = self.agd("adopt")
        self.assertEqual(result.returncode, 2)
        self.assertIn("already set up", result.stderr)


class AgdPacksTest(AgdCase):
    """agd add and agd remove."""

    API_PACKS = AgdCase.PACKS + "\npack api requires flask\n  .claude/skills/api/\n"
    API_SKILL = ".claude/skills/api/SKILL.md"

    def setUp(self):
        super().setUp()
        self.release("1.0.0", {self.API_SKILL: "---\nname: api\ndescription: API rules.\n---\n"}, packs=self.API_PACKS)

    def init(self, *args):
        result = self.agd("init", *args)
        self.assertEqual(result.returncode, 0, result.stderr)

    def exists(self, rel):
        return (self.project / rel).exists()

    def locked(self, rel):
        return any(line.split()[2] == rel for line in self.lock_lines("file"))

    def test_add_installs_the_pack_and_the_packs_it_requires(self):
        self.init("--with", "react")
        result = self.agd("add", "api")
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in (self.API_SKILL, ".claude/agents/flask-developer.md", ".claude/skills/flask/SKILL.md"):
            self.assertTrue(self.exists(rel), rel)
            self.assertTrue(self.locked(rel), rel)
        self.assertEqual([line.split()[2] for line in self.lock_lines("pack")], ["api", "core", "flask", "react"])
        self.assertIn("Nothing to do", self.agd("status").stdout)

    def test_add_installs_from_the_installed_release_not_the_latest(self):
        self.init("--with", "react")
        flask = ".claude/skills/flask/SKILL.md"
        self.release("1.1.0", {flask: self.KIT[flask] + "New in 1.1.\n"}, packs=self.API_PACKS)
        self.assertEqual(self.agd("add", "flask").returncode, 0)
        self.assertNotIn("New in 1.1.", (self.project / flask).read_text())
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.0.0"])

    def test_add_skips_taken_and_ignored_paths(self):
        self.init("--with", "react")
        write(self.project, ".claude/skills/flask/SKILL.md", "Our flask notes.\n")
        write(self.project, ".agd-ignore", ".claude/agents/flask-developer.md\n")
        result = self.agd("add", "flask")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"taken\s+\.claude/skills/flask/SKILL\.md")
        self.assertEqual((self.project / ".claude/skills/flask/SKILL.md").read_text(), "Our flask notes.\n")
        self.assertFalse(self.exists(".claude/agents/flask-developer.md"))
        self.assertIn("pack agentic-defaults flask", self.lock_lines("pack"))

    def test_add_refuses_an_unknown_pack_and_names_an_installed_one(self):
        self.init("--with", "react")
        result = self.agd("add", "vue")
        self.assertEqual(result.returncode, 2)
        self.assertIn("vue", result.stderr)
        self.assertIn("flask", result.stderr)
        result = self.agd("add", "react")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already installed", result.stdout)

    def test_remove_deletes_unchanged_files_and_keeps_changed_ones(self):
        self.init()
        react_skill, react_dev = ".claude/skills/react/SKILL.md", ".claude/agents/react-developer.md"
        write(self.project, react_skill, self.KIT[react_skill] + "Our tweak.\n")
        result = self.agd("remove", "react")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.exists(react_dev))
        self.assertIn("Our tweak.", (self.project / react_skill).read_text())
        self.assertRegex(result.stdout, r"kept\s+\.claude/skills/react/SKILL\.md")
        self.assertFalse(self.locked(react_dev))
        self.assertFalse(self.locked(react_skill))
        self.assertNotIn("pack agentic-defaults react", self.lock_lines("pack"))
        self.assertIn("Nothing to do", self.agd("status").stdout)

    def test_remove_refuses_a_pack_that_others_require(self):
        self.init()
        result = self.agd("remove", "flask")
        self.assertEqual(result.returncode, 2)
        self.assertIn("api", result.stderr)
        self.assertTrue(self.exists(".claude/agents/flask-developer.md"))

    def test_remove_refuses_a_pack_that_is_not_installed(self):
        self.init("--with", "react")
        result = self.agd("remove", "flask")
        self.assertEqual(result.returncode, 2)
        self.assertIn("isn't installed", result.stderr)


class AgdRefTest(AgdCase):
    """Installing and updating to a given release or commit, and folders as sources."""

    DEV = ".claude/agents/developer.md"

    def setUp(self):
        super().setUp()
        self.release("1.0.0")

    def commit(self, text):
        """Commits a new developer agent without tagging it, and returns the commit's SHA."""
        write(self.source, f"kit/{self.DEV}", self.KIT[self.DEV].replace("Developer rules.", text))
        run(["git", "commit", "-q", "-am", text], self.source)
        return run(["git", "rev-parse", "HEAD"], self.source).stdout.strip()

    def developer(self):
        return (self.project / self.DEV).read_text()

    def test_init_at_a_version_installs_that_release(self):
        self.release("1.1.0", {self.DEV: self.KIT[self.DEV].replace("Developer rules.", "Rules of 1.1.")})
        result = self.agd("init", "@1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Developer rules.", self.developer())
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.0.0"])
        self.assertIn("1.1.0 is available", self.agd("status").stdout)

    def test_init_at_a_commit_records_its_sha_and_update_moves_to_the_latest_release(self):
        sha = self.commit("Rules from main.")
        result = self.agd("init", f"{self.source}@{sha[:10]}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Rules from main.", self.developer())
        self.assertEqual(self.lock_lines("source"), [f"source source {self.source} {sha}"])
        status = self.agd("status")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn(f"commit {sha[:7]}", status.stdout)
        self.assertIn("latest release is 1.0.0", status.stdout)
        result = self.agd("update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Developer rules.", self.developer())
        self.assertEqual(self.lock_lines("source"), [f"source source {self.source} 1.0.0"])

    def test_update_to_a_commit_made_after_init(self):
        self.assertEqual(self.agd("init").returncode, 0)
        sha = self.commit("Rules from main.")
        result = self.agd("update", "--to", sha)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Rules from main.", self.developer())
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} {sha}"])

    def test_unknown_version_or_commit_is_refused_and_nothing_written(self):
        for ref in ("9.9.9", "deadbeef123"):
            result = self.agd("init", f"@{ref}")
            self.assertEqual(result.returncode, 2, ref)
            self.assertIn(ref, result.stderr)
            self.assertEqual(list(self.project.iterdir()), [], ref)

    def test_an_existing_folder_is_a_source(self):
        result = subprocess.run([BASH, str(AGD), "-C", str(self.project), "init", "source"], cwd=self.source.parent,
                                env=self.env, stdin=subprocess.DEVNULL, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lock_lines("source"), [f"source source {self.source.resolve()} 1.0.0"])


class AgdUpdateTest(AgdCase):
    """agd status and update: one test per row of the plan's table, plus the project parts."""

    DEV = ".claude/agents/developer.md"
    FLASK_DEV = ".claude/agents/flask-developer.md"
    FLASK_SKILL = ".claude/skills/flask/SKILL.md"

    def setUp(self):
        super().setUp()
        self.release("1.0.0")

    def init(self, *args):
        result = self.agd("init", *args)
        self.assertEqual(result.returncode, 0, result.stderr)

    def update(self, *args):
        result = self.agd("update", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def status(self):
        result = self.agd("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def read(self, rel):
        return (self.project / rel).read_text()

    def kit(self, rel, old, new):
        """The kit's text of rel, with old replaced by new."""
        self.assertIn(old, self.KIT[rel])
        return self.KIT[rel].replace(old, new)

    def improved(self):
        return {self.DEV: self.kit(self.DEV, "Developer rules.", "Developer rules, improved.")}

    def locked_sha(self, rel):
        return next((line.split()[3] for line in self.lock_lines("file") if line.split()[2] == rel), None)

    def test_unchanged_file_gets_the_new_version(self):
        self.init()
        self.release("1.1.0", self.improved())
        self.assertRegex(self.status(), r"update\s+\.claude/agents/developer\.md")
        self.assertRegex(self.update(), r"updated\s+\.claude/agents/developer\.md")
        self.assertIn("Developer rules, improved.", self.read(self.DEV))
        self.assertEqual(self.locked_sha(self.DEV), self.blob("1.1.0", self.DEV))
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.1.0"])
        self.assertIn("Nothing to do", self.status())

    def test_edited_file_is_reported_and_left_alone(self):
        self.init()
        write(self.project, self.FLASK_SKILL, self.KIT[self.FLASK_SKILL] + "Our tweak.\n")
        self.release("1.1.0", self.improved())
        self.assertRegex(self.status(), r"(?m)^edited\s+\.claude/skills/flask/SKILL\.md$")
        self.update()
        self.assertIn("Our tweak.", self.read(self.FLASK_SKILL))
        self.assertEqual(self.locked_sha(self.FLASK_SKILL), self.blob("1.0.0", self.FLASK_SKILL))

    def test_edited_file_with_a_newer_kit_version_is_left_alone(self):
        self.init()
        write(self.project, self.DEV, self.kit(self.DEV, "Developer rules.", "Our developer rules."))
        self.release("1.1.0", self.improved())
        self.assertIn("newer version available", self.status())
        self.assertIn("agd merge", self.update())
        self.assertIn("Our developer rules.", self.read(self.DEV))
        self.assertNotIn("improved", self.read(self.DEV))
        self.assertEqual(self.locked_sha(self.DEV), self.blob("1.0.0", self.DEV))

    def test_deleted_file_is_not_restored(self):
        self.init()
        react = ".claude/agents/react-developer.md"
        os.remove(self.project / react)
        self.release("1.1.0", {react: self.KIT[react] + "More.\n"})
        self.assertRegex(self.update(), r"deleted\s+\.claude/agents/react-developer\.md")
        self.assertFalse((self.project / react).exists())
        self.assertIsNotNone(self.locked_sha(react))

    def test_file_removed_from_the_kit_is_deleted_unless_changed(self):
        self.init()
        react_skill = ".claude/skills/react/SKILL.md"
        write(self.project, self.FLASK_SKILL, self.KIT[self.FLASK_SKILL] + "Our tweak.\n")
        self.release("1.1.0", {react_skill: None, self.FLASK_SKILL: None})
        self.assertRegex(self.status(), r"removed\s+\.claude/skills/react/SKILL\.md")
        self.update()
        self.assertFalse((self.project / ".claude/skills/react").exists())
        self.assertIn("Our tweak.", self.read(self.FLASK_SKILL))
        self.assertIsNone(self.locked_sha(react_skill))
        self.assertIsNone(self.locked_sha(self.FLASK_SKILL))
        self.assertIn("Nothing to do", self.status())

    def test_new_files_arrive_in_selected_packs_unless_the_path_is_taken(self):
        self.init("--with", "flask")
        write(self.project, ".claude/skills/implementation/notes.md", "Our notes.\n")
        self.release("1.1.0", {".claude/skills/flask/reference.md": "Flask reference.\n",
                               ".claude/skills/react/reference.md": "React reference.\n",
                               ".claude/skills/implementation/notes.md": "Kit notes.\n"})
        status = self.status()
        self.assertRegex(status, r"new\s+\.claude/skills/flask/reference\.md")
        self.assertRegex(status, r"taken\s+\.claude/skills/implementation/notes\.md")
        self.update()
        self.assertEqual(self.read(".claude/skills/flask/reference.md"), "Flask reference.\n")
        self.assertFalse((self.project / ".claude/skills/react").exists())
        self.assertEqual(self.read(".claude/skills/implementation/notes.md"), "Our notes.\n")
        self.assertIsNotNone(self.locked_sha(".claude/skills/flask/reference.md"))

    def test_model_choice_is_kept_and_a_new_kit_default_reported(self):
        self.init()
        write(self.project, self.DEV, self.read(self.DEV).replace("model: haiku", "model: opus"))
        status = self.status()
        self.assertIn("Nothing to do", status)
        self.assertRegex(status, r"model\s+\.claude/agents/developer\.md: opus \(kit: haiku\)")
        self.release("1.1.0", {
            self.DEV: self.kit(self.DEV, "model: haiku", "model: sonnet").replace("rules.", "rules, improved."),
            self.FLASK_DEV: self.kit(self.FLASK_DEV, "model: haiku", "model: sonnet")})
        self.assertIn("kept opus; the kit now suggests sonnet", self.status())
        self.assertIn("kept opus; the kit now suggests sonnet", self.update())
        developer = self.read(self.DEV)
        self.assertIn("model: opus\n", developer)
        self.assertNotIn("sonnet", developer)
        self.assertIn("improved", developer)
        self.assertIn("model: sonnet\n", self.read(self.FLASK_DEV))

    def test_tools_entry_is_kept_in_both_forms(self):
        self.init()
        write(self.project, self.DEV, self.read(self.DEV).replace("model: haiku\n", "model: haiku\ntools: Read, Grep\n"))
        write(self.project, self.FLASK_DEV,
              self.read(self.FLASK_DEV).replace("model: haiku\n", "model: haiku\ntools:\n  - Read\n  - Bash\n"))
        status = self.status()
        self.assertNotIn("edited", status)
        self.assertRegex(status, r"tools\s+\.claude/agents/developer\.md: Read, Grep")
        self.release("1.1.0", {**self.improved(),
                               self.FLASK_DEV: self.kit(self.FLASK_DEV, "\n\nFlask.\n", "\n\nFlask, improved.\n")})
        self.update()
        self.assertIn("tools: Read, Grep\n", self.read(self.DEV))
        self.assertIn("improved", self.read(self.DEV))
        self.assertIn("tools:\n  - Read\n  - Bash\n", self.read(self.FLASK_DEV))
        self.assertIn("Flask, improved.", self.read(self.FLASK_DEV))
        self.assertIn("Nothing to do", self.status())

    def test_this_project_sections_are_kept(self):
        self.init()
        write(self.project, self.DEV, self.read(self.DEV) + "\n## This project\n\n- Use our logger.\n")
        write(self.project, "AGENTS.md", self.read("AGENTS.md").replace("`make test`: ...", "`make test`: runs pytest"))
        self.assertIn("Nothing to do", self.status())
        self.release("1.1.0", {**self.improved(), "AGENTS.md": self.kit("AGENTS.md", "- Rule one.", "- Rule one.\n- Rule two.")})
        self.update()
        developer = self.read(self.DEV)
        self.assertIn("improved", developer)
        self.assertTrue(developer.endswith("\n## This project\n\n- Use our logger.\n"), developer)
        agreement = self.read("AGENTS.md")
        self.assertIn("- Rule two.", agreement)
        self.assertIn("runs pytest", agreement)
        self.assertNotIn("`make test`: ...", agreement)
        self.assertIn("agentic-defaults 1.1.0", agreement.splitlines()[0])
        self.assertIn("Nothing to do", self.status())

    def test_crlf_copy_counts_as_unchanged(self):
        self.init()
        (self.project / self.DEV).write_bytes(self.KIT[self.DEV].replace("\n", "\r\n").encode())
        status = self.status()
        self.assertNotIn("edited", status)
        self.assertIn("Nothing to do", status)

    def test_check_exits_1_only_when_an_update_is_due(self):
        self.init()
        self.assertEqual(self.agd("status", "--check").returncode, 0)
        write(self.project, self.FLASK_SKILL, "changed\n")
        self.assertEqual(self.agd("status", "--check").returncode, 0)
        self.release("1.1.0", self.improved())
        self.assertEqual(self.agd("status", "--check").returncode, 1)
        self.update()
        self.assertEqual(self.agd("status", "--check").returncode, 0)

    def test_update_to_a_given_release(self):
        self.init()
        self.release("1.1.0", {self.DEV: self.kit(self.DEV, "Developer rules.", "Rules of 1.1.")})
        self.release("1.2.0", {self.DEV: self.kit(self.DEV, "Developer rules.", "Rules of 1.2.")})
        self.update("--to", "1.1.0")
        self.assertIn("Rules of 1.1.", self.read(self.DEV))
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} 1.1.0"])
        result = self.agd("update", "--to", "9.9.9")
        self.assertEqual(result.returncode, 2)
        self.assertIn("9.9.9", result.stderr)

    def test_github_source_links_the_notes_of_each_crossed_release(self):
        url = "https://github.com/example/kit.git"
        self.env.update({"AGD_SOURCE": url, "GIT_CONFIG_COUNT": "1",
                         "GIT_CONFIG_KEY_0": f"url.{self.source}.insteadOf", "GIT_CONFIG_VALUE_0": url})
        self.init()
        self.release("1.1.0", self.improved())
        self.release("1.2.0")
        status = self.status()
        for version in ("1.1.0", "1.2.0"):
            self.assertIn(f"https://github.com/example/kit/releases/tag/v{version}", status)
        self.assertNotIn("tag/v1.0.0", status)

    def test_project_from_a_release_without_packs_keeps_all_its_files(self):
        self.release("1.1.0", packs=False)
        self.init()
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core"])
        self.release("1.2.0")
        out = self.update()
        self.assertNotRegex(out, r"(?m)^removed ")
        self.assertIn("0 removed", out)
        for rel in self.KIT:
            self.assertTrue((self.project / rel).is_file(), rel)
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core", "pack agentic-defaults flask",
                                                   "pack agentic-defaults react"])

    def test_newly_ignored_file_is_no_longer_managed(self):
        self.init()
        react = ".claude/agents/react-developer.md"
        write(self.project, ".agd-ignore", react + "\n")
        self.assertRegex(self.update(), r"ignored\s+\.claude/agents/react-developer\.md")
        self.assertTrue((self.project / react).exists())
        self.assertIsNone(self.locked_sha(react))

    def test_new_pack_is_mentioned_but_not_installed(self):
        self.init()
        self.release("1.1.0", {".claude/skills/vue/SKILL.md": "---\nname: vue\ndescription: Vue.\n---\n"},
                     packs=self.PACKS + "\npack vue requires core\n  .claude/skills/vue/\n")
        self.assertIn("agd add vue", self.status())
        self.update()
        self.assertFalse((self.project / ".claude/skills/vue").exists())

    VUE = {".claude/skills/vue/SKILL.md": "---\nname: vue\ndescription: Vue.\n---\n"}
    VUE_PACK = "\npack vue requires core\n  .claude/skills/vue/\n"

    def test_a_pack_whose_files_were_in_the_installed_release_is_not_new(self):
        # A release without packs.txt is one pack, core: react's files were in it, vue's weren't.
        self.release("1.1.0", packs=False)
        write(self.project, ".agd-ignore", ".claude/agents/react-developer.md\n.claude/skills/react/*\n")
        self.init()
        self.release("1.2.0", self.VUE, packs=self.PACKS + self.VUE_PACK)
        status = self.status()
        self.assertNotIn("pack     react", status)
        self.assertIn("agd add vue", status)

    def test_a_new_pack_whose_files_are_all_ignored_is_not_mentioned(self):
        self.init()
        write(self.project, ".agd-ignore", ".claude/skills/vue/*\n")
        self.release("1.1.0", self.VUE, packs=self.PACKS + self.VUE_PACK)
        self.assertNotIn("vue", self.status())


class AgdMovedTagTest(AgdCase):
    """A source force-moves the tag of an installed release."""

    DEV = ".claude/agents/developer.md"

    def setUp(self):
        super().setUp()
        self.release("1.0.0")
        self.assertEqual(self.agd("init").returncode, 0)
        self.was = self.commit("v1.0.0")

    def commit(self, ref):
        return run(["git", "rev-parse", f"{ref}^{{commit}}"], self.source).stdout.strip()

    def move_tag(self):
        write(self.source, f"kit/{self.DEV}", self.KIT[self.DEV].replace("Developer rules.", "Sneaky rules."))
        run(["git", "commit", "-qam", "moved"], self.source)
        run(["git", "tag", "-f", "v1.0.0"], self.source)
        return self.commit("v1.0.0")

    def lock(self):
        return (self.project / ".agd.lock").read_text()

    def test_init_records_the_commit_behind_the_release(self):
        self.assertEqual(self.lock_lines("commit"), [f"commit agentic-defaults {self.was}"])

    def test_a_commit_install_needs_no_commit_line(self):
        self.assertEqual(self.agd("update", "--to", self.was).returncode, 0)
        self.assertEqual(self.lock_lines("source"), [f"source agentic-defaults {self.source} {self.was}"])
        self.assertEqual(self.lock_lines("commit"), [])

    def test_commands_that_read_the_release_stop_with_both_commits_and_the_change(self):
        now, before = self.move_tag(), self.lock()
        for args in (["status"], ["update"], ["reset", "--yes"], ["diff", self.DEV], ["remove", "flask"]):
            result = self.agd(*args)
            self.assertEqual(result.returncode, 2, args)
            output = result.stdout + result.stderr
            for text in (self.was, now, "-Developer rules.", "+Sneaky rules.", "agd update --to 1.0.0"):
                self.assertIn(text, output, args)
            self.assertEqual(self.lock(), before, args)
            self.assertIn("Developer rules.", (self.project / self.DEV).read_text(), args)

    def test_update_to_the_release_accepts_the_moved_tag(self):
        now = self.move_tag()
        result = self.agd("update", "--to", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Sneaky rules.", (self.project / self.DEV).read_text())
        self.assertEqual(self.lock_lines("commit"), [f"commit agentic-defaults {now}"])
        self.assertEqual(self.agd("status").returncode, 0)

    def test_a_lock_without_the_commit_is_read_and_gains_it_on_the_next_write(self):
        (self.project / ".agd.lock").write_text(
            "".join(line + "\n" for line in self.lock().splitlines() if not line.startswith("commit ")))
        result = self.agd("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("moved", result.stdout + result.stderr)
        self.assertEqual(self.lock_lines("commit"), [])
        result = self.agd("remove", "flask")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lock_lines("commit"), [f"commit agentic-defaults {self.was}"])


class AgdResolveTest(AgdCase):
    """agd diff, merge and reset, on a project set up from 1.0.0 with a five-line developer agent."""

    DEV = ".claude/agents/developer.md"
    BODY = "Line one.\nLine two.\nLine three.\nLine four.\nLine five.\n"

    def setUp(self):
        super().setUp()
        self.release("1.0.0", {self.DEV: self.dev()})
        self.assertEqual(self.agd("init").returncode, 0)

    def dev(self, old=None, new=None):
        """The kit's developer agent with the five-line body, optionally with one line changed."""
        text = self.KIT[self.DEV].replace("Developer rules.\n", self.BODY)
        return text.replace(old, new) if old else text

    def read(self, rel):
        return (self.project / rel).read_text()

    def lock_text(self):
        return (self.project / ".agd.lock").read_text()

    def test_diff_shows_your_changes_and_the_kits_and_writes_nothing(self):
        write(self.project, self.DEV, self.dev("Line one.", "Our line one."))
        self.release("1.1.0", {self.DEV: self.dev("Line five.", "Line five, improved.")})
        before = (self.read(self.DEV), self.lock_text())
        result = self.agd("diff", self.DEV)
        self.assertEqual(result.returncode, 0, result.stderr)
        for line in ("-Line one.", "+Our line one.", "-Line five.", "+Line five, improved."):
            self.assertIn(line, result.stdout)
        self.assertEqual((self.read(self.DEV), self.lock_text()), before)

    def test_commands_refuse_files_agd_does_not_manage(self):
        write(self.project, "README.md", "Ours.\n")
        for args in (["diff", "README.md"], ["merge", "README.md"], ["reset", "README.md", "--yes"]):
            result = self.agd(*args)
            self.assertEqual(result.returncode, 2, args)
            self.assertIn("README.md isn't a kit file agd manages", result.stderr)
        result = self.agd("diff")
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs a path", result.stderr)

    def test_merge_applies_a_kit_change_that_does_not_overlap(self):
        write(self.project, self.DEV, self.dev("Line one.", "Our line one.").replace("model: haiku", "model: opus")
              + "\n## This project\n\n- Use our logger.\n")
        self.release("1.1.0", {self.DEV: self.dev("Line five.", "Line five, improved.")})
        result = self.agd("merge", self.DEV)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = self.read(self.DEV)
        for expected in ("Our line one.", "Line five, improved.", "model: opus\n",
                         "\n## This project\n\n- Use our logger.\n"):
            self.assertIn(expected, text)
        self.assertNotIn("<<<<<<<", text)
        locked = [line for line in self.lock_lines("file") if f" {self.DEV} " in line]
        self.assertEqual(locked, [f"file agentic-defaults {self.DEV} {self.blob('1.1.0', self.DEV)}"])
        self.assertNotIn("newer version available", self.agd("status").stdout)

    def test_merge_marks_overlapping_changes_as_conflicts(self):
        write(self.project, self.DEV, self.dev("Line three.", "Our line three."))
        self.release("1.1.0", {self.DEV: self.dev("Line three.", "Kit line three.")})
        result = self.agd("merge", self.DEV)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("conflict", result.stdout)
        text = self.read(self.DEV)
        for expected in ("<<<<<<<", "Our line three.", "Kit line three.", ">>>>>>>"):
            self.assertIn(expected, text)

    def test_reset_of_one_file_drops_every_project_change(self):
        write(self.project, self.DEV,
              self.dev("Line two.", "Our line two.").replace("model: haiku\n", "model: opus\ntools: Read\n")
              + "\n## This project\n\n- Use our logger.\n")
        result = self.agd("reset", self.DEV, "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"reset\s+\.claude/agents/developer\.md")
        self.assertEqual(self.read(self.DEV), self.dev())
        self.assertIn("Nothing to do", self.agd("status").stdout)

    def test_reset_of_the_project_restores_kit_files_and_keeps_the_agreements_section(self):
        flask_skill = ".claude/skills/flask/SKILL.md"
        react = ".claude/agents/react-developer.md"
        flask_dev = ".claude/agents/flask-developer.md"
        write(self.project, self.DEV, self.dev("Line two.", "Our line two."))
        write(self.project, flask_skill, self.KIT[flask_skill] + "\n## This project\n\n- Ours.\n")
        os.remove(self.project / react)
        agreement = self.read("AGENTS.md").replace("`make test`: ...", "`make test`: runs pytest")
        write(self.project, "AGENTS.md", agreement)
        write(self.project, ".claude/agents/ours.md", "Our own agent.\n")
        write(self.project, flask_dev, self.KIT[flask_dev] + "Our tweak.\n")
        write(self.project, ".agd-ignore", flask_dev + "\n")
        result = self.agd("reset", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read(self.DEV), self.dev())
        self.assertEqual(self.read(flask_skill), self.KIT[flask_skill])
        self.assertEqual(self.read(react), self.KIT[react])
        self.assertEqual(self.read("AGENTS.md"), agreement)
        self.assertEqual(self.read(".claude/agents/ours.md"), "Our own agent.\n")
        self.assertIn("Our tweak.", self.read(flask_dev))

    def test_reset_asks_first_and_writes_nothing_on_no(self):
        edited = self.dev("Line two.", "Our line two.")
        write(self.project, self.DEV, edited)
        result = self.agd_answering("n", "reset")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.DEV, result.stdout)
        self.assertEqual(self.read(self.DEV), edited)
        result = self.agd_answering("y", "reset")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read(self.DEV), self.dev())

    def test_reset_without_a_terminal_needs_yes(self):
        edited = self.dev("Line two.", "Our line two.")
        write(self.project, self.DEV, edited)
        result = self.agd("reset")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--yes", result.stderr)
        self.assertEqual(self.read(self.DEV), edited)

    def test_reset_with_nothing_to_reset(self):
        result = self.agd("reset", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing to reset", result.stdout)


class WithoutGhAndFzf:
    """Runs agd with a PATH without gh and fzf; fake_fzf adds a fake one."""

    @classmethod
    def setUpClass(cls):
        # A folder with links to every other command on PATH.
        cls._bin = tempfile.TemporaryDirectory()
        for folder in os.environ["PATH"].split(os.pathsep):
            if not os.path.isdir(folder):
                continue
            for name in os.listdir(folder):
                link = os.path.join(cls._bin.name, name)
                if name not in ("gh", "fzf") and not os.path.lexists(link):
                    os.symlink(os.path.join(folder, name), link)

    @classmethod
    def tearDownClass(cls):
        cls._bin.cleanup()

    def setUp(self):
        super().setUp()
        self.env["PATH"] = self._bin.name

    def fake_fzf(self, picks, code=0):
        folder = pathlib.Path(self._tmp.name) / "fzf-bin"
        log = pathlib.Path(self._tmp.name) / "fzf.log"
        lines = "".join(f"echo '{pick}'\n" for pick in picks)
        write(folder, "fzf", f'#!/bin/sh\nprintf "%s\\n" "$@" >"{log}"\ncat >"{log}.input"\n{lines}exit {code}\n')
        (folder / "fzf").chmod(0o755)
        self.env["PATH"] = f"{folder}:{self.env['PATH']}"
        return log


class AgdInitPickTest(WithoutGhAndFzf, AgdCase):
    """agd init in a terminal, without --with, asks which packs to install."""

    CORE = "  1) core (5 files): developer agent, implementation skill\n"
    FLASK = "  2) flask (2 files, needs core): flask-developer agent, flask skill\n"

    def test_lists_the_packs_and_enter_installs_every_pack(self):
        self.release("1.0.0")
        result = self.agd_answering("", "init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.CORE + self.FLASK, result.stdout)
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core", "pack agentic-defaults flask",
                                                   "pack agentic-defaults react"])

    def test_picked_packs_come_with_the_packs_they_need(self):
        self.release("1.0.0")
        # A wrong answer is asked again; numbers and names both pick.
        result = self.agd_answering("4 vue\n3", "init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Type numbers from 1 to 3, or pack names.", result.stdout)
        self.assertIn("Installing core too: react needs it.", result.stdout)
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core", "pack agentic-defaults react"])
        self.assertFalse((self.project / ".claude/agents/flask-developer.md").exists())

    def test_fzf_picks_the_packs_when_it_is_installed(self):
        log = self.fake_fzf([self.FLASK.split(") ", 1)[1].rstrip()])
        self.release("1.0.0")
        result = self.agd_answering("", "init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--multi", log.read_text().splitlines())
        self.assertTrue(pathlib.Path(str(log) + ".input").read_text().startswith(self.CORE.split(") ", 1)[1]))
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core", "pack agentic-defaults flask"])

    def test_leaving_fzf_installs_nothing(self):
        self.fake_fzf([], code=130)
        self.release("1.0.0")
        result = self.agd_answering("", "init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing installed.", result.stdout)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_yes_with_and_a_single_pack_install_without_asking(self):
        self.release("1.0.0")
        result = self.agd_answering("", "init", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Which packs", result.stdout)
        self.assertEqual(len(self.lock_lines("pack")), 3)
        (self.project / ".agd.lock").unlink()
        shutil.rmtree(self.project / ".claude")
        for name in ("AGENTS.md", "CLAUDE.md"):
            (self.project / name).unlink()
        result = self.agd_answering("", "init", "--with", "react")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Which packs", result.stdout)
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core", "pack agentic-defaults react"])

    def test_a_release_with_one_pack_installs_without_asking(self):
        self.release("1.0.0", packs=False)
        result = self.agd_answering("", "init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Which packs", result.stdout)
        self.assertEqual(self.lock_lines("pack"), ["pack agentic-defaults core"])


class AgdFeedbackTest(WithoutGhAndFzf, AgdCase):
    """agd feedback, which only reads .agd.lock and the note, so the tests write the lock themselves."""

    GITHUB = "https://github.com/Zejnilovic/agentic-defaults.git"
    REVIEWER = ".claude/agents/reviewer.md"
    NOTE = "# The reviewer misses stale CONTEXT.md\n\nOutcome: partly done. Cause: .claude/agents/reviewer.md, rule ignored.\n"

    def setUp(self):
        super().setUp()
        self.files = {}

    def install(self, sources):
        """Writes the project files and a lock for them. sources: {name: (url, version, {path: text})}."""
        lines = ["agd-lock 1"]
        for name, (url, version, files) in sources.items():
            lines.append(f"source {name} {url} {version}")
            for path, text in files.items():
                write(self.project, path, text)
                blob = run(["git", "hash-object", str(self.project / path)], self.project).stdout.strip()
                lines.append(f"file {name} {path} {blob}")
        write(self.project, ".agd.lock", "\n".join(lines) + "\n")

    def kit(self, url=GITHUB, version="0.4.0"):
        self.install({"agentic-defaults": (url, version, {"AGENTS.md": "# Rules\n", self.REVIEWER: "Review.\n",
                                                          ".claude/skills/tdd/SKILL.md": "TDD.\n"})})

    def note(self, text=NOTE):
        write(self.project, ".local_context/feedback/note.md", text)
        return ".local_context/feedback/note.md"

    def snapshot(self):
        return {str(p): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}

    def body(self, version="0.4.0"):
        agd_version = (REPO / "VERSION").read_text().strip()
        system = " ".join(run(["uname", "-sr"], self.project).stdout.split())
        return (f"Source: agentic-defaults {version}\nagd: {agd_version}\nOS: {system}\n\nKit files:\n\n"
                f"- `{self.REVIEWER}` (as installed)\n\n---\n\n{self.NOTE}")

    def fake_gh(self):
        folder = pathlib.Path(self._tmp.name) / "gh-bin"
        log = pathlib.Path(self._tmp.name) / "gh.log"
        write(folder, "gh", '#!/bin/sh\nfor a in "$@"; do printf "%s\\n" "$a"; done >"$GH_LOG"\n'
                            'while [ $# -gt 0 ]; do [ "$1" = --body-file ] && cat "$2" >"$GH_LOG.body"; shift; done\n')
        (folder / "gh").chmod(0o755)
        self.env.update({"PATH": f"{folder}:{self._bin.name}", "GH_LOG": str(log)})
        return log

    def test_a_source_not_on_github_gets_the_title_body_and_url_printed(self):
        self.kit(url="https://git.example.com/team/kit.git")
        note = self.note()
        before = self.snapshot()
        result = self.agd("feedback", note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("https://git.example.com/team/kit.git", result.stdout)
        self.assertIn("isn't on GitHub", result.stdout)
        self.assertIn("Title: The reviewer misses stale CONTEXT.md\n", result.stdout)
        self.assertIn(self.body(), result.stdout)
        self.assertEqual(self.snapshot(), before)

    def test_changed_and_missing_files_are_marked_and_a_commit_is_labelled(self):
        self.kit(url="/srv/kits/agentic-defaults", version="ab" * 20)
        write(self.project, "AGENTS.md", "# Rules\n\nOur rule.\n")
        (self.project / ".claude/skills/tdd/SKILL.md").unlink()
        note = self.note("Seen in AGENTS.md and .claude/skills/tdd/SKILL.md, not in docs/AGENTS.md.\n")
        result = self.agd("feedback", note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Source: agentic-defaults commit abababa\n", result.stdout)
        self.assertIn("Title: Feedback on AGENTS.md\n", result.stdout)
        self.assertIn("- `AGENTS.md` (changed in the project)\n", result.stdout)
        self.assertIn("- `.claude/skills/tdd/SKILL.md` (missing in the project)\n", result.stdout)
        self.assertNotIn(self.REVIEWER, result.stdout)

    def test_longer_paths_code_blocks_and_crlf_lines_dont_count(self):
        self.kit(url="https://github.com/Zejnilovic/agentic-defaults/")
        note = self.note("```sh\n# install\n```\n\n# Backups confuse it\r\n\r\nSee AGENTS.md.orig and "
                         ".claude/agents/reviewer.md.bak, then AGENTS.md.\r\n")
        result = self.agd("feedback", note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("issues/new?title=Backups%20confuse%20it&body=", result.stdout)
        self.assertIn("%60AGENTS.md%60%20%28as%20installed%29", result.stdout)
        self.assertNotIn("%60.claude%2Fagents%2Freviewer.md%60", result.stdout)

    def test_when_gh_fails_the_link_is_printed(self):
        log = self.fake_gh()
        gh = pathlib.Path(self._tmp.name) / "gh-bin/gh"
        gh.write_text(gh.read_text() + 'echo "To get started with GitHub CLI, please run: gh auth login" >&2\nexit 4\n')
        self.kit()
        result = self.agd("feedback", self.note())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(log.exists())
        self.assertIn("gh couldn't open the issue", result.stdout)
        self.assertIn("https://github.com/Zejnilovic/agentic-defaults/issues/new?title=The%20reviewer", result.stdout)
        self.assertIn("&body=Source%3A", result.stdout)

    def test_a_note_naming_no_file_goes_to_the_only_source(self):
        self.kit(url="/srv/kits/agentic-defaults")
        result = self.agd("feedback", self.note("# Too many questions\n\nThe agents ask too often.\n"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Title: Too many questions\n", result.stdout)
        self.assertIn("Kit files: none named\n", result.stdout)
        result = self.agd("feedback", self.note("The agents ask too often.\n"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Title: Feedback on agentic-defaults 0.4.0\n", result.stdout)

    def test_the_note_must_name_one_source(self):
        self.install({"agentic-defaults": (self.GITHUB, "0.4.0", {"AGENTS.md": "# Rules\n"}),
                      "team-kit": ("https://github.com/acme/team-kit.git", "1.0.0", {".claude/agents/team.md": "Team.\n"})})
        result = self.agd("feedback", self.note("AGENTS.md and .claude/agents/team.md disagree.\n"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("agentic-defaults: AGENTS.md", result.stderr)
        self.assertIn("team-kit: .claude/agents/team.md", result.stderr)
        self.assertIn("Split the note", result.stderr)
        result = self.agd("feedback", self.note("The agents ask too often.\n"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("name a kit file", result.stderr)

    def test_feedback_needs_a_lock_and_a_note(self):
        result = self.agd("feedback", "note.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("agd init", result.stderr)
        self.kit()
        result = self.agd("feedback", "missing.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing.md", result.stderr)
        result = self.agd("feedback")
        self.assertEqual(result.returncode, 2)
        self.assertIn("agd feedback notes.md", result.stderr)
        self.assertIn("in a terminal", result.stderr)
        self.assertNotIn(".local_context", result.stderr)

    def test_without_a_note_agd_asks_and_builds_the_report_from_the_answers(self):
        from urllib.parse import parse_qs, urlsplit

        self.kit()
        before = self.snapshot()
        # A wrong number and an empty answer are asked again.
        answers = "9\n2\n\nIt wrote 40 tests for one function\nA few tests for what matters\n2"
        result = self.agd_answering(answers, "feedback")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"2) {self.REVIEWER}", result.stdout)
        url = next(line for line in result.stdout.splitlines() if line.startswith("https://"))
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query["title"], ["It wrote 40 tests for one function"])
        body = query["body"][0]
        self.assertIn(f"- `{self.REVIEWER}` (as installed)\n", body)
        for line in ("Outcome: partly done\n", "What went wrong: It wrote 40 tests for one function\n",
                     "What I expected: A few tests for what matters\n"):
            self.assertIn(line, body)
        self.assertEqual(self.snapshot(), before)

    def two_sources(self):
        self.install({"agentic-defaults": (self.GITHUB, "0.4.0", {"AGENTS.md": "# Rules\n", self.REVIEWER: "Review.\n"}),
                      "team-kit": ("https://github.com/acme/team-kit.git", "1.0.0", {".claude/agents/team.md": "Team.\n"})})

    def link(self, result):
        from urllib.parse import parse_qs, urlsplit

        url = next(line for line in result.stdout.splitlines() if line.startswith("https://"))
        parts = urlsplit(url)
        return parts.path, parse_qs(parts.query)

    def test_asked_for_several_files_by_number(self):
        self.kit()
        result = self.agd_answering("1, 3\nIt ignores both\n\n", "feedback")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = self.link(result)[1]["body"][0]
        self.assertIn("- `AGENTS.md` (as installed)\n- `.claude/skills/tdd/SKILL.md` (as installed)\n", body)
        self.assertNotIn(self.REVIEWER, body)

    def test_files_of_two_sources_are_asked_again(self):
        self.two_sources()
        result = self.agd_answering("1 3\n3\nTeam agent is slow\n\n", "feedback")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("several sources", result.stdout)
        path, query = self.link(result)
        self.assertEqual(path, "/acme/team-kit/issues/new")
        self.assertIn("- `.claude/agents/team.md` (as installed)\n", query["body"][0])

    def test_not_sure_which_file_with_two_sources_asks_for_the_source(self):
        self.two_sources()
        result = self.agd_answering("\n5\n2\nSomething is off\n\n", "feedback")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1) agentic-defaults", result.stdout)
        self.assertIn("2) team-kit", result.stdout)
        path, query = self.link(result)
        self.assertEqual(path, "/acme/team-kit/issues/new")
        self.assertIn("Kit files: none named\n", query["body"][0])
        self.assertIn("Kit file: not sure\n", query["body"][0])

    def test_fzf_picks_the_files_when_it_is_installed(self):
        log = self.fake_fzf(["AGENTS.md", self.REVIEWER])
        self.kit()
        result = self.agd_answering("Both are too long\n\n", "feedback")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--multi", log.read_text().splitlines())
        self.assertEqual(pathlib.Path(str(log) + ".input").read_text(),
                         f"AGENTS.md\n{self.REVIEWER}\n.claude/skills/tdd/SKILL.md\n")
        query = self.link(result)[1]
        self.assertEqual(query["title"], ["Both are too long"])
        self.assertIn(f"- `AGENTS.md` (as installed)\n- `{self.REVIEWER}` (as installed)\n", query["body"][0])

    def test_leaving_fzf_means_not_sure(self):
        self.fake_fzf([], code=130)
        self.two_sources()
        result = self.agd_answering("1\nSomething is off\n\n", "feedback")
        self.assertEqual(result.returncode, 0, result.stderr)
        path, query = self.link(result)
        self.assertEqual(path, "/Zejnilovic/agentic-defaults/issues/new")
        self.assertIn("Kit file: not sure\n", query["body"][0])

    def test_asked_without_a_kit_file_and_on_a_source_not_on_github(self):
        self.kit(url="https://git.example.com/team/kit.git")
        result = self.agd_answering("\nThe agents ask too often\n\n", "feedback")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("isn't on GitHub", result.stdout)
        self.assertIn("Title: The agents ask too often\n", result.stdout)
        self.assertIn("Kit files: none named\n", result.stdout)
        self.assertNotIn("Outcome:", result.stdout)
        self.assertNotIn("What I expected:", result.stdout)

    def test_without_gh_a_github_source_gets_a_prefilled_issue_link(self):
        from urllib.parse import parse_qs, urlsplit

        self.kit(url="git@github.com:Zejnilovic/agentic-defaults.git")
        note = self.note(self.NOTE.replace("partly", "partly «é» & 100%"))
        before = self.snapshot()
        result = self.agd("feedback", note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing is posted until you submit it", result.stdout)
        url = next(line for line in result.stdout.splitlines() if line.startswith("https://"))
        parts = urlsplit(url)
        self.assertEqual(parts.netloc + parts.path, "github.com/Zejnilovic/agentic-defaults/issues/new")
        query = parse_qs(parts.query, strict_parsing=True)
        self.assertEqual(query["title"], ["The reviewer misses stale CONTEXT.md"])
        self.assertEqual(query["body"], [self.body().replace("partly", "partly «é» & 100%")])
        self.assertEqual(self.snapshot(), before)

    def test_without_gh_a_long_note_gets_a_title_only_link_and_the_body_to_paste(self):
        from urllib.parse import parse_qs, urlsplit

        self.kit()
        long_note = self.NOTE + "Details.\n" * 1000
        result = self.agd("feedback", self.note(long_note))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Paste this body", result.stdout)
        url = next(line for line in result.stdout.splitlines() if line.startswith("https://"))
        self.assertEqual(parse_qs(urlsplit(url).query), {"title": ["The reviewer misses stale CONTEXT.md"]})
        self.assertIn(self.body().replace(self.NOTE, long_note), result.stdout)

    def test_gh_opens_the_issue_in_the_browser_with_the_title_and_body(self):
        log = self.fake_gh()
        self.kit(url="https://github.com/Zejnilovic/agentic-defaults")
        note = self.note()
        before = self.snapshot()
        result = self.agd("feedback", note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing is posted until you submit it", result.stdout)
        args = log.read_text().splitlines()
        self.assertEqual(args[:6], ["issue", "create", "--repo", "Zejnilovic/agentic-defaults", "--web", "--title"])
        self.assertEqual(args[6:8], ["The reviewer misses stale CONTEXT.md", "--body-file"])
        self.assertEqual(len(args), 9)
        self.assertEqual(pathlib.Path(str(log) + ".body").read_text(), self.body())
        self.assertEqual(self.snapshot(), before)

    def test_gh_gets_only_the_title_of_a_long_note(self):
        log = self.fake_gh()
        self.kit(url="ssh://git@github.com/Zejnilovic/agentic-defaults.git")
        result = self.agd("feedback", self.note(self.NOTE + "Details.\n" * 1000))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(log.read_text().splitlines(), ["issue", "create", "--repo", "Zejnilovic/agentic-defaults",
                                                        "--web", "--title", "The reviewer misses stale CONTEXT.md"])
        self.assertIn("Paste this body", result.stdout)
        self.assertIn("Details.\n" * 1000, result.stdout)


class AgdCompletionTest(AgdCase):
    """agd completion prints shell scripts that ask agd __complete for the candidates."""

    def setUp(self):
        super().setUp()
        self.release("1.0.0")
        self.release("1.1.0")
        self.assertEqual(self.agd("init", "--with", "flask").returncode, 0)
        # The scripts run agd from the PATH.
        self.bin = pathlib.Path(self._tmp.name) / "bin"
        self.bin.mkdir()
        (self.bin / "agd").symlink_to(AGD)
        self.env["PATH"] = f"{self.bin}{os.pathsep}{self.env['PATH']}"

    def complete(self, *words, cwd=None):
        """The candidates for the last word, after the words before it."""
        result = subprocess.run([BASH, str(AGD), "__complete", *words], cwd=cwd or self.project, env=self.env,
                                stdin=subprocess.DEVNULL, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return sorted(result.stdout.split())

    def test_offers_commands_then_their_options(self):
        commands = self.complete("")
        for command in ("init", "status", "update", "add", "remove", "diff", "source", "feedback", "completion"):
            self.assertIn(command, commands)
        self.assertNotIn("__complete", commands)
        self.assertEqual(self.complete("-"), ["--help", "--offline", "--version", "-C"])
        self.assertEqual(self.complete("status", "--"), ["--check", "--offline"])
        self.assertEqual(self.complete("completion", ""), ["bash", "zsh"])
        self.assertEqual(self.complete("source", ""), ["list", "remove"])
        self.assertIn("uninstall", commands)
        self.assertEqual(self.complete("uninstall", "-"), ["--offline", "--yes", "-C"])

    def test_offers_the_packs_paths_sources_and_releases_of_the_project(self):
        self.assertEqual(self.complete("add", ""), ["react"])
        self.assertEqual(self.complete("remove", ""), ["core", "flask"])
        self.assertEqual(self.complete("remove", "agentic-defaults:"), ["agentic-defaults:core", "agentic-defaults:flask"])
        self.assertIn(".claude/agents/flask-developer.md", self.complete("diff", ""))
        self.assertIn("AGENTS.md", self.complete("reset", "--yes", ""))
        self.assertEqual(self.complete("source", "remove", ""), ["agentic-defaults"])
        self.assertEqual(self.complete("update", "--to", ""), ["1.0.0", "1.1.0"])
        self.assertEqual(self.complete("update", "--to="), ["--to=1.0.0", "--to=1.1.0"])

    def test_asks_any_source_for_its_releases(self):
        src = str(self.source)
        self.env["AGD_CACHE"] = str(pathlib.Path(self._tmp.name) / "empty-cache")
        self.assertEqual(self.complete("init", f"{src}@"), [f"{src}@1.0.0", f"{src}@1.1.0"])
        self.assertEqual(self.complete("init", "./missing@"), [])
        # Packs would need the source's files, which agd doesn't fetch to complete.
        self.assertEqual(self.complete("init", src, "--with", ""), [])

    def test_reads_the_project_named_by_dash_c(self):
        elsewhere = pathlib.Path(self._tmp.name)
        self.assertEqual(self.complete("-C", str(self.project), "remove", "", cwd=elsewhere), ["core", "flask"])
        self.assertEqual(self.complete("remove", "", cwd=elsewhere), [])
        self.assertEqual(self.complete("-C", ""), [":dirs"])

    def test_offers_new_releases_without_fetching_or_writing(self):
        def snapshot():
            return sorted(str(p) for root in (self.project, self.cache) for p in root.rglob("*"))

        before = snapshot()
        self.release("1.2.0")
        self.assertEqual(self.complete("update", "--to", ""), ["1.0.0", "1.1.0", "1.2.0"])
        self.assertEqual(self.complete("--offline", "update", "--to", ""), ["1.0.0", "1.1.0"])
        self.assertEqual(snapshot(), before)

    def test_bash_script_completes_through_agd(self):
        script = self.agd("completion", "bash")
        self.assertEqual(script.returncode, 0, script.stderr)

        def tab(line):
            shell = (f'{script.stdout}\nCOMP_LINE="{line}"; COMP_POINT=${{#COMP_LINE}}; _agd\n'
                     'printf "%s\\n" "${COMPREPLY[@]}"')
            result = subprocess.run([BASH, "-c", shell], cwd=self.project, env=self.env, capture_output=True,
                                    text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return sorted(result.stdout.split())

        self.assertIn("complete -F _agd agd", script.stdout)
        self.assertEqual(tab("agd sta"), ["status"])
        self.assertEqual(tab("agd remove "), ["core", "flask"])
        # bash splits words at : and =, so it gets only what comes after them.
        self.assertEqual(tab("agd remove agentic-defaults:fl"), ["flask"])
        self.assertEqual(tab("agd update --to=1.1"), ["1.1.0"])

    def test_zsh_script_is_valid(self):
        script = self.agd("completion", "zsh")
        self.assertEqual(script.returncode, 0, script.stderr)
        self.assertTrue(script.stdout.startswith("#compdef agd\n"))
        if shutil.which("zsh"):
            write(self.project, "_agd", script.stdout)
            check = subprocess.run(["zsh", "-n", str(self.project / "_agd")], capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)

    def test_needs_a_known_shell(self):
        result = self.agd("completion", "fish")
        self.assertEqual(result.returncode, 2)
        self.assertIn("bash or zsh", result.stderr)


if __name__ == "__main__":
    unittest.main()
