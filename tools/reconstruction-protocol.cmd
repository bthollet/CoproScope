@echo off
setlocal
set "REPO_ROOT=%~dp0.."
set "PYTHON=%REPO_ROOT%\server\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"
"%PYTHON%" "%REPO_ROOT%\tools\reconstruction_protocol.py" %*
