@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%stop_lernbrief_hub.ps1"

if errorlevel 1 (
  echo.
  echo Fehler beim Ausfuehren von stop_lernbrief_hub.ps1
  exit /b 1
)

exit /b 0
