@echo off
cd /d "%~dp0"

if not exist ".env" (
  if exist ".env.example" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example. Add API keys later if needed.
  )
)

start "" "http://127.0.0.1:8765/"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py
) else (
  python server.py
)

pause
