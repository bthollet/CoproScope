@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-local-guardrails.ps1" %*
exit /b %ERRORLEVEL%
