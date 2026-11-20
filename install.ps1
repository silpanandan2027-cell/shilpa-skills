# Installs the skills, plugins and MCP servers into Claude Code (Windows PowerShell),
# turned on for every project. Run it again to update.

# 1. Skills: malayalam-type, reel-fx, video-editor, web-design (with 84 DESIGN.md files)
$dst = Join-Path $HOME ".claude\skills"
New-Item -ItemType Directory -Force $dst | Out-Null
Get-ChildItem (Join-Path $PSScriptRoot "skills") -Directory | ForEach-Object {
  $target = Join-Path $dst $_.Name
  New-Item -ItemType Directory -Force $target | Out-Null
  Copy-Item (Join-Path $_.FullName "*") $target -Recurse -Force
  Write-Host "Installed skill $($_.Name)"
}

# 2. Video tools: FFmpeg, yt-dlp, Whisper (whisper.cpp), HyperFrames and Remotion
if (Get-Command winget -ErrorAction SilentlyContinue) {
  foreach ($id in @("Gyan.FFmpeg", "yt-dlp.yt-dlp", "OpenJS.NodeJS.LTS")) {
    winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements *> $null
  }
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
} else { Write-Host "winget is missing, so FFmpeg, yt-dlp and Node.js were skipped" }

$wdir = Join-Path $HOME ".local\whisper.cpp"
if (-not (Get-Command whisper-cli -ErrorAction SilentlyContinue) -and -not (Test-Path (Join-Path $wdir "whisper-cli.exe"))) {
  try {
    $rel = Invoke-RestMethod "https://api.github.com/repos/ggml-org/whisper.cpp/releases/latest" -Headers @{ "User-Agent" = "installer" }
    $asset = $rel.assets | Where-Object { $_.name -match "bin-x64.*\.zip$" -and $_.name -notmatch "cublas|cuda|blas" } | Select-Object -First 1
    $zip = Join-Path $env:TEMP $asset.name
    Invoke-WebRequest $asset.browser_download_url -OutFile $zip
    New-Item -ItemType Directory -Force $wdir | Out-Null
    Expand-Archive $zip -DestinationPath $wdir -Force
    $exe = Get-ChildItem $wdir -Recurse -Filter "whisper-cli.exe" | Select-Object -First 1
    if ($exe -and $exe.DirectoryName -ne $wdir) { Copy-Item (Join-Path $exe.DirectoryName "*") $wdir -Force }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$wdir*") { [Environment]::SetEnvironmentVariable("Path", "$userPath;$wdir", "User") }
    $env:Path += ";$wdir"
  } catch { Write-Host "Could not install whisper.cpp ($($_.Exception.Message))" }
}
$models = Join-Path $wdir "models"
New-Item -ItemType Directory -Force $models | Out-Null
$model = Join-Path $models "ggml-base.bin"
if (-not (Test-Path $model)) {
  try {
    Invoke-WebRequest "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin" -OutFile $model
    Write-Host "Downloaded Whisper model to $model"
  } catch { Write-Host "Could not download the Whisper model" }
}
if (Get-Command npm -ErrorAction SilentlyContinue) {
  npm install -g --silent hyperframes @remotion/cli *> $null
  npx -y skills add remotion-dev/skills -g -y -a claude-code -s '*' --copy *> $null
  if ($LASTEXITCODE -eq 0) { Write-Host "Installed Remotion skills" }
} else { Write-Host "Node.js is missing, so HyperFrames and Remotion were skipped (run this again after installing Node.js)" }
foreach ($t in @("ffmpeg", "yt-dlp", "whisper-cli", "hyperframes", "remotion")) {
  if (Get-Command $t -ErrorAction SilentlyContinue) { Write-Host "Video tool ready: $t" }
  else { Write-Host "Video tool missing: $t (open a new terminal; if still missing, run this again)" }
}

# Claude Code itself
if (-not (Get-Command claude -ErrorAction SilentlyContinue) -and (Get-Command npm -ErrorAction SilentlyContinue)) {
  npm install -g --silent @anthropic-ai/claude-code *> $null
  if (Get-Command claude -ErrorAction SilentlyContinue) { Write-Host "Installed Claude Code" }
}
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Host "Claude Code (claude) is not on PATH, so plugins and MCP servers were skipped."
  Write-Host "Install Claude Code, then run this script again."
  exit 0
}

# 3. Plugins: Impeccable, Refero (brings its own MCP server), HyperFrames, Watch (/watch a video),
#    Frontend Design (Anthropic's design-taste skill) and 21st.dev (component MCP + 21st-ui skill)
claude plugin marketplace add pbakaus/impeccable --scope user --sparse .claude-plugin plugin *> $null
claude plugin marketplace add referodesign/refero_skill --scope user *> $null
claude plugin marketplace add heygen-com/hyperframes --scope user *> $null
claude plugin marketplace add bradautomates/claude-video --scope user *> $null
claude plugin marketplace add anthropics/claude-plugins-official --scope user *> $null
claude plugin marketplace add 21st-dev/magic-mcp --scope user *> $null
claude plugin marketplace update impeccable *> $null
claude plugin marketplace update refero *> $null
claude plugin marketplace update hyperframes *> $null
claude plugin marketplace update claude-video *> $null
claude plugin marketplace update claude-plugins-official *> $null
claude plugin marketplace update 21st-dev *> $null
foreach ($p in @("impeccable@impeccable", "refero@refero", "hyperframes@hyperframes", "watch@claude-video",
                 "frontend-design@claude-plugins-official", "21st@21st-dev")) {
  claude plugin install $p --scope user *> $null
  if ($LASTEXITCODE -eq 0) { Write-Host "Installed plugin $p" }
  else { Write-Host "Could not install plugin $p (open Claude Code and run: /plugin install $p)" }
  claude plugin enable $p --scope user *> $null
}

