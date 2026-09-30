# Deploying the backend

`wsqfai/server/` (M7c-backend) is a real, already-proven FastAPI app - see
`ROADMAP.md` and `README.md` for what it does. It runs today via
`uvicorn wsqfai.server.main:app` wherever someone starts it by hand. It is
not deployed anywhere public yet, which is the one real gap between
`webapp/app/analyze` (M7c-frontend, merged) working locally and working
for an actual visitor to the live website: the deployed webapp has no
backend URL to call.

## The `Dockerfile`

The repo root `Dockerfile` packages the backend so any host that accepts
"deploy from a Dockerfile" (Railway, Render, Fly.io, a plain VM with
Docker installed) can run it with no further setup:

```bash
docker build -t wsqfai-backend .
docker run -p 8000:8000 -e WSQFAI_ALLOWED_ORIGINS=https://your-webapp.vercel.app wsqfai-backend
```

**What's actually verified, honestly:** this development environment has
the `docker` CLI installed but no reachable Docker daemon (`dockerd`) -
the exact same limitation `ROADMAP.md` already documents for
`engine-archive/kagutsuchi/system/sandbox/docker_runner.py`, so this
isn't a new gap. The `Dockerfile` itself has **not** been through a real
`docker build`/`docker run` in this environment. What has been verified
for real: a completely clean `pip install ".[server]"` (matching the
Dockerfile's own install step exactly, from just `pyproject.toml` +
`wsqfai/`) followed by `uvicorn wsqfai.server.main:app`, then a real
`POST /api/analyze-repo/start` + poll round-trip against a live public
repo (`octocat/Hello-World`) - the entire backend, minus the container
layer itself. Building the image is straightforward Python-in-Docker
with no unusual steps, but "should work" and "verified working" are
different claims, and this project doesn't blur them - treat the
container build itself as the one remaining thing to confirm on whatever
host actually runs it.

## What a host needs to set

- `WSQFAI_ALLOWED_ORIGINS` - comma-separated list of allowed CORS
  origins (defaults to `*`, which is fine for testing but should be
  narrowed to the deployed webapp's real origin, e.g.
  `https://your-project.vercel.app`, once this is actually public - see
  `wsqfai/server/main.py`).
- `PORT` - most hosts (Railway, Render) inject this automatically; the
  `Dockerfile`'s `CMD` reads it, defaulting to `8000` if unset.

## Wiring the webapp to it

Once deployed, set `NEXT_PUBLIC_API_BASE_URL` in the webapp's hosting
environment (Vercel project settings -> Environment Variables) to the
backend's real URL - see `webapp/.env.example`. `NEXT_PUBLIC_*` vars are
baked in at build time, so redeploy the webapp after setting it, not just
restart it.

## What this doesn't decide

Which host to actually use, and the credentials/account to provision one,
are real decisions this repository doesn't make on its own - see
`ROADMAP.md`'s M7c-frontend entry.
