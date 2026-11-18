#!/usr/bin/env bash
# Installs the skills, plugins and MCP servers into Claude Code (Mac / Linux),
# turned on for every project. Run it again to update.
set -e
here="$(cd "$(dirname "$0")" && pwd)"

# 1. Skills: malayalam-type, reel-fx, web-design (with 84 DESIGN.md files)
dst="$HOME/.claude/skills"
mkdir -p "$dst"
for d in "$here"/skills/*/; do
  name="$(basename "$d")"
  mkdir -p "$dst/$name"
  cp -R "$d". "$dst/$name/"
  echo "Installed skill $name"
done

if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code (claude) is not on PATH, so plugins and MCP servers were skipped."
  echo "Install Claude Code, then run this script again."
  exit 0
fi

# 2. Plugins: Impeccable and Refero (Refero brings its own MCP server)
claude plugin marketplace add pbakaus/impeccable --scope user --sparse .claude-plugin plugin >/dev/null 2>&1 || true
claude plugin marketplace add referodesign/refero_skill --scope user >/dev/null 2>&1 || true
claude plugin marketplace update impeccable >/dev/null 2>&1 || true
claude plugin marketplace update refero >/dev/null 2>&1 || true
for p in impeccable@impeccable refero@refero; do
  if claude plugin install "$p" --scope user >/dev/null 2>&1; then echo "Installed plugin $p"
  else echo "Could not install plugin $p (open Claude Code and run: /plugin install $p)"; fi
  claude plugin enable "$p" --scope user >/dev/null 2>&1 || true
done

# 3. MCP servers, for every project (user scope)
add_mcp() {
  name="$1"; shift
  claude mcp remove --scope user "$name" >/dev/null 2>&1 || true
  if claude mcp add --scope user "$@" >/dev/null 2>&1; then echo "Added MCP server $name"
  else echo "Could not add MCP server $name"; fi
}
add_mcp chrome-devtools chrome-devtools -- npx -y chrome-devtools-mcp@latest
add_mcp context7 --transport http context7 https://mcp.context7.com/mcp
add_mcp firecrawl --transport http firecrawl https://mcp.firecrawl.dev/v2/mcp-oauth
add_mcp shadcn shadcn -- npx -y shadcn@latest mcp

# 4. Always use the web-design stack for website work
md="$HOME/.claude/CLAUDE.md"
touch "$md"
if ! grep -q "shilpa-skills:web-design" "$md"; then
  cat >> "$md" <<'EOF'

<!-- shilpa-skills:web-design -->
For any website, landing page, web app, UI or HTML page work, always follow the `web-design` skill:
research with Refero and Firecrawl, use a DESIGN.md, build with React Bits, GSAP and Anime.js,
check docs with Context7, review with Impeccable, and test in Chrome DevTools before calling it done.
<!-- /shilpa-skills:web-design -->
EOF
  echo "Turned on web-design for every project in $md"
fi

echo "Done. Restart Claude Code, then run /mcp to sign in to Refero and Firecrawl."
