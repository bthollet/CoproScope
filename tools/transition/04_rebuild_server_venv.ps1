. "$PSScriptRoot\_transition_common.ps1"

$repo = Get-TransitionRepoRoot
$server = Join-Path $repo "server"
$venv = Join-Path $server ".venv"
$python = Resolve-TransitionPython
$report = New-TransitionReportPath -Prefix "04_rebuild_server_venv"
$venvExisted = Test-Path -LiteralPath $venv

if (-not $venvExisted) {
    $create = Invoke-TransitionCommand -FilePath $python -Arguments @("-m", "venv", $venv) -WorkingDirectory $server
}
else {
    $create = New-TransitionCommandResult -FilePath $python -Arguments @("-m", "venv", $venv) -WorkingDirectory $server -ExitCode 0 -Output "server venv already exists; creation skipped."
}

$venvPython = Join-Path $venv "Scripts\python.exe"
if ($create.ExitCode -eq 0 -and (Test-Path -LiteralPath $venvPython)) {
    $pip = Invoke-TransitionCommand -FilePath $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip") -WorkingDirectory $server
    $install = Invoke-TransitionCommand -FilePath $venvPython -Arguments @("-m", "pip", "install", "-e", ".[ui,accounting,dashboards,docai]") -WorkingDirectory $server
    $tools = Invoke-TransitionCommand -FilePath $venvPython -Arguments @("-m", "coproscope.cli", "tools", "status") -WorkingDirectory $server
}
else {
    $reason = "Skipped because server venv Python is missing: $venvPython"
    if ($create.ExitCode -ne 0) {
        $reason = "Skipped because venv creation failed."
    }
    $pip = New-TransitionCommandResult -FilePath $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip") -WorkingDirectory $server -ExitCode 1 -Output $reason
    $install = New-TransitionCommandResult -FilePath $venvPython -Arguments @("-m", "pip", "install", "-e", ".[ui,accounting,dashboards,docai]") -WorkingDirectory $server -ExitCode 1 -Output $reason
    $tools = New-TransitionCommandResult -FilePath $venvPython -Arguments @("-m", "coproscope.cli", "tools", "status") -WorkingDirectory $server -ExitCode 1 -Output $reason
}

$exitCode = if ($create.ExitCode -ne 0 -or $pip.ExitCode -ne 0 -or $install.ExitCode -ne 0 -or $tools.ExitCode -ne 0) { 1 } else { 0 }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Rebuild server venv")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- Python used: $(Format-TransitionCode $python)")
$lines.Add("- Venv: $(Format-TransitionCode $venv)")
$lines.Add("- Venv existed before run: $venvExisted")
$lines.Add("- Venv python exists after run: $(Test-Path -LiteralPath $venvPython)")
$lines.Add("- Overall exit: $exitCode")
$lines.Add("")
Add-TransitionCommandReportSection -Lines $lines -Title "Create venv" -Result $create
Add-TransitionCommandReportSection -Lines $lines -Title "pip upgrade" -Result $pip
Add-TransitionCommandReportSection -Lines $lines -Title "install" -Result $install
Add-TransitionCommandReportSection -Lines $lines -Title "tools status" -Result $tools

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
if ($exitCode -ne 0) { exit $exitCode }
