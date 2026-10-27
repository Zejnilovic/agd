# Install agd

agd is one bash script. It needs bash 3.2 or newer and git: macOS and Linux have both, and on Windows, Git Bash does. Choose one way to install it.

=== "Homebrew"

    On macOS or Linux:

    ```bash
    brew install zejnilovic/tap/agd
    ```

    Update it with `brew upgrade agd`.

=== "Install script"

    On macOS, Linux, WSL or Git Bash:

    ```bash
    curl -fsSL https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh | bash
    ```

    It puts the latest release in `~/.local/bin`, and tells you when that folder isn't on your `PATH`. Run it again to update. [What it does](#the-install-script).

=== "By hand"

    Download the script from the latest release, into a folder on your `PATH`, and make it executable:

    ```bash
    curl -fLo ~/.local/bin/agd https://github.com/Zejnilovic/agd/releases/latest/download/agd
    chmod +x ~/.local/bin/agd
    ```

    To update, download it again. Each release also has the archive `agd-<version>.tar.gz`, with the script in `bin/agd`, and [checksums](#check-a-download).

=== "From a clone"

    To try the latest changes, or to work on agd:

    ```bash
    git clone https://github.com/Zejnilovic/agd.git ~/src/agd
    ln -s ~/src/agd/bin/agd ~/.local/bin/agd
    ```

    `main` is the next release in progress. To run a release instead, check out its tag, for example `git -C ~/src/agd checkout v0.1.1`.

Then check that it runs:

```bash
agd --version
```

## Put agd on your PATH

The install script and the steps by hand use `~/.local/bin`, which many Linux systems already have on the `PATH`. If yours doesn't, add this line to your shell's profile (`~/.zshrc` for zsh, the default on macOS; `~/.bashrc` for bash and Git Bash), then open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Tab completion

Tab completes agd's commands, options, packs, installed paths and releases. Homebrew sets it up for you, when your shell loads Homebrew's completions. Otherwise, add a line to your shell's profile, then open a new terminal:

=== "zsh"

    In `~/.zshrc`, after `compinit` runs (frameworks such as Oh My Zsh run it):

    ```bash
    source <(agd completion zsh)
    ```

    Without a framework, run `compinit` first: `autoload -Uz compinit && compinit`.

=== "bash"

    In `~/.bashrc` (on macOS, `~/.bash_profile`):

    ```bash
    source <(agd completion bash)
    ```

## The install script

[`install.sh`](https://github.com/Zejnilovic/agd/blob/main/install.sh) is short, and you can read it before you run it:

```bash
curl -fsSLO https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh
less install.sh
bash install.sh
```

It finds the newest release tag with `git ls-remote`, downloads that release with a shallow `git clone`, checks that its `bin/agd` runs and reports the release's version, and copies it into place. It doesn't use `sudo`, and doesn't change your shell's profile.

| Option | Does |
|---|---|
| `--version <x.y.z>` | Installs that release instead of the latest, for example to pin agd in CI. |
| `--dir <folder>` | Installs into `<folder>`. The default is `$AGD_INSTALL_DIR`, or `~/.local/bin`. |

Pass options through the pipe with `bash -s --`:

```bash
curl -fsSL https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh | bash -s -- --version 0.1.1 --dir /usr/local/bin
```

## Check a download

Each release lists the SHA-256 checksums of its files in `SHA256SUMS`. In the folder where you downloaded `agd`:

```bash
curl -fsSLO https://github.com/Zejnilovic/agd/releases/latest/download/SHA256SUMS
shasum -a 256 -c --ignore-missing SHA256SUMS
```

On Linux and in Git Bash, `sha256sum -c --ignore-missing SHA256SUMS` does the same.

## Windows

Run agd in Git Bash, which comes with [Git for Windows](https://git-scm.com/download/win), or in WSL. Install it there with the install script, by hand, or from a clone. In Git Bash, add `~/.local/bin` to the `PATH` in `~/.bashrc` as [shown above](#put-agd-on-your-path).

## Uninstall

Remove the script, and the cache of sources agd keeps:

```bash
rm ~/.local/bin/agd        # or: brew uninstall agd
rm -rf ~/.cache/agd
```

Projects keep the files agd installed. To stop managing them with agd too, delete the project's `.agd.lock`; its files are then plain project files.
