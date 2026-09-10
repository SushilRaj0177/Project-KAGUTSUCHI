#!/usr/bin/env bash
# Runs the real backend (with real Docker sandbox access, since this
# devcontainer has docker-in-docker) inside a GitHub Codespace, and
# publishes it with a Cloudflare Tunnel instead of Codespaces' own port
# forwarding -- GitHub's forwarded-port proxy returns a genuine 404 to
# anonymous/logged-out visitors even on "Public" visibility, so it can't
# serve our real users. cloudflared has no such restriction and needs no
# account, domain, or credit card.
#
# Usage (inside a Codespace terminal): bash scripts/start_live_demo.sh
#
# The printed https://<random>.trycloudflare.com URL is your real,
# fully-sandboxed backend for as long as this script keeps running.
# Paste it into Vercel's KAGUTSUCHI_API_URL env var to switch the live
# site over to it (e.g. right before a demo/judging session), then
# switch KAGUTSUCHI_API_URL back to the Render URL when you stop this
# script -- the tunnel URL dies with it.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "Installing cloudflared (one-time, no account needed)..."
  curl -sSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
  chmod +x /usr/local/bin/cloudflared
fi

echo "Starting backend on :8000 (real Docker sandbox, not the subprocess fallback)..."
KAGUTSUCHI_ALLOWED_ORIGINS="*" uvicorn server.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT

sleep 3
echo "Opening a Cloudflare quick tunnel to it..."
cloudflared tunnel --url http://localhost:8000
