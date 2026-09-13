Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-TransitionTimestamp {
    return (Get-Date -Format o)
}

function Get-TransitionRepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Get-TransitionWorkspaceRoot {
    return (Resolve-Path (Join-Path (Get-TransitionRepoRoot) "..")).Path
}

function Get-TransitionReportDir {
    $dir = Join-Path (Get-TransitionWorkspaceRoot) "_transition_reports"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

function Get-TransitionArchiveDir {
    $dir = Join-Path (Get-TransitionWorkspaceRoot) "_archives"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

function New-TransitionReportPath {
    param(
        [Parameter(Mandatory = $true)][string]$Prefix,
        [string]$Extension = "md"
    )
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    return Join-Path (Get-TransitionReportDir) "$Prefix`_$stamp.$Extension"
}

function Write-TransitionText {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Format-TransitionCode {
    param([AllowNull()][object]$Value)
    $tick = [char]96
    return "$tick$Value$tick"
}

function Format-TransitionCommandArgument {
    param([AllowNull()][string]$Argument)
    if ([string]::IsNullOrEmpty($Argument)) {
        return '""'
    }
    if ($Argument -match '\s') {
        return '"' + ($Argument -replace '"', '\"') + '"'
    }
    return $Argument
}

function Format-TransitionCommandLine {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )
    $parts = New-Object System.Collections.Generic.List[string]
    $parts.Add((Format-TransitionCommandArgument $FilePath))
    foreach ($argument in $Arguments) {
        $parts.Add((Format-TransitionCommandArgument $argument))
    }
    return ($parts -join " ")
}

function Format-TransitionProcessArgument {
    param([AllowNull()][string]$Argument)
    if ([string]::IsNullOrEmpty($Argument)) {
        return '""'
    }
    if ($Argument -notmatch '[\s"]') {
        return $Argument
    }
    $builder = [System.Text.StringBuilder]::new()
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($char in $Argument.ToCharArray()) {
        if ($char -eq '\') {
            $backslashes += 1
        }
        elseif ($char -eq '"') {
            [void]$builder.Append(('\' * (($backslashes * 2) + 1)))
            [void]$builder.Append('"')
            $backslashes = 0
        }
        else {
            if ($backslashes -gt 0) {
                [void]$builder.Append(('\' * $backslashes))
                $backslashes = 0
            }
            [void]$builder.Append($char)
        }
    }
    if ($backslashes -gt 0) {
        [void]$builder.Append(('\' * ($backslashes * 2)))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Get-TransitionPathKind {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return "missing"
    }
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer) {
        return "directory"
    }
    return "file"
}

function Test-TransitionPathInsideRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )
    $resolvedPath = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path).Path)
    $resolvedRoot = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Root).Path).TrimEnd([char[]]@('\', '/'))
    return (
        $resolvedPath.Equals($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $resolvedPath.StartsWith($resolvedRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)
    )
}

function New-TransitionCommandResult {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = (Get-TransitionRepoRoot),
        [int]$ExitCode = 0,
        [string]$Output = ""
    )
    return [pscustomobject]@{
        FilePath = $FilePath
        Arguments = $Arguments
        WorkingDirectory = $WorkingDirectory
        CommandLine = (Format-TransitionCommandLine -FilePath $FilePath -Arguments $Arguments)
        ExitCode = $ExitCode
        Output = $Output.TrimEnd()
    }
}

function Invoke-TransitionCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = (Get-TransitionRepoRoot)
    )
    $old = Get-Location
    $oldEap = $ErrorActionPreference
    Set-Location $WorkingDirectory
    try {
        $commandPath = $FilePath
        if (Test-Path -LiteralPath $FilePath) {
            $commandPath = (Resolve-Path -LiteralPath $FilePath).Path
        }
        else {
            $command = Get-Command $FilePath -ErrorAction SilentlyContinue
            if (-not $command) {
                return New-TransitionCommandResult -FilePath $FilePath -Arguments $Arguments -WorkingDirectory $WorkingDirectory -ExitCode 127 -Output "Command not found: $FilePath"
            }
            if ($command.Source) {
                $commandPath = $command.Source
            }
            else {
                $commandPath = $command.Name
            }
        }
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $commandPath
        $psi.Arguments = (($Arguments | ForEach-Object { Format-TransitionProcessArgument $_ }) -join " ")
        $psi.WorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory).Path
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true

        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $psi
        [void]$process.Start()
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $stdout = $stdoutTask.Result.TrimEnd()
        $stderr = $stderrTask.Result.TrimEnd()
        $outputParts = @($stdout, $stderr) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        $output = ($outputParts -join "`n")
        $exitCode = [int]$process.ExitCode
        $process.Dispose()
        return New-TransitionCommandResult -FilePath $FilePath -Arguments $Arguments -WorkingDirectory $WorkingDirectory -ExitCode $exitCode -Output $output
    }
    catch {
        return New-TransitionCommandResult -FilePath $FilePath -Arguments $Arguments -WorkingDirectory $WorkingDirectory -ExitCode 1 -Output ($_ | Out-String)
    }
    finally {
        $ErrorActionPreference = $oldEap
        Set-Location $old
    }
}

function Add-TransitionCommandReportSection {
    param(
        [Parameter(Mandatory = $true)][object]$Lines,
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][object]$Result
    )
    $Lines.Add("## $Title")
    $Lines.Add("")
    $Lines.Add("- Working directory: $(Format-TransitionCode $Result.WorkingDirectory)")
    $Lines.Add("- Command: $(Format-TransitionCode $Result.CommandLine)")
    $Lines.Add("- Exit code: $($Result.ExitCode)")
    $Lines.Add("")
    $Lines.Add('```text')
    if ([string]::IsNullOrWhiteSpace($Result.Output)) {
        $Lines.Add("(no output)")
    }
    else {
        $Lines.Add($Result.Output)
    }
    $Lines.Add('```')
    $Lines.Add("")
}

function Resolve-TransitionPython {
    $repo = Get-TransitionRepoRoot
    $serverVenv = Join-Path $repo "server\.venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $serverVenv) {
        return $serverVenv
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return $py.Source
    }
    throw "No Python executable found."
}
