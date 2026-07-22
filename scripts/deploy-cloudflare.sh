#!/usr/bin/env bash
# Deploy the workbench to Cloudflare Pages.
#
# The app is one self-contained static file, so the deploy is just an asset
# upload — no build step runs on Cloudflare's side. This script rebuilds the
# snapshot locally, then uploads web/dist to the `underwriting-copilot` Pages
# project.
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

# Rebuild the shipping artifact so what we upload matches source.
npm --prefix "$ROOT/web" run release

# Upload. script(1) gives wrangler the TTY it insists on for pages deploy.
script -q /dev/null npx --yes wrangler@latest pages deploy "$ROOT/web/dist" \
  --project-name "$PROJECT" --branch main --commit-dirty=true
