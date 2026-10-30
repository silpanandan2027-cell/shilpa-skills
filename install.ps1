# Installs the skills into Claude Code (Windows PowerShell). Run it again to update.
$dst = Join-Path $HOME ".claude\skills"
New-Item -ItemType Directory -Force $dst | Out-Null
Get-ChildItem (Join-Path $PSScriptRoot "skills") -Directory | ForEach-Object {
  $target = Join-Path $dst $_.Name
  New-Item -ItemType Directory -Force $target | Out-Null
  Copy-Item (Join-Path $_.FullName "*") $target -Recurse -Force
  Write-Host "Installed $($_.Name)"
}
Write-Host "Done. Restart Claude Code."
