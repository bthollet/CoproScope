[CmdletBinding()]
param(
    [switch]$Full,
    [switch]$Ui,
    [switch]$Security,
    [switch]$Orchestration
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Command
}

function Get-RepoRoot {
    $root = (& git rev-parse --show-toplevel 2>$null).Trim()
    if (-not $root) {
        throw "Run this script from inside the CoproScope product repository."
    }
    return $root
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

$repoRoot = Get-RepoRoot
Set-Location -LiteralPath $repoRoot

$python = Join-Path $repoRoot "server\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "No Python interpreter found. Expected server\.venv\Scripts\python.exe or python on PATH."
    }
    $python = $pythonCommand.Source
}

Write-Host "Repository: $repoRoot"
Write-Host "Python:     $python"

if ($Orchestration) {
    Invoke-Step "Orchestration supervisor preview" {
        Invoke-Native -FilePath $python -Arguments @(
            ".\tools\orchestration_supervisor.py",
            "--emit-recovery-prompt"
        )
    }

    Invoke-Step "Orchestration watchdog preview" {
        Invoke-Native -FilePath $python -Arguments @(
            ".\tools\orchestration_watchdog.py",
            "--emit-prompt"
        )
    }
}

Invoke-Step "Git status" {
    $statusLines = @(git status --short)
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed with exit code $LASTEXITCODE"
    }

    if ($statusLines.Count -eq 0) {
        Write-Host "Working tree clean."
        return
    }

    Write-Host "Working tree has $($statusLines.Count) status line(s). Showing first 80:"
    $statusLines | Select-Object -First 80
    if ($statusLines.Count -gt 80) {
        Write-Host "... truncated; run 'git status --short' for the full list."
    }
}

Invoke-Step "Code line limit" {
    Invoke-Native -FilePath $python -Arguments @(".\tools\check_code_line_limit.py")
}

Invoke-Step "Fast agent tests" {
    Push-Location .\server
    try {
        Invoke-Native -FilePath $python -Arguments @(
            "-m",
            "unittest",
            "tests.test_code_line_limit",
            "tests.test_vault",
            "-v"
        )
    }
    finally {
        Pop-Location
    }
}

if ($Ui) {
    Invoke-Step "UI smoke tests" {
        Push-Location .\server
        try {
            Invoke-Native -FilePath $python -Arguments @(
                "-m",
                "unittest",
                "tests.test_ui_smoke_routes_expanded",
                "tests.test_ui_security_routes",
                "-v"
            )
        }
        finally {
            Pop-Location
        }
    }
}

if ($Security) {
    Invoke-Step "Security checks" {
        Push-Location .\server
        try {
            Invoke-Native -FilePath $python -Arguments @(
                "-m",
                "bandit",
                "-r",
                "src",
                "-q",
                "--severity-level",
                "high"
            )
            Invoke-Native -FilePath $python -Arguments @(
                "-m",
                "pip_audit",
                ".",
                "--skip-editable",
                "--progress-spinner",
                "off"
            )
        }
        finally {
            Pop-Location
        }
    }
}

if ($Orchestration) {
    Invoke-Step "Orchestration supervisor" {
        Invoke-Native -FilePath $python -Arguments @(
            ".\tools\orchestration_supervisor.py",
            "--strict"
        )
    }

    Invoke-Step "Orchestration watchdog" {
        Invoke-Native -FilePath $python -Arguments @(
            ".\tools\orchestration_watchdog.py",
            "--strict"
        )
    }
}

if ($Full) {
    Invoke-Step "Full unittest suite" {
        Push-Location .\server
        try {
            Invoke-Native -FilePath $python -Arguments @(
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-v"
            )
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "Agent check complete." -ForegroundColor Green
