[CmdletBinding()]
param(
    [switch]$SkipHooks
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return ($output -join [Environment]::NewLine).TrimEnd()
}

$repoRoot = Invoke-Git -Arguments @("rev-parse", "--show-toplevel")
Set-Location -LiteralPath $repoRoot

$settings = [ordered]@{
    "fetch.prune"         = "true"
    "remote.origin.prune" = "true"
    "pull.ff"             = "only"
    "push.default"        = "simple"
    "rerere.enabled"      = "true"
    "branch.sort"         = "-committerdate"
}

foreach ($entry in $settings.GetEnumerator()) {
    Invoke-Git -Arguments @("config", "--local", $entry.Key, $entry.Value) | Out-Null
}

if (-not $SkipHooks) {
    Invoke-Git -Arguments @("config", "--local", "core.hooksPath", ".githooks") | Out-Null
}

Write-Host "Local Git guardrails installed for $repoRoot"
Write-Host ""
Invoke-Git -Arguments @(
    "config",
    "--local",
    "--get-regexp",
    "^(fetch\.prune|remote\.origin\.prune|pull\.ff|push\.default|rerere\.enabled|branch\.sort|core\.hooksPath)$"
)
