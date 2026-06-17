#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp ".env.example" ".env"
  echo "Created .env from .env.example. Add API keys later if needed."
fi

PORT_VALUE="8765"
if [ -f ".env" ]; then
  PORT_VALUE="$(awk -F= '/^[[:space:]]*PORT[[:space:]]*=/{gsub(/[[:space:]'\''"]/, "", $2); print $2; exit}' .env)"
  if [ -z "$PORT_VALUE" ]; then
    PORT_VALUE="8765"
  fi
fi

URL="http://127.0.0.1:$PORT_VALUE/"
echo "Open $URL"

if command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 server.py
elif command -v python >/dev/null 2>&1; then
  exec python server.py
else
  echo "Python is not installed. Install Python 3.11+."
  exit 1
fi
