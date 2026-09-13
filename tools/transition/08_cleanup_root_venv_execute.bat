@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%SCRIPT_DIR%08_cleanup_root_venv_execute.ps1" %*
exit /b %ERRORLEVEL%
