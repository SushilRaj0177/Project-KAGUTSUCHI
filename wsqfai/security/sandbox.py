"""
M4b: real, isolated execution of a candidate script - re-platformed from
`engine-archive/kagutsuchi/system/sandbox/subprocess_runner.py`, where this
exact approach was already exercised in production.

What it provides, versus just calling the candidate function in-process:
  - a genuinely separate OS process (a crash/hang in candidate code can't
    take this process down with it)
  - CPU, memory, output-size, and process-count limits (rlimits)
  - a scrubbed environment (candidate code cannot read secrets that were
    never handed to it)
  - a dedicated temp working directory, removed after the run
  - runs are serialized (one at a time) so concurrent verification runs
    can't race on the shared marker-file path
  - on a kernel that supports it (Linux 5.13+; network rules 6.7+),
    Landlock confinement (wsqfai/security/landlock.py): filesystem writes
    restricted to this run's own scratch directory plus a narrow /tmp
    allowance, and outbound TCP denied entirely. This is real KERNEL-
    enforced confinement, not just a resource cap, and needs zero elevated
    privilege - it works even inside a restricted container. Its real
    scope is disclosed exactly, never overstated: it only covers TCP (not
    UDP/raw sockets), and is simply absent (disclosed as such) on a kernel
    too old to have it.

This is NOT Docker-level isolation (no separate kernel, no network
namespace) - it's the honest, always-available fallback tier, exactly as
it was in the archived original, which never had Docker isolation working
in this project either (see engine-archive/kagutsuchi/system/sandbox/
docker_runner.py, which isn't re-platformed here - it needs a reachable
Docker daemon this environment doesn't provide, and reintroducing untested
Docker orchestration code would be exactly the "vaporware" this project's
own honesty discipline forbids).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from pydantic import BaseModel, Field

try:
    import resource  # POSIX only - doesn't exist on Windows
except ImportError:
    resource = None  # type: ignore[assignment]

if sys.platform != "win32":
    from wsqfai.security.landlock import restrict_current_process
else:
    restrict_current_process = None  # type: ignore[assignment]

_MAX_LOG_CHARS = 8000
_MEM_LIMIT_BYTES = 128 * 1024 * 1024
_MARKER_PATH = Path("/tmp/wsqfai_pwned")
_LANDLOCK_OUTCOME_FILENAME = ".landlock-outcome"

# Real per-container isolation (Docker) could run attacks concurrently
# since each gets its own container; this fallback shares one host, so
# serialize runs to keep one run's marker-file evidence from crossing with
# another's.
_lock = threading.Lock()


class ExecutionEvidence(BaseModel):
    """What actually happened when a candidate script ran, not what we
    expect it to do - the whole point of sandbox verification over a
    static match. `marker_created` is the concrete, checkable proof a
    shell-injection/code-execution payload actually ran arbitrary code,
    not just that the sink function was reached."""

    exit_code: int
    stdout: str
    stderr: str
    marker_created: bool
    duration_ms: int
    policy_violations: list[str] = Field(default_factory=list)


def _limit_resources(workdir: Path) -> None:
    """Runs in the forked child, after fork() but before exec() of the
    candidate script - the standard place to apply both rlimits (POSIX-
    only; a no-op on Windows) and Landlock confinement, since both need to
    be in effect for whatever gets exec'd next.

    Landlock's outcome can't be returned to the parent directly (this
    function runs in the child); it's written to a small file in
    `workdir` instead - itself covered by the writable-dir allow-rule
    Landlock's restriction grants - which the parent reads back after the
    subprocess finishes to build an honest policy_violations entry."""
    if resource is not None:
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        resource.setrlimit(resource.RLIMIT_AS, (_MEM_LIMIT_BYTES, _MEM_LIMIT_BYTES))
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))

    if restrict_current_process is not None:
        outcome = restrict_current_process(writable_dirs=[workdir, Path("/tmp")])
        try:
            (workdir / _LANDLOCK_OUTCOME_FILENAME).write_text(outcome.detail)
        except OSError:
            pass  # best-effort disclosure only - never let this fail the run


def _clear_marker() -> None:
    try:
        _MARKER_PATH.unlink()
    except FileNotFoundError:
        pass


def run_in_subprocess_sandbox(*, candidate_code: str, payload: str, timeout_s: int = 10) -> ExecutionEvidence:
    """Run `candidate_code` (a self-contained Python script, invoked as
    `python candidate.py <payload>`) in an isolated subprocess and report
    what happened. `payload` is passed as argv[1] - the candidate script
    is responsible for using it (e.g. calling the vulnerable function
    under test with it), not this function."""
    with _lock:
        _clear_marker()
        workdir = Path(tempfile.mkdtemp(prefix="wsqfai-"))
        script = workdir / "candidate.py"
        script.write_text(candidate_code)

        if sys.platform == "win32":
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
                preexec_fn=(lambda: _limit_resources(workdir)) if sys.platform != "win32" else None,
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
        except Exception as exc:  # noqa: BLE001 - report as evidence, don't crash the caller
            stderr = f"[subprocess sandbox error: {exc}]"
        duration_ms = int((time.monotonic() - start) * 1000)

        marker_created = _MARKER_PATH.exists()
        _clear_marker()

        landlock_detail: str | None = None
        outcome_file = workdir / _LANDLOCK_OUTCOME_FILENAME
        try:
            landlock_detail = outcome_file.read_text()
        except OSError:
            landlock_detail = None
        shutil.rmtree(workdir, ignore_errors=True)

        policy_violations = [
            "reduced-isolation: ran without Docker (no privileged/namespace-based sandbox reachable here)"
        ]
        if landlock_detail:
            policy_violations.append(landlock_detail)
        elif sys.platform != "win32":
            policy_violations.append("Landlock confinement was not applied (see landlock_abi_version)")

        return ExecutionEvidence(
            exit_code=exit_code,
            stdout=stdout[:_MAX_LOG_CHARS],
            stderr=stderr[:_MAX_LOG_CHARS],
            marker_created=marker_created,
            duration_ms=duration_ms,
            policy_violations=policy_violations,
        )
