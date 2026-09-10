"""
Reduced-isolation fallback sandbox, used only when the Docker daemon is
unreachable (see docker_runner.SandboxUnavailableError) -- e.g. on
Render's free tier, which doesn't allow Docker-in-Docker. This is NOT a
substitute for real container isolation: there is no network namespace,
so a payload can still reach the network. It exists so the public
"Attack & Verify" feature keeps working (with an honest disclaimer)
instead of hard-failing with a 503 whenever the host has no Docker.

What it does provide, unlike verification/attacks/run_local.py's
in-process call:
  - a genuinely separate OS process (a server crash/hang in candidate
    code can't take the API process down with it)
  - CPU, memory, output-size, and process-count limits (rlimits)
  - a scrubbed environment (no GROQ_API_KEY, DATABASE_URL, etc. -
    candidate code cannot read secrets that were never handed to it)
  - a dedicated temp working directory, removed after the run
  - the run is serialized (one at a time) so concurrent requests can't
    race on the shared /tmp/kagutsuchi_pwned marker path fixtures use
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

try:
    import resource  # POSIX only - doesn't exist on Windows
except ImportError:
    resource = None  # type: ignore[assignment]

from contracts import ExecutionEvidence, ExecutionPhase

_MAX_LOG_CHARS = 8000
_MEM_LIMIT_BYTES = 128 * 1024 * 1024
_MARKER_PATH = Path("/tmp/kagutsuchi_pwned")

# Real isolation (Docker) can run attacks concurrently since each gets its
# own container; this fallback shares one host, so serialize runs to keep
# before/after evidence for one request from crossing with another's.
_lock = threading.Lock()


def _limit_resources() -> None:
    """rlimits are POSIX-only. On Windows (no `resource` module) this is a
    no-op -- there's no equivalent stdlib mechanism, so local Windows dev
    runs the fallback with fewer guardrails than Linux (Render, Codespaces,
    CI) gets. Fine for local development; the deployed backend is always
    Linux."""
    if resource is None:
        return
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (_MEM_LIMIT_BYTES, _MEM_LIMIT_BYTES))
    resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))


def _clear_marker() -> None:
    try:
        _MARKER_PATH.unlink()
    except FileNotFoundError:
        pass


def run_in_subprocess_sandbox(
    *,
    candidate_code: str,
    payload: str,
    hypothesis_id: str,
    run_id: str,
    phase: ExecutionPhase,
    timeout_s: int = 10,
) -> ExecutionEvidence:
    with _lock:
        _clear_marker()
        workdir = Path(tempfile.mkdtemp(prefix="kagutsuchi-"))
        script = workdir / "candidate.py"
        script.write_text(candidate_code)

        if sys.platform == "win32":
            # Python's own startup on Windows needs a few OS-managed vars
            # (SYSTEMROOT in particular) or it can fail to initialize at
            # all - there's no POSIX-style minimal PATH-only env here.
            env = {
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "TEMP": str(workdir),
                "TMP": str(workdir),
            }
        else:
            env = {"PATH": "/usr/bin:/bin", "HOME": str(workdir), "LANG": "C.UTF-8"}

        start = time.monotonic()
        exit_code = -1
        stdout = ""
        stderr = ""
        try:
            proc = subprocess.run(
                [sys.executable, str(script), payload],
                cwd=workdir,
                env=env,
                preexec_fn=_limit_resources if sys.platform != "win32" else None,
                timeout=timeout_s,
                capture_output=True,
                text=True,
            )
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as exc:
            exit_code = -1
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = ((exc.stderr or "") if isinstance(exc.stderr, str) else "") + "\n[killed: timed out]"
        except Exception as exc:  # noqa: BLE001 - report as evidence, don't crash the API
            stderr = f"[subprocess sandbox error: {exc}]"
        duration_ms = int((time.monotonic() - start) * 1000)

        marker_created = _MARKER_PATH.exists()
        _clear_marker()
        shutil.rmtree(workdir, ignore_errors=True)

        return ExecutionEvidence(
            evidence_id=str(uuid.uuid4()),
            hypothesis_id=hypothesis_id,
            run_id=run_id,
            phase=phase,
            container_id="subprocess-fallback",
            exit_code=exit_code,
            stdout=stdout[:_MAX_LOG_CHARS],
            stderr=stderr[:_MAX_LOG_CHARS],
            filesystem_diff={
                "created": [_MARKER_PATH.as_posix()] if marker_created else [],
                "modified": [],
                "deleted": [],
            },
            network_egress_attempts=[],
            policy_violations=[
                "reduced-isolation: ran without Docker (network namespace not sandboxed) "
                "because no Docker daemon was reachable on this host"
            ],
            duration_ms=duration_ms,
        )
