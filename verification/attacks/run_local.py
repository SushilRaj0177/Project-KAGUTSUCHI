"""Local (non-Docker) attack runner for independent testing of the fixture.

Real, isolated execution against the sandbox is system/sandbox's job
(Docker, per CONTRIBUTING.md - never built here). This module exists so
verification/ can exercise its own fixture + hypothesis end-to-end (fixture
-> attack -> evidence-shaped result) without waiting on system/ to exist,
per PLAN.md Phase 1. Its output is shaped like ExecutionEvidence but is
NOT a substitute for the real sandboxed evidence system/ will produce.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Callable

from verification.models import ExecutionEvidence, ExecutionPhase

MARKER_PATH = Path("/tmp/kagutsuchi_pwned")


def _clear_marker() -> None:
    try:
        MARKER_PATH.unlink()
    except FileNotFoundError:
        pass


def run_local_attack(
    target: Callable[[str], int],
    payload: str,
    hypothesis_id: str,
    run_id: str,
    phase: ExecutionPhase,
) -> ExecutionEvidence:
    """Run `target(payload)` locally and observe the marker-file side effect.

    Not sandboxed - for local unit testing only. Never point this at
    untrusted payloads outside a throwaway/dev environment.
    """
    _clear_marker()
    start = time.monotonic()
    exit_code = 0
    stderr = ""
    try:
        exit_code = target(payload)
    except Exception as exc:  # noqa: BLE001 - capture as evidence, don't crash
        exit_code = -1
        stderr = str(exc)
    duration_ms = int((time.monotonic() - start) * 1000)

    marker_created = MARKER_PATH.exists()
    _clear_marker()

    return ExecutionEvidence(
        evidence_id=str(uuid.uuid4()),
        hypothesis_id=hypothesis_id,
        run_id=run_id,
        phase=phase,
        container_id="local-no-sandbox",
        exit_code=exit_code,
        stdout="",
        stderr=stderr,
        # Matches system/sandbox/docker_runner.py's confirmed shape (see
        # COORDINATION.md): all three buckets always present, not just
        # "created" - even though this local runner only ever detects
        # marker-file creation, not modifications or deletions.
        filesystem_diff={
            "created": [str(MARKER_PATH)] if marker_created else [],
            "modified": [],
            "deleted": [],
        },
        network_egress_attempts=[],
        policy_violations=[],
        duration_ms=duration_ms,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
