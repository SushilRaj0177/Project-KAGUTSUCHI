"""
Zero-trust Docker sandbox.

This is the ONLY place candidate code and attack payloads actually
execute. No network, a memory cap, and the container is destroyed after
every run — nothing here is ever trusted, regardless of which side (LLM
or hand-written fixture) produced the code or the payload.
"""
from __future__ import annotations

import io
import tarfile
import time

import docker

from contracts import ExecutionEvidence, ExecutionPhase

_IMAGE = "python:3.11-slim"
_MAX_LOG_CHARS = 8000


def _tar_bytes(filename: str, content: str) -> bytes:
    data = content.encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=filename)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def run_in_sandbox(
    *,
    candidate_code: str,
    payload: str,
    hypothesis_id: str,
    run_id: str,
    phase: ExecutionPhase,
    timeout_s: int = 10,
) -> ExecutionEvidence:
    """Run `candidate_code` (a Python script that reads the attack payload
    from sys.argv[1]) inside an isolated, network-disabled container and
    return the recorded ExecutionEvidence.
    """
    client = docker.from_env()
    container = client.containers.create(
        image=_IMAGE,
        command=["python", "/workspace/candidate.py", payload],
        network_disabled=True,
        mem_limit="128m",
        working_dir="/workspace",
        detach=True,
    )
    try:
        container.put_archive("/workspace", _tar_bytes("candidate.py", candidate_code))

        start = time.monotonic()
        container.start()
        try:
            result = container.wait(timeout=timeout_s)
            exit_code = result.get("StatusCode", -1)
        except Exception:
            container.kill()
            exit_code = -1
        duration_ms = int((time.monotonic() - start) * 1000)

        stdout = container.logs(stdout=True, stderr=False).decode(errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode(errors="replace")
        try:
            fs_changes = container.diff() or []
        except Exception:
            fs_changes = []

        return ExecutionEvidence(
            hypothesis_id=hypothesis_id,
            run_id=run_id,
            phase=phase,
            container_id=container.id,
            exit_code=exit_code,
            stdout=stdout[:_MAX_LOG_CHARS],
            stderr=stderr[:_MAX_LOG_CHARS],
            filesystem_diff={"changes": fs_changes},
            network_egress_attempts=[],
            policy_violations=[],
            duration_ms=duration_ms,
        )
    finally:
        container.remove(force=True)
