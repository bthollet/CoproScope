[CmdletBinding()]
param(
    [switch]$Pull,
    [switch]$Push,
    [switch]$NoFetch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    $output = & git @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($output -join [Environment]::NewLine).TrimEnd()

    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "git $($Arguments -join ' ') failed with exit code ${exitCode}: $text"
    }

    [pscustomobject]@{
        ExitCode = $exitCode
        Text     = $text
    }
}

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host "==> $Text" -ForegroundColor Cyan
}

function Get-OptionalCommand {
    param([string]$Name)
    return Get-Command $Name -ErrorAction SilentlyContinue
}

$root = (Invoke-Git -Arguments @("rev-parse", "--show-toplevel")).Text
Set-Location -LiteralPath $root

Write-Section "Repository"
$branch = (Invoke-Git -Arguments @("branch", "--show-current")).Text
$origin = (Invoke-Git -Arguments @("remote", "get-url", "origin") -AllowFailure).Text
Write-Host "Root:   $root"
Write-Host "Branch: $branch"
Write-Host "Origin: $origin"

if (-not $NoFetch) {
    Write-Section "Fetch"
    Invoke-Git -Arguments @("fetch", "--prune", "--tags", "origin") | Out-Null
    Write-Host "origin refreshed with prune and tags."
}

Write-Section "Tracking"
$upstreamResult = Invoke-Git -Arguments @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") -AllowFailure
$upstream = ""
$ahead = 0
$behind = 0

if ($upstreamResult.ExitCode -eq 0 -and $upstreamResult.Text) {
    $upstream = $upstreamResult.Text
    $counts = (Invoke-Git -Arguments @("rev-list", "--left-right", "--count", "HEAD...@{u}")).Text -split "\s+"
    if ($counts.Count -ge 2) {
        $ahead = [int]$counts[0]
        $behind = [int]$counts[1]
    }
    Write-Host "Upstream: $upstream"
    Write-Host "Ahead:    $ahead"
    Write-Host "Behind:   $behind"
} else {
    Write-Warning "No upstream configured for branch '$branch'. First push should use: git push -u origin $branch"
}

Write-Section "Working tree"
$status = (Invoke-Git -Arguments @("status", "--short")).Text
$isDirty = -not [string]::IsNullOrWhiteSpace($status)
if ($isDirty) {
    $lines = $status -split [Environment]::NewLine
    Write-Warning "Working tree is not clean ($($lines.Count) status line(s))."
    $lines | Select-Object -First 40 | ForEach-Object { Write-Host $_ }
    if ($lines.Count -gt 40) {
        Write-Host "... truncated; run 'git status --short' for the full list."
    }
} else {
    Write-Host "Working tree clean."
}

Write-Section "GitHub CLI"
if (Get-OptionalCommand -Name "gh") {
    $ghStatus = & gh auth status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "gh auth status: OK"
    } else {
        Write-Warning "gh auth status failed:"
        $ghStatus | ForEach-Object { Write-Host $_ }
    }
} else {
    Write-Warning "gh command not found; Git operations still work, but PR/issue workflows are less visible."
}

if ($Pull) {
    Write-Section "Pull"
    if (-not $upstream) {
        throw "Cannot pull: no upstream is configured for '$branch'."
    }
    if ($isDirty) {
        throw "Cannot pull safely: working tree is not clean. Commit, stash, or discard intentionally first."
    }
    Invoke-Git -Arguments @("pull", "--ff-only") | Out-Null
    Write-Host "Fast-forward pull complete."
}

if ($Push) {
    Write-Section "Push"
    if (-not $upstream) {
        throw "Cannot push with this helper: no upstream is configured. Use 'git push -u origin $branch' once."
    }
    if ($behind -gt 0) {
        throw "Cannot push: '$branch' is behind '$upstream' by $behind commit(s). Pull fast-forward first."
    }
    if ($isDirty) {
        throw "Cannot push with this helper while the working tree is not clean. Commit or split the changes first."
    }
    Invoke-Git -Arguments @("push") | Out-Null
    Write-Host "Push complete."
}

if (-not $Pull -and -not $Push) {
    Write-Section "Next"
    if ($behind -gt 0) {
        Write-Host "Remote has new commits. If the working tree is clean, run: .\tools\git\sync.ps1 -Pull"
    } elseif ($ahead -gt 0) {
        Write-Host "Local branch has commits to publish. If the working tree is clean, run: .\tools\git\sync.ps1 -Push"
    } else {
        Write-Host "Branch and upstream are aligned. Sort the working tree before committing or pushing."
    }
}
