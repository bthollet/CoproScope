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

# **Le venv est partage entre arbres de travail, et son .pth code en dur le
# server\src de l'arbre PRINCIPAL.** Sans la ligne ci-dessous, un agent qui
# lance ce check depuis un worktree obtient une suite VERTE qui a mesure le code
# d'un autre arbre. Le defaut ne casse aucun test: il en fait passer. Constate
# le 2026-09-05 par un agent de la campagne de finition - "mes premiers passages
# verts etaient donc faux".
#
# Forcer PYTHONPATH sur l'arbre courant rend le venv partage inoffensif: les
# sources locales gagnent, quel que soit l'interpreteur trouve.
$sourceRoot = Join-Path $repoRoot "server\src"
$env:PYTHONPATH = $sourceRoot

Write-Host "Repository: $repoRoot"
Write-Host "Python:     $python"
Write-Host "Sources:    $sourceRoot"

if ($Orchestration) {
    Invoke-Step "Registre de presence" {
        Invoke-Native -FilePath $python -Arguments @(
            ".\tools\presence_lint.py"
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

Invoke-Step "File de travail" {
    # Affiche l'etat de la file derivee du gouvernail: engages, decisions en
    # attente, journal, dormants. **Ne fait PAS echouer le check.** Un plafond
    # depasse est une information de pilotage, pas une regression de code, et
    # une garde qui bloquerait le travail parce que la file est pleine
    # empecherait precisement de la vider.
    & $python ".\tools\file_travail.py"
    if ($LASTEXITCODE -eq 2) {
        Write-Host "file_travail: le gouvernail n'a PAS PU etre lu." -ForegroundColor Yellow
    }
    $global:LASTEXITCODE = 0
}

Invoke-Step "Fast agent tests" {
    Push-Location .\server
    try {
        Invoke-Native -FilePath $python -Arguments @(
            "-m",
            "unittest",
            "tests.test_arbre_teste",
            "tests.test_code_line_limit",
            "tests.test_file_travail",
            "tests.test_vault",
            # Ajoutee au chemin rapide le 2026-09-09. Cette garde refuse un
            # appel a `subprocess` hors liste, et un garde neuf qui demande a
            # Git ce qu'il suit la viole des sa creation. Le defaut est
            # INVISIBLE a tout passage cible: seule la suite complete le
            # revele, dix minutes plus tard. Il s'est produit deux fois dans la
            # meme heure le 2026-09-09, et cinq fois le 2026-09-07. Dix-huit
            # secondes ici valent dix minutes de suite rouge.
            "tests.test_security_code_injection_guards",
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
    Invoke-Step "Registre de presence (JSON)" {
        Invoke-Native -FilePath $python -Arguments @(
            ".\tools\presence_lint.py",
            "--json"
        )
    }
}

if ($Full) {
    Invoke-Step "Full unittest suite" {
        # **Une seule facon de jouer la suite** (RM-2026-0173). L'invocation
        # precedente etait `python -m unittest discover -s tests -v` depuis
        # server: elle place server/tests en tete de sys.path, change le nom
        # d'import des modules, joue environ 330 tests de MOINS, et sort sur 1
        # pendant qu'unittest imprime OK. Le lanceur canonique se place
        # lui-meme au bon endroit, nomme les tests collectes et jamais
        # demarres, et lit son verdict d'unittest - jamais d'un code de sortie
        # compose.
        Invoke-Native -FilePath $python -Arguments @(".\tools\lancer_la_suite.py", "-v")
    }
}

Write-Host ""
Write-Host "Agent check complete." -ForegroundColor Green
