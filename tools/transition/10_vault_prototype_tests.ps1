. "$PSScriptRoot\_transition_common.ps1"

$repo = Get-TransitionRepoRoot
$python = Resolve-TransitionPython
$report = New-TransitionReportPath -Prefix "10_vault_tests"
$oldPath = $env:PYTHONPATH
$oldDontWriteBytecode = $env:PYTHONDONTWRITEBYTECODE
$testPath = Join-Path $repo "server\tests\test_vault.py"
$testPythonPath = Join-Path $repo "server\src"
$env:PYTHONPATH = $testPythonPath
$env:PYTHONDONTWRITEBYTECODE = "1"
try {
    $tests = Invoke-TransitionCommand -FilePath $python -Arguments @("-m", "unittest", "discover", "-s", "server\tests", "-p", "test_vault.py", "-v") -WorkingDirectory $repo
}
finally {
    if ($null -eq $oldPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $oldPath
    }
    if ($null -eq $oldDontWriteBytecode) {
        Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONDONTWRITEBYTECODE = $oldDontWriteBytecode
    }
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Vault prototype tests")
$lines.Add("")
$lines.Add("- Date: $(Get-TransitionTimestamp)")
$lines.Add("- Python: $(Format-TransitionCode $python)")
$lines.Add("- Test file: $(Format-TransitionCode $testPath)")
$lines.Add("- Test file exists: $(Test-Path -LiteralPath $testPath)")
$lines.Add("- PYTHONPATH during run: $(Format-TransitionCode $testPythonPath)")
$lines.Add("- PYTHONDONTWRITEBYTECODE during run: 1")
$lines.Add("- Exit code: $($tests.ExitCode)")
$lines.Add("")
Add-TransitionCommandReportSection -Lines $lines -Title "unittest" -Result $tests

Write-TransitionText -Path $report -Content ($lines -join "`n")
Write-Host $report
if ($tests.ExitCode -ne 0) { exit $tests.ExitCode }
