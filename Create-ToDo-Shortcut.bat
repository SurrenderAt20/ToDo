@echo off
setlocal
cd /d "%~dp0"
PowerShell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Create-ToDo-Shortcut.ps1"
endlocal
