. "$PSScriptRoot\_transition_common.ps1"

$repo = Get-TransitionRepoRoot
$pyproject = Join-Path $repo "server\pyproject.toml"
$report = Join-Path (Get-TransitionReportDir) "03_pyproject_dependency_patch.diff"
$content = Get-Content -LiteralPath $pyproject -Raw
$needed = @("PyYAML>=6.0", "python-docx>=1.1", "cryptography>=42.0")
$missing = @($needed | Where-Object { $content -notmatch [regex]::Escape($_) })

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Pyproject dependency plan")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- Pyproject: $(Format-TransitionCode $pyproject)")
$lines.Add("- Missing direct dependencies: $($missing.Count)")
$lines.Add("")
$lines.Add("## Dependency status")
$lines.Add("")
$lines.Add("| Requirement | Present |")
$lines.Add("|---|---:|")
foreach ($requirement in $needed) {
    $present = $content -match [regex]::Escape($requirement)
    $lines.Add("| $(Format-TransitionCode $requirement) | $present |")
}
$lines.Add("")

if ($missing.Count -eq 0) {
    $lines.Add("## Patch")
    $lines.Add("")
    $lines.Add("No dependency patch needed. Required direct dependencies are already present.")
}
else {
    $lines.Add("## Missing")
    $lines.Add("")
    foreach ($requirement in $missing) {
        $lines.Add("- $(Format-TransitionCode $requirement)")
    }
    $lines.Add("")
    $lines.Add("## Suggested patch")
    $lines.Add("")
    $lines.Add("Suggested location: $(Format-TransitionCode '[project].dependencies')")
    $lines.Add("")
    $lines.Add('```toml')
    foreach ($requirement in $missing) {
        $lines.Add('  "' + $requirement + '",')
    }
    $lines.Add('```')
}

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
