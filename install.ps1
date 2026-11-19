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

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Host "Claude Code (claude) is not on PATH, so plugins and MCP servers were skipped."
  Write-Host "Install Claude Code, then run this script again."
  exit 0
}

# 3. Plugins: Impeccable, Refero (brings its own MCP server), HyperFrames and Watch (/watch a video)
claude plugin marketplace add pbakaus/impeccable --scope user --sparse .claude-plugin plugin *> $null
claude plugin marketplace add referodesign/refero_skill --scope user *> $null
claude plugin marketplace add heygen-com/hyperframes --scope user *> $null
claude plugin marketplace add bradautomates/claude-video --scope user *> $null
claude plugin marketplace update impeccable *> $null
claude plugin marketplace update refero *> $null
claude plugin marketplace update hyperframes *> $null
claude plugin marketplace update claude-video *> $null
foreach ($p in @("impeccable@impeccable", "refero@refero", "hyperframes@hyperframes", "watch@claude-video")) {
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

# 5. Always use the web-design stack for website work
$md = Join-Path $HOME ".claude\CLAUDE.md"
if (-not (Test-Path $md)) { New-Item -ItemType File -Force $md | Out-Null }
if (-not (Select-String -Path $md -Pattern "shilpa-skills:web-design" -Quiet)) {
  $block = @"

<!-- shilpa-skills:web-design -->
For any website, landing page, web app, UI or HTML page work, always follow the ``web-design`` skill:
research with Refero and Firecrawl, use a DESIGN.md, build with React Bits, GSAP and Anime.js,
check docs with Context7, review with Impeccable, and test in Chrome DevTools before calling it done.
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
