# Installs the skills, plugins and MCP servers into Claude Code (Windows PowerShell),
# turned on for every project. Run it again to update.

# 1. Skills: malayalam-type, reel-fx, web-design (with 84 DESIGN.md files)
$dst = Join-Path $HOME ".claude\skills"
New-Item -ItemType Directory -Force $dst | Out-Null
Get-ChildItem (Join-Path $PSScriptRoot "skills") -Directory | ForEach-Object {
  $target = Join-Path $dst $_.Name
  New-Item -ItemType Directory -Force $target | Out-Null
  Copy-Item (Join-Path $_.FullName "*") $target -Recurse -Force
  Write-Host "Installed skill $($_.Name)"
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Host "Claude Code (claude) is not on PATH, so plugins and MCP servers were skipped."
  Write-Host "Install Claude Code, then run this script again."
  exit 0
}

# 2. Plugins: Impeccable and Refero (Refero brings its own MCP server)
claude plugin marketplace add pbakaus/impeccable --scope user --sparse .claude-plugin plugin *> $null
claude plugin marketplace add referodesign/refero_skill --scope user *> $null
claude plugin marketplace update impeccable *> $null
claude plugin marketplace update refero *> $null
foreach ($p in @("impeccable@impeccable", "refero@refero")) {
  claude plugin install $p --scope user *> $null
  if ($LASTEXITCODE -eq 0) { Write-Host "Installed plugin $p" }
  else { Write-Host "Could not install plugin $p (open Claude Code and run: /plugin install $p)" }
  claude plugin enable $p --scope user *> $null
}

# 3. MCP servers, for every project (user scope). '--' is quoted so PowerShell passes it on.
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

# 4. Always use the web-design stack for website work
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

Write-Host "Done. Restart Claude Code, then run /mcp to sign in to Refero and Firecrawl."
