. "$PSScriptRoot\_transition_common.ps1"

$workspace = Get-TransitionWorkspaceRoot
$repo = Get-TransitionRepoRoot
$report = New-TransitionReportPath -Prefix "07_cleanup_root_venv_dryrun"
$rootVenv = Join-Path $workspace ".venv"
$serverPython = Join-Path $repo "server\.venv\Scripts\python.exe"
$inventory = Get-ChildItem -LiteralPath (Get-TransitionReportDir) -Filter "02_venv_inventory*.md" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$rebuild = Get-ChildItem -LiteralPath (Get-TransitionReportDir) -Filter "04_rebuild_server_venv*.md" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$excludedPycachePathPattern = '[\\/](\.git|\.venv)[\\/]'
$pycacheSample = @(Get-ChildItem -LiteralPath $workspace -Directory -Recurse -Force -Filter "__pycache__" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch $excludedPycachePathPattern } | Select-Object -First 201)
$pycache = @($pycacheSample | Select-Object -First 200)
$pycacheTruncated = $pycacheSample.Count -gt 200
$inventoryPath = if ($null -ne $inventory) { $inventory.FullName } else { "" }
$rebuildPath = if ($null -ne $rebuild) { $rebuild.FullName } else { "" }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Cleanup root venv dry-run")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- Root venv: $(Format-TransitionCode $rootVenv)")
$lines.Add("- Root venv exists: $(Test-Path -LiteralPath $rootVenv)")
$lines.Add("- Server python exists: $(Test-Path -LiteralPath $serverPython)")
$lines.Add("- Latest inventory report: $(Format-TransitionCode $inventoryPath)")
$lines.Add("- Latest rebuild report: $(Format-TransitionCode $rebuildPath)")
$lines.Add("- Pycache scan excludes: $(Format-TransitionCode '.git'), $(Format-TransitionCode '.venv')")
$lines.Add("- Pycache entries shown: $($pycache.Count)")
$lines.Add("- Pycache list truncated: $pycacheTruncated")
$lines.Add("")
$lines.Add("## Automatic action in 08")
$lines.Add("")
if (Test-Path -LiteralPath $rootVenv) {
    $lines.Add("- Archive and remove $(Format-TransitionCode $rootVenv)")
}
else {
    $lines.Add("(nothing)")
}
$lines.Add("")
$lines.Add("## Pycache candidates for manual review")
$lines.Add("")
$lines.Add("The execute batch does not remove these paths automatically.")
$lines.Add("")
if ($pycache.Count -eq 0) {
    $lines.Add("(none)")
}
else {
    foreach ($dir in $pycache) { $lines.Add("- $(Format-TransitionCode $dir.FullName)") }
}

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
