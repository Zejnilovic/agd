#!/usr/bin/env bash
# Installs agd, or updates it: puts bin/agd of the latest release, or of the given one, in a folder on
# your PATH. Needs only bash and git, like agd. Works with bash 3.2 (macOS) and Git Bash (Windows).
# Run it again to update. bash install.sh --help lists the options.
#
#   curl -fsSL https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh | bash

set -u

usage() {
  cat <<'EOF'
Installs agd, or updates it to the latest release.

Usage: bash install.sh [--version <x.y.z>] [--dir <folder>]
       curl -fsSL https://raw.githubusercontent.com/Zejnilovic/agd/main/install.sh | bash -s -- [options]
  --version <x.y.z>   install that release instead of the latest
  --dir <folder>      install into <folder> instead of $AGD_INSTALL_DIR, or ~/.local/bin
EOF
}

die() { echo "install.sh: $*" >&2; exit 2; }

# Everything runs from main, called on the last line, so a download cut short installs nothing.
main() {
  local repo=https://github.com/Zejnilovic/agd.git
  local want="" dir=${AGD_INSTALL_DIR:-$HOME/.local/bin} releases v old where profile_dir
  while [ $# -gt 0 ]; do
    case "$1" in
      --version) [ $# -ge 2 ] || die "--version needs a release, for example --version 0.1.1"; want=$2; shift ;;
      --version=*) want=${1#--version=} ;;
      --dir) [ $# -ge 2 ] || die "--dir needs a folder"; dir=$2; shift ;;
      --dir=*) dir=${1#--dir=} ;;
      -h|--help) usage; return 0 ;;
      *) die "unknown argument $1 (see --help)" ;;
    esac
    shift
  done
  want=${want#v}
  command -v git >/dev/null 2>&1 || die "agd needs git: install git, then run this again"

  # Not local: the EXIT trap runs after main returns.
  tmp=$(mktemp -d) || die "can't create a temporary folder"
  trap 'rm -rf "$tmp"' EXIT

  # Releases are the tags v<major.minor.patch>, as for every agd source.
  if ! git ls-remote --tags --refs "$repo" 'v*' </dev/null >"$tmp/tags" 2>"$tmp/git.err"; then
    cat "$tmp/git.err" >&2; die "can't reach $repo"
  fi
  releases=$(sed -n 's#^[0-9a-f]*[[:space:]]*refs/tags/v\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)$#\1#p' "$tmp/tags" \
    | sort -t. -k1,1n -k2,2n -k3,3n)
  [ -n "$releases" ] || die "$repo has no releases"
  if [ -n "$want" ]; then
    printf '%s\n' "$releases" | grep -qxF -- "$want" || die "agd has no release $want. Releases: $(echo $releases)"
    v=$want
  else
    v=$(printf '%s\n' "$releases" | tail -1)
  fi

  if ! git -c advice.detachedHead=false clone -q --depth 1 --branch "v$v" "$repo" "$tmp/agd" </dev/null 2>"$tmp/git.err"; then
    cat "$tmp/git.err" >&2; die "can't download agd $v"
  fi
  [ "$(bash "$tmp/agd/bin/agd" --version 2>/dev/null </dev/null)" = "agd $v" ] || die "release $v has no working bin/agd"

  mkdir -p "$dir" 2>/dev/null && dir=$(cd "$dir" && pwd) || die "can't create $dir"
  old=""
  [ ! -f "$dir/agd" ] || old=$(bash "$dir/agd" --version 2>/dev/null </dev/null | sed -n 's/^agd //p')
  if [ "$old" = "$v" ]; then
    echo "agd $v is already installed in $dir."
  else
    # Write a new file and move it into place, so a running agd is never half replaced.
    cp "$tmp/agd/bin/agd" "$dir/agd.new" && chmod +x "$dir/agd.new" && mv -f "$dir/agd.new" "$dir/agd" \
      || die "can't write $dir/agd"
    if [ -n "$old" ]; then echo "Replaced agd $old with $v in $dir."; else echo "Installed agd $v in $dir."; fi
  fi

  case ":$PATH:" in
    *":$dir:"*)
      where=$(command -v agd 2>/dev/null)
      [ -z "$where" ] || [ "$where" = "$dir/agd" ] || echo "Note: $where comes first on your PATH, so agd runs that copy."
      ;;
    *)
      profile_dir=$dir
      case "$dir" in "$HOME"/*) profile_dir="\$HOME/${dir#"$HOME"/}" ;; esac
      echo "$dir isn't on your PATH. Add this line to your shell's profile (~/.zshrc, ~/.bashrc), then open a new terminal:"
      echo "  export PATH=\"$profile_dir:\$PATH\""
      ;;
  esac
  echo "Get started: https://zejnilovic.github.io/agd/quick-start/"
}

main "$@"
