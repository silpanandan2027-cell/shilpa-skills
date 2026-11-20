#!/usr/bin/env bash
# Nine free apps that replace nine paid ones. Installs, starts, stops and checks them.
#
#   apps/free-apps.sh install [app ...]   install (all nine when no app is named)
#   apps/free-apps.sh start   [app ...]   start the self-hosted ones
#   apps/free-apps.sh stop    [app ...]   stop them
#   apps/free-apps.sh status              which are installed and answering
#
# Apps: higgsfield voicestudio openseo weknora openwhispr openproject caldiy chatwoot cap
# Desktop apps (voicestudio, openwhispr, cap) install like any other app.
# The rest run in Docker under ~/free-apps, each on its own port (see PORTS below).
set -e

ROOT="${FREE_APPS_DIR:-$HOME/free-apps}"
ALL="higgsfield voicestudio openseo weknora openwhispr openproject caldiy chatwoot cap"
SERVERS="higgsfield openseo weknora openproject caldiy chatwoot"

# One port per app, so they can all run at once.
port() {
  case "$1" in
    higgsfield) echo 3100 ;;   # Open Higgsfield
    voicestudio) echo 3900 ;;  # VoiceStudio backend (API and MCP at /mcp/)
    openseo) echo 3001 ;;
    weknora) echo 3200 ;;      # web UI; API on 8180
    openproject) echo 8090 ;;
    caldiy) echo 3000 ;;       # the Cal.diy image is built for localhost:3000
    chatwoot) echo 3400 ;;
    *) echo "" ;;
  esac
}