# 4. MCP servers, for every project (user scope). '--' is quoted so PowerShell passes it on.
function Add-Mcp($name, [string[]]$mcpArgs) {
  claude mcp remove --scope user $name *> $null
  claude mcp add --scope user @mcpArgs *> $null
  if ($LASTEXITCODE -eq 0) { Write-Host "Added MCP server $name" }
  else { Write-Host "Could not add MCP server $name" }
}
Add-Mcp "chrome-devtools" @("chrome-devtools", '--', "cmd", "/c", "npx", "-y", "chrome-devtools-mcp@latest")
Add-Mcp "context7" @("--transport", "http", "context7", "https://mcp.context7.com/mcp")
Add-Mcp "firecrawl" @("--transport", "http", "firecrawl", "https://mcp.firecrawl.dev/v2/mcp-oauth")
Add-Mcp "shadcn" @("shadcn", '--', "cmd", "/c", "npx", "-y", "shadcn@latest", "mcp")
# 21st.dev: its plugin's own server entry is missing "type": "http" and does not load, so add it here.
# The key comes from API_KEY_21ST (saved below in ~/.claude/settings.json).
Add-Mcp "21st" @("--transport", "http", "21st", "https://21st.dev/api/mcp", "--header", 'x-api-key: ${API_KEY_21ST}')

# 21st.dev needs a free key (https://21st.dev/mcp). Saved in ~/.claude/settings.json so every chat has it.
$cfg = Join-Path $HOME ".claude\settings.json"
$hasKey = $env:API_KEY_21ST -or ((Test-Path $cfg) -and (Select-String -Path $cfg -Pattern '"API_KEY_21ST"' -Quiet))
if (-not $hasKey -and [Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
  $key21 = Read-Host "Paste your 21st.dev key from https://21st.dev/mcp (or press Enter to skip)"
  if ($key21) {
    $settings = if (Test-Path $cfg) { Get-Content $cfg -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    if (-not $settings.env) { $settings | Add-Member -NotePropertyName env -NotePropertyValue ([pscustomobject]@{}) -Force }
    $settings.env | Add-Member -NotePropertyName API_KEY_21ST -NotePropertyValue $key21 -Force
    $settings | ConvertTo-Json -Depth 20 | Set-Content $cfg -Encoding UTF8
    $hasKey = $true
    Write-Host "Saved your 21st.dev key"
  }
}

# 5. Always use the web-design stack for website work (the note is refreshed on every run)
$md = Join-Path $HOME ".claude\CLAUDE.md"
if (-not (Test-Path $md)) { New-Item -ItemType File -Force $md | Out-Null }
$text = Get-Content $md -Raw
if ($text) {
  $text = [regex]::Replace($text, '(\r?\n)*<!-- shilpa-skills:web-design -->[\s\S]*?<!-- /shilpa-skills:web-design -->', '')
  Set-Content -Path $md -Value $text.TrimEnd() -Encoding UTF8
}
if (-not (Select-String -Path $md -Pattern "shilpa-skills:web-design" -Quiet)) {
  $block = @"

<!-- shilpa-skills:web-design -->
For any website, landing page, web app, UI or HTML page work, always follow the ``web-design`` skill:
research with Refero and Firecrawl, follow the frontend-design skill, use a DESIGN.md (type scale, 8px grid,
colour tokens), build with 21st.dev and React Bits components, animate with Motion (Framer Motion), GSAP and Anime.js,
check docs with Context7, review with Impeccable, and test in Chrome DevTools (with a Lighthouse audit) before calling it done.
<!-- /shilpa-skills:web-design -->
"@
  Add-Content -Path $md -Value $block -Encoding UTF8
  Write-Host "Turned on web-design for every project in $md"
}
if (-not (Select-String -Path $md -Pattern "shilpa-skills:video-editor" -Quiet)) {
  $block = @"

<!-- shilpa-skills:video-editor -->
For any video work (edit, cut, caption, transcribe, download, render, motion graphics), follow the ``video-editor`` skill:
FFmpeg, yt-dlp, Whisper (whisper.cpp), HyperFrames and Remotion are installed on this computer.
<!-- /shilpa-skills:video-editor -->
"@
  Add-Content -Path $md -Value $block -Encoding UTF8
  Write-Host "Turned on video-editor for every project in $md"
}

Write-Host "Done. Restart Claude Code, then run /mcp to sign in to Refero and Firecrawl."
if (-not $hasKey) { Write-Host "For 21st.dev components, get a free key at https://21st.dev/mcp and run this again to save it." }
