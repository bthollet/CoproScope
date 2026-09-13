. "$PSScriptRoot\_transition_common.ps1"

$workspace = Get-TransitionWorkspaceRoot
$repo = Get-TransitionRepoRoot
$reportDir = Get-TransitionReportDir
$jsonPath = Join-Path $reportDir "02_venv_inventory.json"
$mdPath = Join-Path $reportDir "02_venv_inventory.md"
$gapPath = Join-Path $reportDir "02_dependency_gap.md"
$venv = Join-Path $workspace ".venv"
$sitePackages = Join-Path $venv "Lib\site-packages"
$pyvenvCfg = Join-Path $venv "pyvenv.cfg"

$distInfos = @()
if (Test-Path -LiteralPath $sitePackages) {
    $distInfos = Get-ChildItem -LiteralPath $sitePackages -Directory -Filter "*.dist-info" | Sort-Object Name | ForEach-Object { $_.Name }
}

$imports = Invoke-TransitionCommand -FilePath "rg" -Arguments @("-n", "import (yaml|docx|fitz|openpyxl|pypdf|duckdb|pandas|docling|rapidocr|fastapi|uvicorn)|from (yaml|docx|fitz|openpyxl|pypdf|duckdb|pandas|docling|rapidocr|fastapi|uvicorn)", "server\src", "server\tests") -WorkingDirectory $repo

$inventory = [pscustomobject]@{
    generated_at = (Get-TransitionTimestamp)
    workspace = $workspace
    repo = $repo
    venv_path = $venv
    venv_exists = (Test-Path -LiteralPath $venv)
    site_packages_exists = (Test-Path -LiteralPath $sitePackages)
    pyvenv_cfg_exists = (Test-Path -LiteralPath $pyvenvCfg)
    pyvenv_cfg = if (Test-Path -LiteralPath $pyvenvCfg) { Get-Content -LiteralPath $pyvenvCfg -Raw } else { "" }
    dist_info_count = $distInfos.Count
    dist_info = $distInfos
    import_scan_exit_code = $imports.ExitCode
    import_scan_command = $imports.CommandLine
    import_scan = $imports.Output
}

Write-TransitionText -Path $jsonPath -Content ($inventory | ConvertTo-Json -Depth 5)

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# Inventaire venv")
$md.Add("")
$md.Add("- Date: $(Get-TransitionTimestamp)")
$md.Add("- Venv: $(Format-TransitionCode $venv)")
$md.Add("- Exists: $($inventory.venv_exists)")
$md.Add("- site-packages exists: $($inventory.site_packages_exists)")
$md.Add("- pyvenv.cfg exists: $($inventory.pyvenv_cfg_exists)")
$md.Add("- dist-info count: $($inventory.dist_info_count)")
$md.Add("- import scan exit: $($imports.ExitCode)")
$md.Add("")
$md.Add("## pyvenv.cfg")
$md.Add("")
$md.Add('```text')
$md.Add($inventory.pyvenv_cfg.TrimEnd())
$md.Add('```')
$md.Add("")
$md.Add("## dist-info")
$md.Add("")
if ($distInfos.Count -eq 0) {
    $md.Add("(none)")
}
else {
    foreach ($name in $distInfos) { $md.Add("- $name") }
}
$md.Add("")
Add-TransitionCommandReportSection -Lines $md -Title "Imports detectes" -Result $imports
Write-TransitionText -Path $mdPath -Content ($md -join "`n")

$gap = @"
# Dependency gap

- Date: $(Get-TransitionTimestamp)
- Inventory report: $(Format-TransitionCode $mdPath)
- Import scan exit: $($imports.ExitCode)

Verifier avant suppression de l'ancien venv:

- `PyYAML`: necessaire pour les fichiers `instance.yml`.
- `python-docx`: utilise par DocOps, PrivacyOps et BiffageOps pour les fichiers DOCX.
- `cryptography`: necessaire au vault signe/chiffre.
- `PyMuPDF`, `openpyxl`, `pypdf`: deja dans les extras existants, a conserver.
- `docling`, `rapidocr`: restent dans l'extra `docai`.
- `torch`, `qwen-vl-utils`: restent dans l'extra `vl`, non installe par defaut.
"@
Write-TransitionText -Path $gapPath -Content $gap
Write-Host $mdPath