os="$(uname -s)"
say() { printf '%s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
secret() { openssl rand -hex "${1:-32}" 2>/dev/null || head -c "${1:-32}" /dev/urandom | od -An -tx1 | tr -d ' \n'; }
setenv() { # setenv FILE KEY VALUE: replace KEY=... (commented or not) or append it
  f="$1"; k="$2"; v="$3"
  if grep -qE "^#? *$k=" "$f"; then
    awk -v k="$k" -v v="$v" 'BEGIN{d=0} $0 ~ "^#? *"k"=" && !d {print k"="v; d=1; next} {print}' "$f" >"$f.tmp" && mv "$f.tmp" "$f"
  else
    printf '%s=%s\n' "$k" "$v" >>"$f"
  fi
}
clone() { # clone REPO DIR: fresh shallow clone, or pull if it is already there
  if [ -d "$2/.git" ]; then git -C "$2" pull -q --ff-only || true
  else git clone -q --depth 1 "https://github.com/$1.git" "$2"; fi
}
need_docker() {
  if ! have docker || ! docker info >/dev/null 2>&1; then
    say "  Docker is not running. Install Docker Desktop (docker.com), start it, and run this again."
    return 1
  fi
}
# Latest GitHub release asset whose name matches a regex.
asset() {
  curl -fsSL "https://api.github.com/repos/$1/releases/latest" 2>/dev/null \
    | grep -o '"browser_download_url": *"[^"]*"' | sed 's/.*"\(http[^"]*\)"/\1/' | grep -Ei "$2" | head -1
}
linux_pkg() { # install a .deb / .AppImage from a GitHub release
  repo="$1"; name="$2"
  if have dpkg && url="$(asset "$repo" 'amd64\.deb$|x86_64\.deb$|\.deb$')" && [ -n "$url" ]; then
    curl -fsSL -o "/tmp/$name.deb" "$url" && sudo apt-get install -y -qq "/tmp/$name.deb" >/dev/null && return 0
  fi
  if url="$(asset "$repo" '\.AppImage$')" && [ -n "$url" ]; then
    mkdir -p "$HOME/Applications" && curl -fsSL -o "$HOME/Applications/$name.AppImage" "$url" \
      && chmod +x "$HOME/Applications/$name.AppImage" && say "  Saved to ~/Applications/$name.AppImage" && return 0
  fi
  return 1
}

# ---------- install ----------
install_app() {
  case "$1" in
  higgsfield)
    have node || { say "  Needs Node.js 22+ (nodejs.org)"; return 1; }
    have pnpm || corepack enable >/dev/null 2>&1 || npm install -g pnpm >/dev/null
    clone wide-trace/open-higgsfield "$ROOT/open-higgsfield"
    (cd "$ROOT/open-higgsfield" && pnpm install --silent && pnpm build >/dev/null) || return 1
    ;;
  voicestudio)
    if [ "$os" = Darwin ] && have brew; then
      brew tap debpalash/tap >/dev/null && brew trust --cask debpalash/tap/voicestudio >/dev/null 2>&1 || true
      brew install --cask debpalash/tap/voicestudio
    else
      curl -fsSL https://voicestudio.sh/install | sh
    fi
    ;;
  openwhispr)
    if have brew; then brew install --cask openwhispr
    elif [ "$os" = Linux ]; then linux_pkg OpenWhispr/openwhispr openwhispr \
      || { say "  Download it from github.com/OpenWhispr/openwhispr/releases/latest"; return 1; }
    fi
    ;;
  cap)
    if [ "$os" = Darwin ] && have brew; then brew install --cask cap
    else linux_pkg CapSoftware/Cap cap || { say "  Download it from cap.so/download"; return 1; }
    fi
    ;;
  openseo)
    need_docker || return 1
    d="$ROOT/open-seo"; clone every-app/open-seo "$d"
    e="$d/deploy/standalone/.env"
    [ -f "$e" ] || { cp "$d/deploy/standalone/.env.example" "$e"; setenv "$e" STORAGE_SECRET_KEY "$(secret)"; }
    [ -n "$DATAFORSEO_API_KEY" ] && setenv "$e" DATAFORSEO_API_KEY "$DATAFORSEO_API_KEY"
    grep -qE '^DATAFORSEO_API_KEY=.+' "$e" || say "  Add your DataForSEO key: DATAFORSEO_API_KEY in $e (base64 of login:password)"
    (cd "$d" && COMPOSE_FILE=deploy/standalone/compose.yaml docker compose pull -q) || return 1
    ;;
  weknora)
    need_docker || return 1
    d="$ROOT/WeKnora"; clone Tencent/WeKnora "$d"
    [ -f "$d/.env" ] || { cp "$d/.env.example" "$d/.env"; setenv "$d/.env" FRONTEND_PORT 3200; setenv "$d/.env" APP_PORT 8180; }
    (cd "$d" && docker compose pull -q) || return 1
    say "  For local models, install Ollama (ollama.com) and pick it in WeKnora's model settings."
    ;;
  openproject)
    need_docker || return 1
    d="$ROOT/openproject"; mkdir -p "$d/pgdata" "$d/assets"
    [ -f "$d/secret" ] || secret 64 >"$d/secret"
    docker pull -q openproject/openproject:17 >/dev/null || return 1
    ;;
  caldiy)
    need_docker || return 1
    d="$ROOT/cal.diy"; clone calcom/cal.diy "$d"
    if [ ! -f "$d/.env" ]; then
      cp "$d/.env.example" "$d/.env"
      setenv "$d/.env" NEXTAUTH_SECRET "$(openssl rand -base64 32)"
      setenv "$d/.env" CALENDSO_ENCRYPTION_KEY "$(openssl rand -base64 24)"
      setenv "$d/.env" POSTGRES_USER calcom
      setenv "$d/.env" POSTGRES_PASSWORD "$(secret 16)"
      setenv "$d/.env" POSTGRES_DB calendso
      setenv "$d/.env" DATABASE_HOST database:5432
      setenv "$d/.env" REDIS_PORT 6380
      setenv "$d/.env" API_PORT 3003
      if have npx && keys="$(npx -y web-push generate-vapid-keys --json 2>/dev/null)"; then
        setenv "$d/.env" NEXT_PUBLIC_VAPID_PUBLIC_KEY "$(printf '%s' "$keys" | sed 's/.*"publicKey":"\([^"]*\)".*/\1/')"
        setenv "$d/.env" VAPID_PRIVATE_KEY "$(printf '%s' "$keys" | sed 's/.*"privateKey":"\([^"]*\)".*/\1/')"
      fi
    fi
    # No ready-made Cal.diy image is published, so it is built here (takes a while, needs about 8 GB of RAM).
    (cd "$d" && docker compose pull -q database && docker compose build calcom) || return 1
    say "  Calendar sync: add your Google / Outlook app keys in $d/.env (see the Cal.diy README)."
    ;;
  chatwoot)
    need_docker || return 1
    d="$ROOT/chatwoot"; mkdir -p "$d"
    base=https://raw.githubusercontent.com/chatwoot/chatwoot/develop
    [ -f "$d/docker-compose.yaml" ] || curl -fsSL -o "$d/docker-compose.yaml" "$base/docker-compose.production.yaml"
    if [ ! -f "$d/.env" ]; then
      curl -fsSL -o "$d/.env" "$base/.env.example"
      pw="$(secret 16)"; rpw="$(secret 16)"
      setenv "$d/.env" SECRET_KEY_BASE "$(secret 64)"
      setenv "$d/.env" FRONTEND_URL "http://localhost:3400"
      setenv "$d/.env" RAILS_ENV production
      setenv "$d/.env" POSTGRES_PASSWORD "$pw"
      setenv "$d/.env" REDIS_PASSWORD "$rpw"
      setenv "$d/.env" REDIS_URL "redis://:$rpw@redis:6379"
    fi
    cat >"$d/compose.override.yaml" <<'EOF'
services:
  rails:
    ports: !override
      - "127.0.0.1:3400:3000"
  postgres:
    ports: !reset []
    environment: !override
      - POSTGRES_DB=chatwoot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  redis:
    ports: !reset []
EOF
    (cd "$d" && docker compose -f docker-compose.yaml -f compose.override.yaml pull -q \
      && docker compose -f docker-compose.yaml -f compose.override.yaml run --rm rails bundle exec rails db:chatwoot_prepare >/dev/null) || return 1
    ;;
  *) say "Unknown app: $1 (apps: $ALL)"; return 1 ;;
  esac
}

# ---------- start / stop ----------
start_app() {
  case "$1" in
  higgsfield)
    d="$ROOT/open-higgsfield"; [ -d "$d" ] || return 1
    (cd "$d" && nohup pnpm start -p 3100 >"$ROOT/open-higgsfield.log" 2>&1 & echo $! >"$ROOT/open-higgsfield.pid")
    ;;
  openseo) (cd "$ROOT/open-seo" && COMPOSE_FILE=deploy/standalone/compose.yaml docker compose up -d) ;;
  weknora) (cd "$ROOT/WeKnora" && docker compose up -d) ;;
  openproject)
    d="$ROOT/openproject"
    docker start openproject >/dev/null 2>&1 || docker run -d --name openproject --restart unless-stopped \
      -p 127.0.0.1:8090:80 -e SECRET_KEY_BASE="$(cat "$d/secret")" \
      -e OPENPROJECT_HOST__NAME=localhost:8090 -e OPENPROJECT_HTTPS=false -e OPENPROJECT_DEFAULT__LANGUAGE=en \
      -v "$d/pgdata:/var/openproject/pgdata" -v "$d/assets:/var/openproject/assets" openproject/openproject:17 >/dev/null
    ;;
  caldiy) (cd "$ROOT/cal.diy" && docker compose up -d database calcom) ;;
  chatwoot) (cd "$ROOT/chatwoot" && docker compose -f docker-compose.yaml -f compose.override.yaml up -d) ;;
  voicestudio|openwhispr|cap) say "  $1 is a desktop app: open it from your apps menu." ;;
  esac
}
stop_app() {
  case "$1" in
  higgsfield) [ -f "$ROOT/open-higgsfield.pid" ] && kill "$(cat "$ROOT/open-higgsfield.pid")" 2>/dev/null; rm -f "$ROOT/open-higgsfield.pid" ;;
  openseo) (cd "$ROOT/open-seo" && COMPOSE_FILE=deploy/standalone/compose.yaml docker compose stop) ;;
  weknora) (cd "$ROOT/WeKnora" && docker compose stop) ;;
  openproject) docker stop openproject >/dev/null ;;
  caldiy) (cd "$ROOT/cal.diy" && docker compose stop) ;;
  chatwoot) (cd "$ROOT/chatwoot" && docker compose -f docker-compose.yaml -f compose.override.yaml stop) ;;
  esac
}

