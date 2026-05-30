param(
    [switch]$InstallBuildDeps,
    [string]$PythonExe = "",
    [string]$DistPath = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$DefaultPython = Join-Path $ServerRoot ".venv\Scripts\python.exe"

if (-not $PythonExe) {
    if (Test-Path $DefaultPython) {
        $PythonExe = $DefaultPython
    } else {
        $PythonExe = "python"
    }
}

if ($InstallBuildDeps) {
    & $PythonExe -m pip install --upgrade pip wheel pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Installation des dependances de build echouee."
    }
    & $PythonExe -m pip install -e "$($ServerRoot)[ui,drive,executable]"
    if ($LASTEXITCODE -ne 0) {
        throw "Installation des extras CoproScope echouee."
    }
}

& $PythonExe -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller est absent. Relancez avec -InstallBuildDeps ou installez l'extra executable."
}

Push-Location $ServerRoot
try {
    $PyInstallerArgs = @("--noconfirm", "--clean")
    if ($DistPath) {
        $ResolvedDistPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($DistPath)
        $WorkPathName = "build-" + (Split-Path -Leaf $ResolvedDistPath)
        $ResolvedWorkPath = Join-Path (Split-Path -Parent $ResolvedDistPath) $WorkPathName
        $PyInstallerArgs += @("--distpath", $ResolvedDistPath)
        $PyInstallerArgs += @("--workpath", $ResolvedWorkPath)
    }
    $PyInstallerArgs += (Join-Path $ScriptDir "CoproScope.spec")
    & $PythonExe -m PyInstaller @PyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "La construction PyInstaller a echoue."
    }
}
finally {
    Pop-Location
}

$OutputRoot = if ($DistPath) {
    $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($DistPath)
} else {
    Join-Path $ServerRoot "dist"
}
$ExePath = Join-Path $OutputRoot "CoproScope\CoproScope.exe"
if (-not (Test-Path $ExePath)) {
    throw "Executable attendu introuvable: $ExePath"
}

Write-Host "POC executable pret: $ExePath"
