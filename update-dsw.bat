@echo off
cd /d "%~dp0"

git pull --ff-only
if errorlevel 1 (
  echo Update failed. Make sure Git is installed and this folder was cloned from GitHub.
  pause
  exit /b 1
)

echo David Strategy Works is up to date.
pause
