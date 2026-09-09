# Sandbox image for running candidate code + attack payloads. Built on
# python:3.11-slim (Debian) with iputils-ping added, since the P0 netdiag
# fixture's fixed() path actually shells out to a real `ping` binary via
# subprocess.run(shell=False) — plain python:3.11-slim doesn't ship it.
FROM python:3.11-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*
