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
import warnings
from pathlib import Path

import docker

from contracts import ExecutionEvidence, ExecutionPhase
from system.sandbox.subprocess_runner import run_in_subprocess_sandbox

_IMAGE = "kagutsuchi-sandbox:latest"
_DOCKERFILE_DIR = Path(__file__).parent
_MAX_LOG_CHARS = 8000


class SandboxUnavailableError(RuntimeError):
    """Raised when the Docker daemon can't be reached. This is an
    infrastructure failure, not a security signal — callers should
    surface it distinctly from an INCONCLUSIVE verdict."""


def _client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as exc:  # docker.errors.DockerException, ConnectionError, ...
        raise SandboxUnavailableError(
            "Could not reach the Docker daemon. Is Docker running? "
            f"(underlying error: {exc})"
        ) from exc


def _ensure_image(client: docker.DockerClient) -> None:
    """Build the sandbox image (see Dockerfile in this directory) if it
    isn't already present. Built once per host, then reused — the build
    only re-runs when the image is missing, not on every attack."""
    try:
        client.images.get(_IMAGE)
    except docker.errors.ImageNotFound:
        client.images.build(path=str(_DOCKERFILE_DIR), tag=_IMAGE)


# Docker's container.diff() "Kind" codes: 0=modified, 1=added, 2=deleted.
_DIFF_KIND_TO_BUCKET = {0: "modified", 1: "created", 2: "deleted"}


def _bucket_filesystem_diff(raw_changes: list[dict]) -> dict[str, list[str]]:
    """Convert Docker's raw container.diff() list into the
    {"created": [...], "modified": [...], "deleted": [...]} shape that
    verification/regression's marker-file check expects (see
    COORDINATION.md's filesystem_diff convention)."""
    buckets: dict[str, list[str]] = {"created": [], "modified": [], "deleted": []}
    for change in raw_changes:
        bucket = _DIFF_KIND_TO_BUCKET.get(change.get("Kind"))
        if bucket is not None:
            buckets[bucket].append(change.get("Path", ""))
    return buckets


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

    Falls back to system.sandbox.subprocess_runner (reduced isolation,
    flagged via policy_violations) when no Docker daemon is reachable --
    e.g. on hosts like Render's free tier that don't support
    Docker-in-Docker. Only raises SandboxUnavailableError if that
    fallback itself can't run either.
    """
    try:
        client = _client()
    except SandboxUnavailableError:
        return run_in_subprocess_sandbox(
            candidate_code=candidate_code,
            payload=payload,
            hypothesis_id=hypothesis_id,
            run_id=run_id,
            phase=phase,
            timeout_s=timeout_s,
        )
    _ensure_image(client)
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
            try:
                container.kill()
            except Exception:
                pass  # already exited/removed — nothing to kill
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
            filesystem_diff=_bucket_filesystem_diff(fs_changes),
            network_egress_attempts=[],
            policy_violations=[],
            duration_ms=duration_ms,
        )
    finally:
        try:
            container.remove(force=True)
        except Exception as exc:
            # Best-effort cleanup: a transient daemon race (seen on
            # Windows/WSL2 - removing immediately after exit can race the
            # daemon's own teardown) shouldn't crash the run or mask
            # whatever result/exception was already in flight. Leaves at
            # most a stopped container behind for manual cleanup, never a
            # running one - it's already exited or been killed by this
            # point.
            warnings.warn(
                f"Failed to remove sandbox container {container.id}: {exc}",
                stacklevel=2,
            )
