param(
    [string]$ExePath = "",
    [string]$InstanceRoot = "",
    [ValidateSet("http", "window")]
    [string]$Mode = "http",
    [string]$ProbePath = "/",
    [string[]]$ExpectText = @("CoproScope"),
    [string]$Token = "smoke-token",
    [int]$TimeoutSeconds = 35
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$RepoRoot = (Resolve-Path (Join-Path $ServerRoot "..")).Path

function Resolve-CoproScopeExe {
    param([string]$RequestedPath)
    if ($RequestedPath) {
        return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($RequestedPath)
    }

    $DistRoot = Join-Path $ServerRoot "dist"
    $StandardExe = Join-Path $DistRoot "CoproScope\CoproScope.exe"
    $Candidates = @()
    if (Test-Path $DistRoot) {
        $Candidates += Get-ChildItem -LiteralPath $DistRoot -Recurse -Filter "CoproScope.exe" -File -ErrorAction SilentlyContinue |
            ForEach-Object { $_.FullName }
    }
    if (Test-Path $StandardExe) {
        $Candidates += $StandardExe
    }
    $Resolved = $Candidates |
        Sort-Object { (Get-Item -LiteralPath $_).LastWriteTime } -Descending |
        Select-Object -First 1
    if (-not $Resolved) {
        throw "Aucun CoproScope.exe trouve. Construisez d'abord avec packaging\windows\build-executable.ps1."
    }
    return $Resolved
}

function New-FreeLoopbackPort {
    $Listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), 0)
    $Listener.Start()
    try {
        return $Listener.LocalEndpoint.Port
    }
    finally {
        $Listener.Stop()
    }
}

function Get-DescendantProcessIds {
    param([int]$ParentProcessId)
    $Children = @(Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $ParentProcessId })
    foreach ($Child in $Children) {
        Get-DescendantProcessIds -ParentProcessId $Child.ProcessId
        $Child.ProcessId
    }
}

function Stop-OwnedProcessTree {
    param([System.Diagnostics.Process]$RootProcess)
    if (-not $RootProcess) {
        return
    }
    $ProcessIds = @(Get-DescendantProcessIds -ParentProcessId $RootProcess.Id)
    [array]::Reverse($ProcessIds)
    foreach ($ProcessId in $ProcessIds) {
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    }
    if (-not $RootProcess.HasExited) {
        $RootProcess.Kill()
        $RootProcess.WaitForExit(5000) | Out-Null
    }
}

function Normalize-ExpectedText {
    param([string[]]$Values)
    $Normalized = @()
    foreach ($Value in $Values) {
        $Normalized += $Value -split "," |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    }
    return $Normalized
}

$ResolvedExePath = Resolve-CoproScopeExe $ExePath
if (-not (Test-Path $ResolvedExePath)) {
    throw "Executable introuvable: $ResolvedExePath"
}

if (-not $InstanceRoot) {
    $InstanceRoot = Join-Path $RepoRoot "examples\synthetic_copro"
}
$ResolvedInstanceRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($InstanceRoot)
if (-not (Test-Path (Join-Path $ResolvedInstanceRoot "instance.yml"))) {
    throw "Instance invalide pour le smoke: $ResolvedInstanceRoot"
}

$Port = New-FreeLoopbackPort
$LogPath = Join-Path $env:TEMP "coproscope-executable-smoke-$Port.log"
Remove-Item -LiteralPath $LogPath -ErrorAction SilentlyContinue
$ProbePath = "/" + $ProbePath.TrimStart("/")
$ProbeUri = "http://127.0.0.1:$Port$ProbePath"
$ProbeSeparator = if ($ProbeUri.Contains("?")) { "&" } else { "?" }
$ProbeUri = "$ProbeUri$ProbeSeparator" + "token=$Token"
$ExpectedTexts = Normalize-ExpectedText $ExpectText

$Arguments = @("--instance-root", "`"$ResolvedInstanceRoot`"", "--port", $Port, "--token", $Token)
if ($Mode -eq "http") {
    $Arguments += "--no-browser"
}

$Process = $null
try {
    $StartInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $StartInfo.FileName = $ResolvedExePath
    $StartInfo.Arguments = ($Arguments -join " ")
    $StartInfo.WorkingDirectory = Split-Path -Parent $ResolvedExePath
    $StartInfo.UseShellExecute = $false
    $StartInfo.Environment["COPROSCOPE_LAUNCHER_LOG"] = $LogPath
    $Process = [System.Diagnostics.Process]::Start($StartInfo)

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $HttpOk = $false
    $MissingText = @()
    while ((Get-Date) -lt $Deadline) {
        try {
            $Response = Invoke-WebRequest -UseBasicParsing -Uri $ProbeUri -TimeoutSec 2
            $ExpectedTextFound = $true
            $MissingText = @()
            foreach ($Expected in $ExpectedTexts) {
                if ($Response.Content -notmatch [regex]::Escape($Expected)) {
                    $ExpectedTextFound = $false
                    $MissingText += $Expected
                }
            }
            if ($Response.StatusCode -eq 200 -and $ExpectedTextFound) {
                $HttpOk = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
        if ($Process.HasExited) {
            break
        }
    }
    if (-not $HttpOk) {
        $MissingDetails = if ($MissingText.Count) { " Textes absents: $($MissingText -join ', ')." } else { "" }
        throw "Smoke executable KO: l'UI ne repond pas comme attendu sur $ProbePath port $Port.$MissingDetails"
    }

    if ($Mode -eq "window") {
        Start-Sleep -Seconds 2
        $LogText = if (Test-Path $LogPath) { Get-Content -Raw $LogPath } else { "" }
        if ($LogText -notmatch "opening desktop window") {
            throw "Smoke fenetre KO: pywebview n'a pas atteint l'ouverture de fenetre."
        }
        if ($Process.HasExited) {
            throw "Smoke fenetre KO: l'executable s'est ferme trop tot."
        }
    }

    $Hash = Get-FileHash -Algorithm SHA256 $ResolvedExePath
    [pscustomobject]@{
        Status = "OK"
        Mode = $Mode
        ProbePath = $ProbePath
        ExePath = $ResolvedExePath
        InstanceRoot = $ResolvedInstanceRoot
        Port = $Port
        SHA256 = $Hash.Hash
    } | Format-List
}
finally {
    Stop-OwnedProcessTree -RootProcess $Process
}
