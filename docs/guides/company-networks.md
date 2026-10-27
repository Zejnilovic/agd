# Mirrors, proxies and offline machines

agd reaches sources only through git, so it works wherever your git does: through an internal mirror, a proxy, or with no network at all. Tokens for private sources are in [the FAQ](../faq.md#can-a-source-be-private).

## An internal mirror

When your company mirrors GitHub, tell git to fetch from the mirror instead:

```bash
git config --global url."https://git.example.com/github/".insteadOf "https://github.com/"
```

Every source on GitHub, `agd init` and `agd update` included, then comes from `https://git.example.com/github/<owner>/<repo>.git`. To send only some, give a longer prefix, for example `https://github.com/Zejnilovic/`. The mirror must carry the source's tags, since releases are tags.

agd writes the public URL in `.agd.lock`, and git rewrites it on each fetch, so the lock is the same with or without the mirror, and teammates outside the company network can use it as it is:

```console
$ agd init --with core
Installed agentic-defaults 0.5.1: 27 files from the packs core.
Commit .agd.lock along with the new files.

$ grep '^source' .agd.lock
source agentic-defaults https://github.com/Zejnilovic/agentic-defaults.git 0.5.1
```

## A proxy

git's proxy settings apply to agd. Set `http.proxy`, or the `HTTPS_PROXY` variable, which git, `curl` and the install script all read:

```bash
git config --global http.proxy http://proxy.example.com:8080
# or
export HTTPS_PROXY=http://proxy.example.com:8080
```

When git can't reach the proxy, agd passes on git's message:

```console
$ HTTPS_PROXY=http://localhost:8080 agd status
fatal: unable to access 'https://github.com/Zejnilovic/agentic-defaults.git/': Failed to connect to localhost port 8080 after 0 ms: Couldn't connect to server
agd: can't fetch https://github.com/Zejnilovic/agentic-defaults.git (use --offline to work from the cache)
```

## A company certificate

A proxy that inspects HTTPS, or a mirror with an internal certificate, presents certificates signed by your company's own certificate authority (CA). Until git trusts that CA, it refuses the connection. Here, for a mirror at `https://localhost:18443/`:

```console
$ agd init --with core
fatal: unable to access 'https://localhost:18443/Zejnilovic/agentic-defaults.git/': SSL certificate problem: unable to get local issuer certificate
agd: can't fetch https://github.com/Zejnilovic/agentic-defaults.git
```

Give git the CA's certificate, a PEM file your IT department provides. For a mirror, set it for the mirror's host only, so other hosts keep the system's certificates:

```bash
git config --global http."https://git.example.com/".sslCAInfo ~/certs/company-ca.pem
```

For a proxy that inspects every connection, set `http.sslCAInfo` without a host, or the `GIT_SSL_CAINFO` variable, which works for one run, as in CI. Then agd fetches as usual:

```console
$ agd init --with core
Installed agentic-defaults 0.5.1: 27 files from the packs core.
Commit .agd.lock along with the new files.
```

To download agd's release files with `curl` through the same proxy or mirror, pass the certificate with `--cacert ~/certs/company-ca.pem`, or set `CURL_CA_BUNDLE` to it.

## A machine without a network

agd keeps a bare clone of each source in its cache, `~/.cache/agd` (or `$XDG_CACHE_HOME/agd`, or `$AGD_CACHE`), and works from it with `--offline`. Fill the cache on a connected machine, by running any agd command that fetches the sources you need, then pack it:

```bash
agd status                                     # in a project that uses the sources
tar -czf agd-cache.tar.gz -C ~/.cache agd
```

On the offline machine, unpack it and run agd with `--offline`:

```console
$ mkdir -p ~/.cache && tar -xzf agd-cache.tar.gz -C ~/.cache
$ agd init --offline --with core
Installed agentic-defaults 0.5.1: 27 files from the packs core.
Commit .agd.lock along with the new files.

$ agd status --offline
agentic-defaults 0.5.1 is installed, the latest release.
Nothing to do.
```

The cache names each source after its URL, so use the same URL on both machines; a mirror set up with `insteadOf` doesn't change it. A source that isn't in the cache stops agd:

```console
$ agd init --offline --with core
agd: no cached copy of https://github.com/Zejnilovic/agentic-defaults.git yet: run once without --offline
```

To get newer releases, fill the cache again on the connected machine and copy it over.

## Install agd itself

The [install script](../install.md#the-install-script) also fetches agd with git, from `https://github.com/Zejnilovic/agd.git`, so a mirror set up with `insteadOf` and a proxy apply to it. When `raw.githubusercontent.com` is blocked, run it from a clone, which comes from the mirror too:

```bash
git clone https://github.com/Zejnilovic/agd.git
bash agd/install.sh --version 0.3.0
```

Without git access to agd, keep a copy of a release's files, `agd` and `SHA256SUMS`, where your machines can download them, for example in an internal artifact store. Download both, check the script, and put it on your `PATH`:

```bash
curl -fsSLO https://artifacts.example.com/agd/0.3.0/agd
curl -fsSLO https://artifacts.example.com/agd/0.3.0/SHA256SUMS
shasum -a 256 -c --ignore-missing SHA256SUMS   # on Linux and in Git Bash: sha256sum
install -m 755 agd ~/.local/bin/agd
```

The check prints `agd: OK`. On a machine without any network, copy the same two files to it and run the last two lines.
