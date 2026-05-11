@echo off
setlocal
cd /d "%~dp0"
start "ToDo" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py"
endlocal