status() {
  for a in $ALL; do
    p="$(port "$a")"
    if [ -n "$p" ] && curl -s -o /dev/null -m 3 "http://localhost:$p"; then s="running   http://localhost:$p"
    else
      case "$a" in
        higgsfield) d=open-higgsfield ;; openseo) d=open-seo ;; weknora) d=WeKnora ;; caldiy) d=cal.diy ;; *) d="$a" ;;
      esac
      if [ -d "$ROOT/$d" ]; then s="installed, stopped"
      elif [ "$a" = voicestudio ] || [ "$a" = openwhispr ] || [ "$a" = cap ]; then s="desktop app (open it from your apps)"
      else s="not installed"; fi
    fi
    printf '  %-12s %s\n' "$a" "$s"
  done
}

cmd="${1:-status}"; [ $# -gt 0 ] && shift
apps="${*:-$ALL}"
mkdir -p "$ROOT"
case "$cmd" in
  install)
    for a in $apps; do
      say "Installing $a ..."
      if install_app "$a"; then say "  $a installed"; else say "  $a NOT installed (see above)"; fi
    done
    if have claude; then # VoiceStudio's MCP server: Claude can speak, clone and transcribe with it
      claude mcp remove --scope user voicestudio >/dev/null 2>&1 || true
      claude mcp add --scope user --transport http voicestudio http://localhost:3900/mcp/ >/dev/null 2>&1 \
        && say "Added VoiceStudio MCP server to Claude Code (works while VoiceStudio is open)"
    fi
    say "Next: apps/free-apps.sh start   then   apps/free-apps.sh status"
    ;;
  start)  for a in $apps; do say "Starting $a"; start_app "$a" || say "  $a is not installed"; done; status ;;
  stop)   for a in $apps; do stop_app "$a" || true; done; status ;;
  status) status ;;
  *) sed -n 2,11p "$0"; exit 1 ;;
esac
