# Running the backend on your own Windows laptop (free, real isolation)

This gets you the exact same real, network-disabled Docker sandbox
`system/sandbox/docker_runner.py` was always built for — Render's shared
container just refuses to grant the kernel privileges it needs (confirmed
directly via `/api/debug/isolation-probe`). Your own machine doesn't have
that restriction: Docker Desktop on Windows runs its containers inside
WSL2, which is a real, full Linux VM (not a restricted PaaS container), so
the same code gets genuine isolation.

The honest tradeoff: your laptop has to be on and connected to the
internet for the backend (and so "Attack & Verify") to work. That's the
real cost of $0 instead of a VPS — not a hidden weakness in the isolation
itself, which is fully real once this is running.

## 1. Install WSL2 + Ubuntu

In PowerShell **as Administrator**:

```powershell
wsl --install -d Ubuntu
```

This needs a restart on a fresh install. Afterwards, launch "Ubuntu" from
the Start menu once to finish setup (pick a username/password for the
Linux side — separate from your Windows login).

## 2. Install Docker Desktop

Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
(free for personal use, no card needed). During/after install:

- Settings → General → confirm "Use the WSL 2 based engine" is checked.
- Settings → Resources → WSL Integration → enable integration for your
  "Ubuntu" distro.

Restart Docker Desktop, then in the Ubuntu terminal confirm it's reachable:

```bash
docker info
```

## 3. Set up the app inside WSL2's Ubuntu

In the Ubuntu terminal:

```bash
sudo apt-get update -qq
sudo apt-get install -y python3.11 python3.11-venv git   # or python3.12/python3 if 3.11 isn't available - anything >=3.11 works

git clone --branch claude/hackathon-plan-coordination-wipbuc \
  https://github.com/SushilRaj0177/Project-KAGUTSUCHI.git ~/kagutsuchi
cd ~/kagutsuchi

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r server/requirements.txt -r verification/requirements.txt

docker build -t kagutsuchi-sandbox:latest system/sandbox
```

Create `~/kagutsuchi/.env` with your real values:

```
PYTHONPATH=.
KAGUTSUCHI_ALLOWED_ORIGINS=*
GROQ_API_KEY=your-real-key-here
```

## 4. Run the backend and check isolation for real

```bash
cd ~/kagutsuchi
source .venv/bin/activate
set -a && source .env && set +a
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

Leave that running, open a second Ubuntu terminal, and confirm:

```bash
curl http://localhost:8000/api/debug/isolation-probe
```

This time you want `"all_ok":true` — that's the actual proof it's using
real Docker isolation, not the subprocess fallback.

(To keep it running after you close the terminal, prefix the uvicorn
command with `nohup ... &`, or just get in the habit of leaving that
terminal window open while you want the site's attack feature live.)

## 5. Expose it to the internet with a free, stable URL (ngrok)

Cloudflare's anonymous "quick tunnel" also works with zero signup, but its
URL changes every time you restart it — annoying to keep updating in
Vercel. ngrok's free plan includes **one permanent static domain**, so do
this instead:

1. Sign up free at [ngrok.com](https://ngrok.com) (email only, no card).
2. In the ngrok dashboard, claim your free static domain (Cloud Edge →
   Domains) — you'll get something like `your-name-123.ngrok-free.app`.
3. Install the agent inside WSL2's Ubuntu and authenticate:
   ```bash
   curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
   echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
   sudo apt-get update -qq && sudo apt-get install -y ngrok
   ngrok config add-authtoken <your-authtoken-from-the-dashboard>
   ```
4. In a third terminal, with the backend still running from step 4:
   ```bash
   ngrok http 8000 --domain=your-name-123.ngrok-free.app
   ```

That domain is now a real `https://` URL pointing at your laptop.

## 6. Point the webapp at it

Vercel project settings → Environment Variables:

```
KAGUTSUCHI_API_URL=https://your-name-123.ngrok-free.app
```

Redeploy the webapp (or it picks it up on its next build), run a real
scan on the live site, and paste back the isolation-probe output from
step 4 so we can confirm together it's genuinely `all_ok: true` before
calling this done.

## Later, if money allows

Everything above also works verbatim on a $4-6/mo VPS (Hetzner/
DigitalOcean) if you ever want the backend running without your laptop
needing to stay on — see `deploy/vps_setup.sh` and `deploy/README.md` for
that path. Nothing about the sandbox code changes; only where it runs.
