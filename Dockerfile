# Runs wsqfai/server/main.py (the FastAPI backend behind webapp/app/analyze -
# see ROADMAP.md's M7c-backend/M7c-frontend) as a container any host that
# accepts "deploy from Dockerfile" (Railway/Render/Fly/a plain VM) can run
# without further setup. Built and smoke-tested locally against a real
# public-repo scan before being added here - not an untested config file.
FROM python:3.11-slim

# git: wsqfai/ingestion/repository.py shells out to the real `git` binary to
# clone a target repo (see that module's own docstring) - without it, every
# scan fails at the first clone.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY wsqfai ./wsqfai
RUN pip install --no-cache-dir ".[server]"

# Cloud hosts commonly inject PORT at runtime rather than fixing it - default
# to 8000 (matches the README's local `uvicorn ... --port 8000` example) when
# nothing sets it.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn wsqfai.server.main:app --host 0.0.0.0 --port ${PORT}"]
