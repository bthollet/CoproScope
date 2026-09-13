@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%SCRIPT_DIR%03_update_dependencies_plan.ps1" %*
exit /b %ERRORLEVEL%
