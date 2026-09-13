@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\server\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0presence_lint.py" %*
exit /b %ERRORLEVEL%
