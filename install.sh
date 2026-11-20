#!/usr/bin/env bash
# Installs the skills, plugins and MCP servers into Claude Code (Mac / Linux),
# turned on for every project. Run it again to update.
set -e
here="$(cd "$(dirname "$0")" && pwd)"

# 1. Skills: malayalam-type, reel-fx, video-editor, web-design (with 84 DESIGN.md files)
dst="$HOME/.claude/skills"
mkdir -p "$dst"
for d in "$here"/skills/*/; do
  name="$(basename "$d")"
  mkdir -p "$dst/$name"
  cp -R "$d". "$dst/$name/"
  echo "Installed skill $name"
done

# 2. Video tools: FFmpeg, yt-dlp, Whisper (whisper.cpp), HyperFrames and Remotion
if command -v brew >/dev/null 2>&1; then
  brew install ffmpeg yt-dlp whisper-cpp node >/dev/null 2>&1 || echo "brew could not install some video tools"
elif command -v apt-get >/dev/null 2>&1 && ! { command -v ffmpeg && command -v cmake && command -v g++; } >/dev/null 2>&1; then
  sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg git cmake build-essential python3-pip >/dev/null \
    || echo "apt-get could not install some video tools"
fi
if ! command -v yt-dlp >/dev/null 2>&1; then
  python3 -m pip install -q -U --user yt-dlp 2>/dev/null || python3 -m pip install -q -U --user --break-system-packages yt-dlp || true
fi
wdir="$HOME/.local/share/whisper.cpp"
[ -d /opt/whisper.cpp/models ] && wdir=/opt/whisper.cpp  # cloud sessions
if ! command -v whisper-cli >/dev/null 2>&1 && [ ! -x "$wdir/build/bin/whisper-cli" ]; then
  rm -rf "$wdir" && git clone -q --depth 1 https://github.com/ggml-org/whisper.cpp "$wdir" \
    && (cd "$wdir" && cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DWHISPER_BUILD_TESTS=OFF >/dev/null \
        && cmake --build build -j --target whisper-cli >/dev/null) \
    && mkdir -p "$HOME/.local/bin" && ln -sf "$wdir/build/bin/whisper-cli" "$HOME/.local/bin/whisper-cli" \
    || echo "Could not build whisper.cpp"
fi
mkdir -p "$wdir/models"
if [ ! -f "$wdir/models/ggml-base.bin" ]; then
  curl -fsSL -o "$wdir/models/ggml-base.bin" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin \
    && echo "Downloaded Whisper model to $wdir/models/ggml-base.bin" || echo "Could not download the Whisper model"
fi
if command -v npm >/dev/null 2>&1; then
  npm install -g --silent hyperframes @remotion/cli >/dev/null 2>&1 \
    || sudo npm install -g --silent hyperframes @remotion/cli >/dev/null 2>&1 || echo "Could not install HyperFrames and Remotion"
else
  echo "Node.js is missing, so HyperFrames and Remotion were skipped (install Node.js 22+ and run this again)"
fi
for t in ffmpeg yt-dlp whisper-cli hyperframes remotion; do
  if command -v "$t" >/dev/null 2>&1 || [ -x "$HOME/.local/bin/$t" ]; then echo "Video tool ready: $t"
  else echo "Video tool missing: $t"; fi
done
# Agent skills for Remotion (HyperFrames comes as a plugin below)
command -v npx >/dev/null 2>&1 && npx -y skills add remotion-dev/skills -g -y -a claude-code -s '*' --copy >/dev/null 2>&1 \
  && echo "Installed Remotion skills" || true

# Claude Code itself
if ! command -v claude >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  npm install -g --silent @anthropic-ai/claude-code >/dev/null 2>&1 \
    || sudo npm install -g --silent @anthropic-ai/claude-code >/dev/null 2>&1 || true
  command -v claude >/dev/null 2>&1 && echo "Installed Claude Code"
fi
if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code (claude) is not on PATH, so plugins and MCP servers were skipped."
  echo "Install Claude Code, then run this script again."
  exit 0
fi

# 3. Plugins: Impeccable, Refero (brings its own MCP server), HyperFrames, Watch (/watch a video),
#    Frontend Design (Anthropic's design-taste skill) and 21st.dev (component MCP + 21st-ui skill)
claude plugin marketplace add pbakaus/impeccable --scope user --sparse .claude-plugin plugin >/dev/null 2>&1 || true
claude plugin marketplace add referodesign/refero_skill --scope user >/dev/null 2>&1 || true
claude plugin marketplace add heygen-com/hyperframes --scope user >/dev/null 2>&1 || true
claude plugin marketplace add bradautomates/claude-video --scope user >/dev/null 2>&1 || true
claude plugin marketplace add anthropics/claude-plugins-official --scope user >/dev/null 2>&1 || true
claude plugin marketplace add 21st-dev/magic-mcp --scope user >/dev/null 2>&1 || true
claude plugin marketplace update impeccable >/dev/null 2>&1 || true
claude plugin marketplace update refero >/dev/null 2>&1 || true
claude plugin marketplace update hyperframes >/dev/null 2>&1 || true
claude plugin marketplace update claude-video >/dev/null 2>&1 || true
claude plugin marketplace update claude-plugins-official >/dev/null 2>&1 || true
claude plugin marketplace update 21st-dev >/dev/null 2>&1 || true
for p in impeccable@impeccable refero@refero hyperframes@hyperframes watch@claude-video \
         frontend-design@claude-plugins-official 21st@21st-dev; do
  if claude plugin install "$p" --scope user >/dev/null 2>&1; then echo "Installed plugin $p"
  else echo "Could not install plugin $p (open Claude Code and run: /plugin install $p)"; fi
  claude plugin enable "$p" --scope user >/dev/null 2>&1 || true
done

# 4. MCP servers, for every project (user scope)
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
# 21st.dev: its plugin's own server entry is missing "type": "http" and does not load, so add it here.
# The key comes from API_KEY_21ST (saved below in ~/.claude/settings.json).
add_mcp 21st --transport http 21st https://21st.dev/api/mcp --header 'x-api-key: ${API_KEY_21ST}'

# 21st.dev needs a free key (https://21st.dev/mcp). Saved in ~/.claude/settings.json so every chat has it.
cfg="$HOME/.claude/settings.json"
if [ -z "$API_KEY_21ST" ] && ! grep -q '"API_KEY_21ST"' "$cfg" 2>/dev/null && [ -t 0 ]; then
  printf "Paste your 21st.dev key from https://21st.dev/mcp (or press Enter to skip): "
  read -r key21 || key21=""
  if [ -n "$key21" ] && command -v node >/dev/null 2>&1; then
    KEY21="$key21" CFG="$cfg" node -e '
      const fs = require("fs"), f = process.env.CFG;
      const s = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : {};
      s.env = Object.assign({}, s.env, { API_KEY_21ST: process.env.KEY21 });
      fs.writeFileSync(f, JSON.stringify(s, null, 2) + "\n");' && echo "Saved your 21st.dev key"
  fi
fi

# 5. Always use the web-design stack for website work (the note is refreshed on every run)
md="$HOME/.claude/CLAUDE.md"
touch "$md"
sed '/<!-- shilpa-skills:web-design -->/,/<!-- \/shilpa-skills:web-design -->/d' "$md" | cat -s > "$md.tmp" && mv "$md.tmp" "$md"
if ! grep -q "shilpa-skills:web-design" "$md"; then
  cat >> "$md" <<'EOF'

<!-- shilpa-skills:web-design -->
For any website, landing page, web app, UI or HTML page work, always follow the `web-design` skill:
research with Refero and Firecrawl, follow the frontend-design skill, use a DESIGN.md (type scale, 8px grid,
colour tokens), build with 21st.dev and React Bits components, animate with Motion (Framer Motion), GSAP and Anime.js,
check docs with Context7, review with Impeccable, and test in Chrome DevTools (with a Lighthouse audit) before calling it done.
<!-- /shilpa-skills:web-design -->
EOF
  echo "Turned on web-design for every project in $md"
fi
if ! grep -q "shilpa-skills:video-editor" "$md"; then
  cat >> "$md" <<'EOF'

<!-- shilpa-skills:video-editor -->
For any video work (edit, cut, caption, transcribe, download, render, motion graphics), follow the `video-editor` skill:
FFmpeg, yt-dlp, Whisper (whisper.cpp), HyperFrames and Remotion are installed on this computer.
<!-- /shilpa-skills:video-editor -->
EOF
  echo "Turned on video-editor for every project in $md"
fi

echo "Done. Restart Claude Code, then run /mcp to sign in to Refero and Firecrawl."
[ -z "$API_KEY_21ST" ] && ! grep -q '"API_KEY_21ST"' "$cfg" 2>/dev/null \
  && echo "For 21st.dev components, get a free key at https://21st.dev/mcp and run this again to save it."
exit 0
