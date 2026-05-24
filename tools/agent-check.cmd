@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0agent-check.ps1" %*
exit /b %ERRORLEVEL%
