. "$PSScriptRoot\_transition_common.ps1"

$workspace = Get-TransitionWorkspaceRoot
$repo = Get-TransitionRepoRoot
$report = New-TransitionReportPath -Prefix "00_audit_local"

$checks = @(
    $repo,
    (Join-Path $repo ".git"),
    (Join-Path $repo "README.md"),
    (Join-Path $repo "server\pyproject.toml"),
    (Join-Path $repo "docs"),
    (Join-Path $repo "examples"),
    (Join-Path $repo "server\src")
)

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Audit local readonly")
$lines.Add("")
$lines.Add("- Workspace: $(Format-TransitionCode $workspace)")
$lines.Add("- Repo: $(Format-TransitionCode $repo)")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("")

$gitStatus = Invoke-TransitionCommand -FilePath "git" -Arguments @("status", "--short", "--branch") -WorkingDirectory $repo
$worktrees = Invoke-TransitionCommand -FilePath "git" -Arguments @("worktree", "list", "--porcelain") -WorkingDirectory $repo
$missingChecks = @($checks | Where-Object { -not (Test-Path -LiteralPath $_) })
$driveRefs = @($worktrees.Output -split "`r?`n" | Where-Object { $_ -match 'G:[\\/]' })

$lines.Add("## Summary")
$lines.Add("")
$lines.Add("- Missing expected paths: $($missingChecks.Count)")
$lines.Add("- Git status exit: $($gitStatus.ExitCode)")
$lines.Add("- Git worktree exit: $($worktrees.ExitCode)")
$lines.Add("- Worktree Drive references: $($driveRefs.Count)")
$lines.Add("")
$lines.Add("## Presence")
$lines.Add("")
$lines.Add("| Path | Kind | Exists |")
$lines.Add("|---|---:|---:|")
foreach ($path in $checks) {
    $lines.Add("| $(Format-TransitionCode $path) | $(Get-TransitionPathKind $path) | $(Test-Path -LiteralPath $path) |")
}

$lines.Add("")
Add-TransitionCommandReportSection -Lines $lines -Title "Git status" -Result $gitStatus
Add-TransitionCommandReportSection -Lines $lines -Title "Git worktrees" -Result $worktrees
if ($driveRefs.Count -gt 0) {
    $lines.Add("## Drive references")
    $lines.Add("")
    foreach ($ref in $driveRefs) {
        $lines.Add("- $(Format-TransitionCode $ref)")
    }
}

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
