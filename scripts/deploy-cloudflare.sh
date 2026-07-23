#!/usr/bin/env bash
# Deploy the workbench to Cloudflare Pages.
#
# The deployed UI is the classic dashboard (src/dashboard.py -> one
# self-contained HTML file), so the deploy is just an asset upload — no build
# runs on Cloudflare's side. This script regenerates that file from the current
# pipeline output, refreshes the committed copies in dashboard/ and docs/, and
# uploads it to the `underwriting-copilot` Pages project.
# (The React app in web/ stays in the repo and CI but is not deployed.)
#
# Two gotchas this handles for you:
#   1. wrangler needs Node >= 20.19; it prefers an nvm-managed 20.19+/22 if the
#      system node is older.
#   2. `wrangler pages deploy` refuses to run without a TTY, so it is wrapped in
#      script(1) to present a pseudo-terminal and reuse your existing
#      `wrangler login` session (run that once if you have not).
set -euo pipefail

PROJECT="underwriting-copilot"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Prefer a new-enough Node (wrangler requires >= 20.19).
if command -v node >/dev/null 2>&1 && node -e 'process.exit(process.versions.node.split(".").map(Number)[0]>20 || (process.versions.node.split(".").map(Number)[0]===20 && process.versions.node.split(".").map(Number)[1]>=19) ? 0 : 1)'; then
  : # system node is fine
elif [ -s "$HOME/.nvm/nvm.sh" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.nvm/nvm.sh"
  nvm use 22 >/dev/null 2>&1 || nvm use --lts >/dev/null 2>&1 || true
fi

echo "node $(node -v)  ·  deploying $PROJECT"

# Regenerate the shipping artifact from the current pipeline output and keep
# the committed copies in sync with what actually deploys.
PY="$ROOT/.venv/bin/python"; [ -x "$PY" ] || PY=python3
"$PY" "$ROOT/src/dashboard.py"
cp "$ROOT/output/underwriting_copilot_mvp.html" "$ROOT/dashboard/underwriting_copilot_mvp.html"
cp "$ROOT/output/underwriting_copilot_mvp.html" "$ROOT/docs/index.html"

# Stage the upload: the artifact is one HTML file; robots.txt / llms.txt live
# outside it in web/deploy and are copied in only at publish time.
PUBLISH="$(mktemp -d)"
trap 'rm -rf "$PUBLISH"' EXIT
cp "$ROOT/output/underwriting_copilot_mvp.html" "$PUBLISH/index.html"
cp "$ROOT/web/deploy/robots.txt" "$ROOT/web/deploy/llms.txt" "$PUBLISH/"

# Upload. `wrangler pages deploy` refuses to run without a TTY, so it is wrapped
# in script(1) to present a pseudo-terminal. The BSD (macOS) and util-linux
# calling conventions differ, so branch on the platform.
WRANGLER="npx --yes wrangler@latest pages deploy '$PUBLISH' --project-name '$PROJECT' --branch main --commit-dirty=true"
if [ "$(uname)" = "Darwin" ]; then
  script -q /dev/null npx --yes wrangler@latest pages deploy "$PUBLISH" \
    --project-name "$PROJECT" --branch main --commit-dirty=true
else
  # util-linux: -e returns the command's exit code, -c passes the command
  script -qec "$WRANGLER" /dev/null
fi
