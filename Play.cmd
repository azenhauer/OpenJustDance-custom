@echo off
setlocal
cd /d "%~dp0"
set "YOLO_AUTOINSTALL=false"
if not exist ".venv\Scripts\python.exe" (
  echo Run uv sync --locked in this folder first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m apps.desktop.main
if errorlevel 1 pause
