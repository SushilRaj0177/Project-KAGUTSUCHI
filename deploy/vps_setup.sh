#!/usr/bin/env bash
# Sets up the KAGUTSUCHI backend on a real VM (a plain Ubuntu box you have
# root on - a DigitalOcean/Hetzner/Linode/EC2 instance, anything that
# isn't a shared PaaS container).
#
# WHY THIS EXISTS: server/main.py's sandbox (system/sandbox/docker_runner.py)
# already runs attacks in a real, network-disabled Docker container when a
# Docker daemon is reachable - that code was never the problem. Render's
# standard web service plan doesn't grant the kernel privileges Docker (or
# any hand-rolled namespace-based sandbox) needs to run at all - confirmed
# directly against Render via GET /api/debug/isolation-probe, which failed
# every required check (network/mount/pid namespaces, chroot, cgroup
# delegation). That's a property of Render's container runtime, not
# something any application code can work around. A real VM gives you the
# whole kernel, so the exact same code gets the exact same real isolation
# it was already designed to use.
#
# Usage (as root, on a fresh Ubuntu 22.04/24.04 VM):
#   curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/<branch>/deploy/vps_setup.sh | bash
# or, having already cloned the repo:
#   sudo bash deploy/vps_setup.sh
#
# Re-running is safe: every step below is idempotent (checks before it
# acts), so this also doubles as the update/redeploy script - `git pull`
# happens first, then everything downstream picks up the new code.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/SushilRaj0177/Project-KAGUTSUCHI.git}"
BRANCH="${BRANCH:-claude/hackathon-plan-coordination-wipbuc}"
APP_DIR="${APP_DIR:-/opt/kagutsuchi}"
SERVICE_USER="${SERVICE_USER:-kagutsuchi}"
PORT="${PORT:-8000}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this as root (sudo bash deploy/vps_setup.sh)." >&2
  exit 1
fi

echo "==> Installing system packages (Docker, Python, git)..."
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git >/dev/null
# python3.11 is in Ubuntu 22.04's universe repo but doesn't exist at all
# on 24.04 (which ships 3.12, already >=3.11 - the actual requirement,
# per pyproject.toml) - so this is best-effort, not a hard dependency.
apt-get install -y -qq python3.11 python3.11-venv >/dev/null 2>&1 || true

PYTHON_BIN=""
for candidate in python3.11 python3.12 python3.13 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done
if [ -z "$PYTHON_BIN" ]; then
  echo "No Python >=3.11 interpreter found (need requires-python from pyproject.toml)." >&2
  exit 1
fi
apt-get install -y -qq "${PYTHON_BIN}-venv" >/dev/null 2>&1 || true
echo "Using $PYTHON_BIN ($("$PYTHON_BIN" --version))"

if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin >/dev/null
fi
systemctl enable --now docker

echo "==> Creating service user..."
id -u "$SERVICE_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
usermod -aG docker "$SERVICE_USER"

echo "==> Fetching the app..."
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR"

echo "==> Installing Python dependencies..."
sudo -u "$SERVICE_USER" "$PYTHON_BIN" -m venv "$APP_DIR/.venv"
sudo -u "$SERVICE_USER" "$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
sudo -u "$SERVICE_USER" "$APP_DIR/.venv/bin/pip" install --quiet \
  -r "$APP_DIR/requirements.txt" \
  -r "$APP_DIR/server/requirements.txt" \
  -r "$APP_DIR/verification/requirements.txt"

echo "==> Pre-building the sandbox Docker image (system/sandbox/Dockerfile)..."
sudo -u "$SERVICE_USER" docker build -t kagutsuchi-sandbox:latest "$APP_DIR/system/sandbox"

if [ ! -f "/etc/kagutsuchi.env" ]; then
  echo "==> Writing /etc/kagutsuchi.env (fill in real values before starting the service!)"
  cat > /etc/kagutsuchi.env <<EOF
PYTHONPATH=$APP_DIR
KAGUTSUCHI_ALLOWED_ORIGINS=*
GROQ_API_KEY=
EOF
  chmod 600 /etc/kagutsuchi.env
fi

echo "==> Installing systemd service..."
sed -e "s#{{APP_DIR}}#$APP_DIR#g" -e "s#{{PORT}}#$PORT#g" -e "s#{{SERVICE_USER}}#$SERVICE_USER#g" \
  "$APP_DIR/deploy/kagutsuchi-backend.service" > /etc/systemd/system/kagutsuchi-backend.service
systemctl daemon-reload
systemctl enable kagutsuchi-backend

echo
echo "==> Done. Before starting:"
echo "    1. Edit /etc/kagutsuchi.env and set GROQ_API_KEY (and KAGUTSUCHI_ALLOWED_ORIGINS"
echo "       to your real webapp origin, not '*', once you're ready to lock it down)."
echo "    2. sudo systemctl start kagutsuchi-backend"
echo "    3. curl http://localhost:$PORT/api/debug/isolation-probe  (expect \"all_ok\":true)"
echo "    4. Point a reverse proxy (Caddy/nginx) with a real TLS cert at 127.0.0.1:$PORT,"
echo "       then set KAGUTSUCHI_API_URL on Vercel to that https:// URL."
