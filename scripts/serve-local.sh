#!/usr/bin/env bash
# Serve the Underwriting Copilot locally so you can walk the interactive tutorial.
# Usage:  ./scripts/serve-local.sh [port]      (default port 8137)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8137}"
APP="$ROOT/output/underwriting_copilot_mvp.html"

# Regenerate the app if it's missing (needs the venv; falls back to system python).
if [ ! -f "$APP" ]; then
  PY="$ROOT/.venv/bin/python"; [ -x "$PY" ] || PY=python3
  echo "Building the app…"; "$PY" "$ROOT/src/dashboard.py"
fi

URL="http://localhost:$PORT/underwriting_copilot_mvp.html"
echo ""
echo "  Underwriting Copilot is live at:"
echo "      $URL"
echo ""
echo "  Click the 🎓 Tutorial button (top-right) to take the guided tour."
echo "  Press Ctrl+C to stop the server."
echo ""

# Open the browser automatically (macOS 'open', Linux 'xdg-open') — best effort.
( sleep 1; { command -v open >/dev/null && open "$URL"; } || { command -v xdg-open >/dev/null && xdg-open "$URL"; } || true ) &

cd "$ROOT/output"
exec python3 -m http.server "$PORT"
