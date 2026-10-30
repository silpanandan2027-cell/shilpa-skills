#!/usr/bin/env bash
# Installs the skills into Claude Code (Mac / Linux). Run it again to update.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
dst="$HOME/.claude/skills"
mkdir -p "$dst"
for d in "$here"/skills/*/; do
  name="$(basename "$d")"
  mkdir -p "$dst/$name"
  cp -R "$d". "$dst/$name/"
  echo "Installed $name"
done
echo "Done. Restart Claude Code."
