. "$PSScriptRoot\_transition_common.ps1"

$workspace = Get-TransitionWorkspaceRoot
$repo = Get-TransitionRepoRoot
$report = New-TransitionReportPath -Prefix "05_worktree_audit"
$dirs = Get-ChildItem -LiteralPath $workspace -Directory -Force | Where-Object { $_.Name -like "coproscope-agent-*" }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Audit worktrees")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- Workspace: $(Format-TransitionCode $workspace)")
$lines.Add("- Candidate directories: $($dirs.Count)")
$lines.Add("")

if ($dirs.Count -eq 0) {
    $lines.Add("No $(Format-TransitionCode 'coproscope-agent-*') directories found under workspace.")
    $lines.Add("")
}

foreach ($dir in $dirs) {
    $gitPath = Join-Path $dir.FullName ".git"
    $gitTarget = ""
    if (Test-Path -LiteralPath $gitPath) {
        $item = Get-Item -LiteralPath $gitPath -Force
        $gitTarget = if ($item.PSIsContainer) { "<directory>" } else { (Get-Content -LiteralPath $gitPath -Raw).Trim() }
    }
    $status = Invoke-TransitionCommand -FilePath "git" -Arguments @("status", "--short", "--branch") -WorkingDirectory $dir.FullName
    $pointsDrive = $gitTarget -match 'G:[\\/]'
    $lines.Add("## $($dir.Name)")
    $lines.Add("")
    $lines.Add("- Path: $(Format-TransitionCode $dir.FullName)")
    $lines.Add("- .git kind: $(Get-TransitionPathKind $gitPath)")
    $lines.Add("- Git target: $(Format-TransitionCode $gitTarget)")
    $lines.Add("- Points to Drive: $pointsDrive")
    $lines.Add("- Git status exit: $($status.ExitCode)")
    $lines.Add("")
    Add-TransitionCommandReportSection -Lines $lines -Title "$($dir.Name) git status" -Result $status
}

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
