. "$PSScriptRoot\_transition_common.ps1"

$repo = Get-TransitionRepoRoot
$report = New-TransitionReportPath -Prefix "09_vault_spec_scaffold"
$specs = @(
    "docs\vault_format.md",
    "docs\signatures_historique.md",
    "docs\objets_metier_evenements_v1.md",
    "docs\plugins_officiels.md"
)
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Vault spec scaffold")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- Specs checked: $($specs.Count)")
$lines.Add("")
$lines.Add("| Spec | Action | Kind | Size bytes |")
$lines.Add("|---|---:|---:|---:|")

foreach ($relative in $specs) {
    $path = Join-Path $repo $relative
    if (-not (Test-Path -LiteralPath $path)) {
        Write-TransitionText -Path $path -Content "# $relative`n`nSpec a completer.`n"
        $action = "created"
    }
    else {
        $action = "exists"
    }
    $item = Get-Item -LiteralPath $path -Force
    $size = if ($item.PSIsContainer) { "" } else { $item.Length }
    $lines.Add("| $(Format-TransitionCode $relative) | $action | $(Get-TransitionPathKind $path) | $size |")
}

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
