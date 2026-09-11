# Deploying the backend somewhere that actually gives real isolation

Render's standard web service plan does not grant the kernel privileges
Docker (or any hand-rolled sandbox) needs — confirmed directly by hitting
`/api/debug/isolation-probe` on the live Render deployment: every required
check (network/mount/pid namespaces, chroot, cgroup delegation) came back
denied. That's a property of Render's container runtime itself, not
something fixable in this codebase — `system/sandbox/docker_runner.py`
already runs attacks in a real, network-disabled Docker container whenever
a Docker daemon is reachable, and only falls back to the weaker subprocess
sandbox when one isn't.

The fix is infrastructure, not code: run the backend somewhere you own
the whole kernel instead of sharing a restricted slice of someone else's.

**No money for a VPS?** See `deploy/windows-local-setup.md` instead — your
own laptop's Docker Desktop (via WSL2, a real Linux VM) gives the exact
same real isolation, for free, exposed to the internet with a free ngrok
static domain. Everything below is for when you'd rather it run on a
paid VPS instead of your own machine.

## 1. Get a VM

Any of these work — pick based on budget. All support Ubuntu 22.04/24.04
and give you full root, which is the only real requirement:

| Provider | Cheapest that'll work | Notes |
|---|---|---|
| Hetzner Cloud | ~€4.5/mo (CX22) | Cheapest reliable option |
| DigitalOcean | $6/mo (Basic droplet) | Most-documented, easiest to Google |
| Oracle Cloud Free Tier | Free forever (Ampere A1) | Genuinely free, but signup/capacity can be finicky |
| AWS EC2 | Free for 12mo (t2/t3.micro) | More setup ceremony than the others |

Whichever you pick: create an Ubuntu 22.04 or 24.04 instance, note its
public IP, and make sure you can `ssh root@<ip>`.

## 2. Run the setup script

SSH into the box, then:

```bash
curl -fsSL https://raw.githubusercontent.com/SushilRaj0177/Project-KAGUTSUCHI/claude/hackathon-plan-coordination-wipbuc/deploy/vps_setup.sh | bash
```

This installs Docker, Python 3.11, clones the repo, installs dependencies,
pre-builds the sandbox image, and installs (but does not yet start) a
systemd service. It's idempotent — re-running it later is how you deploy
new commits too.

## 3. Fill in secrets and start it

```bash
nano /etc/kagutsuchi.env      # set GROQ_API_KEY at minimum
systemctl start kagutsuchi-backend
curl http://localhost:8000/api/debug/isolation-probe
```

That last command is the actual proof: you want `"all_ok":true` this
time. If any check still fails, it means something about that specific
VM/provider is still restricting namespaces — worth pasting the output
back so we can see exactly what's blocked.

## 4. Put a real domain + TLS in front of it

Vercel (and browsers) will refuse to call an `http://` API from an
`https://` site. Easiest path — [Caddy](https://caddyserver.com) gets you
automatic TLS with one file:

```bash
apt-get install -y caddy
cat > /etc/caddy/Caddyfile <<'EOF'
your-backend-domain.com {
    reverse_proxy 127.0.0.1:8000
}
EOF
systemctl reload caddy
```

(Point `your-backend-domain.com`'s DNS A record at the VM's IP first.)

## 5. Point the webapp at it

In Vercel's project settings, set:

```
KAGUTSUCHI_API_URL=https://your-backend-domain.com
```

Redeploy the webapp (or it'll pick this up on its next build), then run a
real scan on the live site and confirm a verified fix's evidence looks
like it came from an actual container run, not the subprocess fallback.

## Keeping it updated

Re-run step 2's script (or just `git pull && systemctl restart
kagutsuchi-backend` inside `/opt/kagutsuchi` as the `kagutsuchi` user) any
time you want the VM running the latest commit.
