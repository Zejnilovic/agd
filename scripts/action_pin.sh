#!/usr/bin/env bash
# Moves a checkout of Zejnilovic/agd-action to a new agd release: writes agd-release and adds a bullet to
# the "(unreleased)" entry of its CHANGELOG.md, which it starts or raises by the level of the agd release
# (patch -> patch, minor -> minor). Prints the action version to release. The Release workflow runs it.
# Exits 3, changing nothing, on a new agd major version: that is a new action major, released by hand.
# Works with bash 3.2 (macOS) and Git Bash (Windows).
#
# Usage: bash scripts/action_pin.sh <agd-action folder> <agd version> <sha256 of the release's agd>

set -u
dir=${1:-} new=${2:-} sum=${3:-}
if [ -z "$dir" ] || ! printf '%s\n' "$new" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' \
  || ! printf '%s\n' "$sum" | grep -Eq '^[0-9a-f]{64}$'; then
  echo "Usage: bash scripts/action_pin.sh <agd-action folder> <agd version x.y.z> <sha256>" >&2; exit 2
fi
pin=$dir/agd-release changelog=$dir/CHANGELOG.md

old=$(awk '$1 == "version" { print $2 }' "$pin")
if [ "$old" = "$new" ]; then
  echo "agd-action already runs agd $new." >&2; exit 0
fi
old_major=${old%%.*} new_major=${new%%.*}
if [ "$old_major" != "$new_major" ]; then
  echo "agd $new is a new major version, and agd-action runs agd $old: release agd-action's next major version by hand." >&2
  exit 3
fi
old_minor=${old#*.}; old_minor=${old_minor%%.*}
new_minor=${new#*.}; new_minor=${new_minor%%.*}
level=patch
[ "$old_minor" = "$new_minor" ] || level=minor

# The next version after the last release, at that level; an unreleased entry's own version wins if higher.
last=$(grep -E '^## [0-9]+\.[0-9]+\.[0-9]+ \([0-9]{4}-' "$changelog" | head -n 1 | sed 's/^## \([^ ]*\) .*/\1/')
unreleased=$(grep -E '^## [0-9]+\.[0-9]+\.[0-9]+ \(unreleased\)$' "$changelog" | head -n 1 | sed 's/^## \([^ ]*\) .*/\1/')
next=""
if [ -n "$last" ]; then
  next=$(printf '%s\n' "$last" | awk -F. -v l="$level" '{ if (l == "minor") print $1 "." $2 + 1 ".0"; else print $1 "." $2 "." $3 + 1 }')
fi
version=$(printf '%s\n%s\n' "$next" "$unreleased" | awk -F. 'NF == 3 { v = $1 * 1000000 + $2 * 1000 + $3; if (v > best) { best = v; out = $0 } } END { print out }')
[ -n "$version" ] || { echo "$changelog has no released or unreleased version to start from." >&2; exit 1; }

bullet="- Runs [agd $new](https://github.com/Zejnilovic/agd/releases/tag/v$new)."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
if [ -n "$unreleased" ]; then
  # The new bullet goes first in the entry, under its raised heading.
  awk -v h="## $unreleased (unreleased)" -v d="## $version (unreleased)" -v b="$bullet" '
    $0 == h { print d; print ""; print b; skip = 1; next }
    skip && $0 == "" { skip = 0; next }
    { skip = 0; print }
  ' "$changelog" > "$tmp"
else
  awk -v d="## $version (unreleased)" -v b="$bullet" '
    !done && /^## / { print d; print ""; print b; print ""; done = 1 }
    { print }
  ' "$changelog" > "$tmp"
fi
cat "$tmp" > "$changelog"
printf 'version %s\nsha256 %s\n' "$new" "$sum" > "$pin"
echo "$version"
