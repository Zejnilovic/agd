#!/usr/bin/env bash
# Starts a new agd version: updates VERSION and the version= line of bin/agd, and adds an
# "(unreleased)" CHANGELOG.md heading with a TODO to replace.
# Works with bash 3.2 (macOS) and Git Bash (Windows).
#
# Usage: bash scripts/bump.sh <major.minor.patch>
#   patch  fixes
#   minor  new commands or options
#   major  changes that need manual steps in projects or sources (the lock or packs.txt format)

set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
new="${1:-}"

case "$new" in
  -h|--help|"") sed -n '2,10p' "$0"; [ -n "$new" ]; exit $? ;;
esac
if ! printf '%s\n' "$new" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Version must look like 1.2.3, got: $new" >&2; exit 2
fi

current=$(tr -d '[:space:]' < "$root/VERSION")
# Compare numerically, part by part.
greater=$(awk -v a="$new" -v b="$current" 'BEGIN {
  split(a, x, "."); split(b, y, ".")
  for (i = 1; i <= 3; i++) { if (x[i] + 0 > y[i] + 0) { print 1; exit } if (x[i] + 0 < y[i] + 0) { print 0; exit } }
  print 0 }')
if [ "$greater" != 1 ]; then
  echo "New version $new must be greater than the current $current." >&2; exit 2
fi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

printf '%s\n' "$new" > "$root/VERSION"

# cat into the file, not mv, so bin/agd keeps its executable bit.
sed "s/^version=[0-9][0-9.]*\$/version=$new/" "$root/bin/agd" > "$tmp" && cat "$tmp" > "$root/bin/agd"

# Insert the new heading before the first section.
awk -v v="$new" '
  function entry() { print "## " v " (unreleased)"; print ""; print "- TODO: describe the change" }
  !done && /^## / { entry(); print ""; done = 1 }
  { print }
  END { if (!done) { print ""; entry() } }
' "$root/CHANGELOG.md" > "$tmp" && cat "$tmp" > "$root/CHANGELOG.md"

echo "Bumped $current -> $new: VERSION, bin/agd and CHANGELOG.md."
echo "Next: replace the TODO in CHANGELOG.md with what changed."
