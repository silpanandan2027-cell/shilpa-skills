# Nine free apps that replace nine paid ones (Windows).
#
#   powershell -ExecutionPolicy Bypass -File apps\free-apps.ps1 install [app ...]
#   powershell -ExecutionPolicy Bypass -File apps\free-apps.ps1 start | stop | status [app ...]
#
# Desktop apps (voicestudio, openwhispr, cap) are installed here.
# The self-hosted ones (higgsfield, openseo, weknora, openproject, caldiy, chatwoot) run in
# Docker Desktop and are handled by free-apps.sh through Git Bash, so both systems behave the same.
param([string]$cmd = "status", [Parameter(ValueFromRemainingArguments = $true)][string[]]$apps)

$all = @("higgsfield", "voicestudio", "openseo", "weknora", "openwhispr", "openproject", "caldiy", "chatwoot", "cap")
$desktop = @("voicestudio", "openwhispr", "cap")
if (-not $apps -or $apps.Count -eq 0) { $apps = $all }

function Install-Release($repo, $pattern, $name, $fallback) {
  try {
    $rel = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest" -Headers @{ "User-Agent" = "installer" }
    $a = $rel.assets | Where-Object { $_.name -match $pattern -and $_.name -notmatch "arm64|aarch64" } | Select-Object -First 1
    if (-not $a) { throw "no Windows installer in the latest release" }
    $file = Join-Path $env:TEMP $a.name
    Invoke-WebRequest $a.browser_download_url -OutFile $file
    if ($file -like "*.msi") { Start-Process msiexec -ArgumentList "/i `"$file`" /passive" -Wait }
    else { Start-Process $file -Wait }
    Write-Host "  $name installed"
  } catch {
    Write-Host "  Could not install $name automatically ($($_.Exception.Message)). Opening the download page."
    Start-Process $fallback
  }
}

if ($cmd -eq "install") {
  foreach ($a in $apps | Where-Object { $desktop -contains $_ }) {
    Write-Host "Installing $a ..."
    switch ($a) {
      "voicestudio" { try { Invoke-RestMethod https://voicestudio.sh/install.ps1 | Invoke-Expression }
                      catch { Install-Release "debpalash/VoiceStudio" "\.(exe|msi)$" "VoiceStudio" "https://github.com/debpalash/VoiceStudio/releases/latest" } }
      "openwhispr"  { Install-Release "OpenWhispr/openwhispr" "\.(exe|msi)$" "OpenWhispr" "https://github.com/OpenWhispr/openwhispr/releases/latest" }
      "cap"         { Install-Release "CapSoftware/Cap" "\.(exe|msi)$" "Cap" "https://cap.so/download" }
    }
  }
  if (Get-Command claude -ErrorAction SilentlyContinue) {
    claude mcp remove --scope user voicestudio *> $null
    claude mcp add --scope user --transport http voicestudio http://localhost:3900/mcp/ *> $null
    if ($LASTEXITCODE -eq 0) { Write-Host "Added VoiceStudio MCP server to Claude Code (works while VoiceStudio is open)" }
  }
}

# Everything else goes to free-apps.sh in Git Bash.
$server = @($apps | Where-Object { $desktop -notcontains $_ })
if ($cmd -eq "status" -or $server.Count -gt 0) {
  $bash = @("$env:ProgramFiles\Git\bin\bash.exe", "${env:ProgramFiles(x86)}\Git\bin\bash.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $bash) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements *> $null
      $bash = "$env:ProgramFiles\Git\bin\bash.exe"
    }
  }
  if (-not (Test-Path $bash)) { Write-Host "Git for Windows is needed for the self-hosted apps (git-scm.com)."; exit 1 }
  if (-not (Get-Command docker -ErrorAction SilentlyContinue) -and $cmd -eq "install") {
    Write-Host "Docker Desktop is needed for the self-hosted apps."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      winget install --id Docker.DockerDesktop -e --silent --accept-package-agreements --accept-source-agreements
      Write-Host "Docker Desktop installed. Start it, wait until it says it is running, then run this again."
      exit 0
    }
  }
  $script = (Join-Path $PSScriptRoot "free-apps.sh") -replace "\\", "/"
  if ($cmd -eq "status") { & $bash $script status } else { & $bash $script $cmd @server }
}
