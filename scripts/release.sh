#!/usr/bin/env bash
# Prepares the release of VERSION: dates its "(unreleased)" CHANGELOG.md entry and writes the entry's
# text to a notes file for the GitHub release. Prints the version. The Release workflow runs it.
# Works with bash 3.2 (macOS) and Git Bash (Windows).
#
# Usage: bash scripts/release.sh --notes <file> [--date YYYY-MM-DD]

set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
notes="" date=$(date -u +%Y-%m-%d)
while [ $# -gt 0 ]; do
  case "$1" in
    --notes) notes=${2:-}; shift ;;
    --date) date=${2:-}; shift ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done
[ -n "$notes" ] || { echo "Usage: bash scripts/release.sh --notes <file> [--date YYYY-MM-DD]" >&2; exit 2; }

version=$(tr -d '[:space:]' < "$root/VERSION")
changelog=$root/CHANGELOG.md
heading="## $version (unreleased)"
grep -qxF "$heading" "$changelog" || { echo "CHANGELOG.md has no '$heading' entry for VERSION $version." >&2; exit 1; }

# The entry: the lines after its heading, up to the next heading.
entry=$(awk -v h="$heading" '$0 == h { on = 1; next } on && /^## / { exit } on { print }' "$changelog")
printf '%s\n' "$entry" | grep -q '^- [^[:space:]]' || { echo "CHANGELOG.md's $version entry has no bullet points." >&2; exit 1; }
if printf '%s\n' "$entry" | grep -q 'TODO'; then
  echo "CHANGELOG.md's $version entry still has a TODO: describe the change." >&2; exit 1
fi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
# Drop the entry's leading and trailing blank lines.
printf '%s\n' "$entry" | awk 'NF { started = 1 } started { lines[++n] = $0 } END { while (n > 0 && lines[n] == "") n--; for (i = 1; i <= n; i++) print lines[i] }' > "$notes"
awk -v h="$heading" -v d="## $version ($date)" '$0 == h { print d; next } { print }' "$changelog" > "$tmp" && cat "$tmp" > "$changelog"
echo "$version"
