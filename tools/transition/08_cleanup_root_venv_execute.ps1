. "$PSScriptRoot\_transition_common.ps1"

$workspace = Get-TransitionWorkspaceRoot
$repo = Get-TransitionRepoRoot
$report = New-TransitionReportPath -Prefix "08_cleanup_root_venv_execute"
$dryRun = Get-ChildItem -LiteralPath (Get-TransitionReportDir) -Filter "07_cleanup_root_venv_dryrun*.md" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $dryRun) { throw "Run 07_cleanup_root_venv_dryrun.bat first." }
if ($dryRun.LastWriteTime -lt (Get-Date).AddHours(-24)) { throw "Dry-run report is older than 24 hours." }

$serverPython = Join-Path $repo "server\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $serverPython)) { throw "server venv is missing." }
$tools = Invoke-TransitionCommand -FilePath $serverPython -Arguments @("-m", "coproscope.cli", "tools", "status") -WorkingDirectory (Join-Path $repo "server")

$archiveRoot = Join-Path (Get-TransitionArchiveDir) ("root_venv_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
$rootVenv = Join-Path $workspace ".venv"
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Cleanup root venv execute")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- Dry-run used: $(Format-TransitionCode $dryRun.FullName)")
$lines.Add("- Archive root: $(Format-TransitionCode $archiveRoot)")
$lines.Add("- Tools status exit: $($tools.ExitCode)")
$lines.Add("")
Add-TransitionCommandReportSection -Lines $lines -Title "tools status" -Result $tools

if ($tools.ExitCode -ne 0) {
    $lines.Add("Execution stopped before archive because tools status failed.")
    Write-TransitionText -Path $report -Content ($lines -join "`n")
    Write-Host $report
    exit $tools.ExitCode
}

if (Test-Path -LiteralPath $rootVenv) {
    $resolved = (Resolve-Path -LiteralPath $rootVenv).Path
    if (-not (Test-TransitionPathInsideRoot -Path $resolved -Root $workspace)) {
        throw "Refusing to move path outside workspace: $resolved"
    }
    New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null
    Move-Item -LiteralPath $rootVenv -Destination (Join-Path $archiveRoot ".venv")
    $lines.Add("- Archived root venv.")
}
else {
    $lines.Add("- Root venv already absent.")
}

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
