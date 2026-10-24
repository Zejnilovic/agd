#!/usr/bin/env bash
# Prints the Homebrew formula for agd <version>, whose release archive has the SHA-256 <checksum>.
# The Release workflow writes it to Formula/agd.rb in Zejnilovic/homebrew-tap.
#
# Usage: bash scripts/formula.sh <version> <sha256>

set -u
[ $# = 2 ] || { echo "Usage: bash scripts/formula.sh <version> <sha256>" >&2; exit 2; }
version=$1 sha=$2

cat <<EOF
class Agd < Formula
  desc "Install, update and combine agentic setups from git repositories"
  homepage "https://github.com/Zejnilovic/agd"
  url "https://github.com/Zejnilovic/agd/releases/download/v$version/agd-$version.tar.gz"
  sha256 "$sha"
  license "MIT"

  def install
    bin.install "bin/agd"
  end

  test do
    assert_equal "agd #{version}", shell_output("#{bin}/agd --version").strip
  end
end
EOF
