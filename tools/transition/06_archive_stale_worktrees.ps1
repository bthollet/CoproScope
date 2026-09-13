param([switch]$Execute)
. "$PSScriptRoot\_transition_common.ps1"

$workspace = Get-TransitionWorkspaceRoot
$archiveRoot = Join-Path (Join-Path $workspace "_archives") ("worktrees_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
$report = New-TransitionReportPath -Prefix "06_archive_stale_worktrees"
$dirs = @(Get-ChildItem -LiteralPath $workspace -Directory -Force | Where-Object { $_.Name -like "coproscope-agent-*" })
$lines = New-Object System.Collections.Generic.List[string]
$actions = New-Object System.Collections.Generic.List[object]
$lines.Add("# Archive stale worktrees")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- Execute: $Execute")
$lines.Add("- Archive root: $(Format-TransitionCode $archiveRoot)")
$lines.Add("- Candidate directories: $($dirs.Count)")
$lines.Add("")

foreach ($dir in $dirs) {
    $gitPath = Join-Path $dir.FullName ".git"
    $gitTarget = if (Test-Path -LiteralPath $gitPath -PathType Leaf) { (Get-Content -LiteralPath $gitPath -Raw).Trim() } else { "" }
    $pointsDrive = $gitTarget -match 'G:[\\/]'
    $porcelain = Invoke-TransitionCommand -FilePath "git" -Arguments @("status", "--porcelain") -WorkingDirectory $dir.FullName
    $clean = ($porcelain.ExitCode -eq 0 -and [string]::IsNullOrWhiteSpace($porcelain.Output))
    $candidate = $pointsDrive -and $clean
    $action = if ($candidate) { "candidate" } else { "skip" }
    if ($Execute -and $candidate) {
        $resolved = (Resolve-Path -LiteralPath $dir.FullName).Path
        if (-not (Test-TransitionPathInsideRoot -Path $resolved -Root $workspace)) {
            throw "Refusing to move path outside workspace: $resolved"
        }
        New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null
        Move-Item -LiteralPath $resolved -Destination (Join-Path $archiveRoot $dir.Name)
        $action = "archived"
    }
    $actions.Add([pscustomobject]@{
        Name = $dir.Name
        Path = $dir.FullName
        PointsDrive = $pointsDrive
        Clean = $clean
        Candidate = $candidate
        StatusExit = $porcelain.ExitCode
        Action = $action
    })
}

$lines.Add("## Summary")
$lines.Add("")
$lines.Add("- Drive pointers: $(@($actions | Where-Object { $_.PointsDrive }).Count)")
$lines.Add("- Clean candidates: $(@($actions | Where-Object { $_.Candidate }).Count)")
$lines.Add("- Archived: $(@($actions | Where-Object { $_.Action -eq 'archived' }).Count)")
$lines.Add("")
$lines.Add("## Worktrees")
$lines.Add("")
if ($actions.Count -eq 0) {
    $lines.Add("(none)")
}
else {
    $lines.Add("| Name | Points Drive | Clean | Candidate | Git exit | Action |")
    $lines.Add("|---|---:|---:|---:|---:|---:|")
    foreach ($action in $actions) {
        $lines.Add("| $(Format-TransitionCode $action.Name) | $($action.PointsDrive) | $($action.Clean) | $($action.Candidate) | $($action.StatusExit) | $($action.Action) |")
    }
}

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
