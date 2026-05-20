param([switch]$ForceRewrite)
. "$PSScriptRoot\_transition_common.ps1"

$workspace = Get-TransitionWorkspaceRoot
$repo = Get-TransitionRepoRoot
$report = New-TransitionReportPath -Prefix "01_write_transition_docs"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$targets = @(
    @{ Path = Join-Path $workspace "PASSATION_COPROSCOPE_LOCAL.md"; Title = "Passation CoproScope locale" },
    @{ Path = Join-Path $repo "docs\transition_vault_collaboratif.md"; Title = "Transition vers un vault collaboratif signe" },
    @{ Path = Join-Path $repo "docs\migration_drive_vers_local.md"; Title = "Migration Drive vers local" },
    @{ Path = Join-Path $repo "docs\documentation_noyau_vs_instance.md"; Title = "Documentation noyau vs documentation d'instance" },
    @{ Path = Join-Path $repo "docs\vault_format.md"; Title = "Format vault CoproScope V1" },
    @{ Path = Join-Path $repo "docs\signatures_historique.md"; Title = "Signatures et historique" },
    @{ Path = Join-Path $repo "docs\objets_metier_evenements_v1.md"; Title = "Objets metier et evenements V1" },
    @{ Path = Join-Path $repo "docs\plugins_officiels.md"; Title = "Plugins officiels CoproScope" },
    @{ Path = Join-Path $repo "docs\batchs_transition_locale.md"; Title = "Batchs de transition locale" }
)

$created = New-Object System.Collections.Generic.List[string]
$unchanged = New-Object System.Collections.Generic.List[string]
$backedUp = New-Object System.Collections.Generic.List[string]
$results = New-Object System.Collections.Generic.List[object]

foreach ($target in $targets) {
    $path = [string]$target.Path
    $title = [string]$target.Title
    $fallback = "# $title`n`nDocument cree par le batch de transition. Completer depuis le plan de transition local.`n"
    if (Test-Path -LiteralPath $path) {
        if ($ForceRewrite) {
            $backup = "$path.bak-$stamp"
            Copy-Item -LiteralPath $path -Destination $backup
            Write-TransitionText -Path $path -Content $fallback
            $backedUp.Add($backup)
            $results.Add([pscustomobject]@{ Path = $path; Status = "rewritten"; Backup = $backup })
        }
        else {
            $unchanged.Add($path)
            $results.Add([pscustomobject]@{ Path = $path; Status = "unchanged"; Backup = "" })
        }
    }
    else {
        Write-TransitionText -Path $path -Content $fallback
        $created.Add($path)
        $results.Add([pscustomobject]@{ Path = $path; Status = "created"; Backup = "" })
    }
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Ecriture docs transition")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- ForceRewrite: $ForceRewrite")
$lines.Add("- Created: $($created.Count)")
$lines.Add("- Rewritten with backup: $($backedUp.Count)")
$lines.Add("- Unchanged: $($unchanged.Count)")
$lines.Add("")
$lines.Add("## Targets")
$lines.Add("")
$lines.Add("| Target | Status | Backup |")
$lines.Add("|---|---:|---|")
foreach ($result in $results) {
    $backup = if ([string]::IsNullOrWhiteSpace($result.Backup)) { "" } else { Format-TransitionCode $result.Backup }
    $lines.Add("| $(Format-TransitionCode $result.Path) | $($result.Status) | $backup |")
}
Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
