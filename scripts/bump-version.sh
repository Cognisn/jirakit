#!/usr/bin/env bash
# Single-source version management. src/jirakit/_version.txt is the source of
# truth; pyproject.toml reads it dynamically via [tool.setuptools.dynamic].
#
# Usage:
#   scripts/bump-version.sh           Print the current version.
#   scripts/bump-version.sh 0.2.1     Set _version.txt and roll CHANGELOG.md.
set -euo pipefail

version_file="src/jirakit/_version.txt"
if [ ! -f "${version_file}" ]; then
  echo "${version_file} not found" >&2
  exit 1
fi

current=$(tr -d '[:space:]' < "${version_file}")

if [ "$#" -eq 0 ]; then
  echo "${current}"
  exit 0
fi

new="$1"
today=$(date +%F)

printf '%s\n' "${new}" > "${version_file}"
echo "_version.txt: ${current} -> ${new}"

# Python reads the version dynamically from _version.txt via pyproject.toml,
# so there is nothing further to propagate.

# Roll CHANGELOG.md: promote [Unreleased] to a dated section for this version
# and open a fresh [Unreleased] above it.
if [ -f CHANGELOG.md ]; then
  if ! grep -q '^## \[Unreleased\]' CHANGELOG.md; then
    echo "warning: CHANGELOG.md has no [Unreleased] section, leaving it unchanged" >&2
  else
    body=$(awk '
      /^## \[Unreleased\]/ {inblk=1; next}
      inblk && /^## / {exit}
      inblk {print}
    ' CHANGELOG.md | grep -Ev '^[[:space:]]*$|^###' || true)
    if [ -z "${body}" ]; then
      echo "warning: no entries under [Unreleased] to release" >&2
    fi
    awk -v ver="${new}" -v date="${today}" '
      !done && /^## \[Unreleased\]/ {
        print "## [Unreleased]"
        print ""
        print "## [" ver "] - " date
        done=1
        next
      }
      { print }
    ' CHANGELOG.md > CHANGELOG.md.tmp && mv CHANGELOG.md.tmp CHANGELOG.md
    echo "CHANGELOG.md: released ${new} (${today})"
  fi
fi
