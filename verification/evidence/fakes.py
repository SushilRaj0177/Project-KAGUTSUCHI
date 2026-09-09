"""Hand-written fake ExecutionEvidence instances for unit-testing regression/
without waiting on the real system/sandbox, per CONTRIBUTING.md's contract
boundary rule.
"""

from __future__ import annotations

from verification.models import ExecutionEvidence, ExecutionPhase

_COMMON = dict(
    hypothesis_id="fallback-netdiag-shell-exec-0001",
    run_id="fake-run-0001",
    container_id="fake-container",
    stdout="",
    stderr="",
    network_egress_attempts=[],
    policy_violations=[],
    duration_ms=42,
    timestamp="2026-09-09T00:00:00Z",
)


def _diff(created: list[str]) -> dict[str, list[str]]:
    """Matches system/sandbox/docker_runner.py's confirmed shape (see
    COORDINATION.md): all three buckets always present."""
    return {"created": created, "modified": [], "deleted": []}


def fake_evidence_vulnerable_before() -> ExecutionEvidence:
    """Marker file created: the injected command executed."""
    return ExecutionEvidence(
        evidence_id="fake-evidence-before-vuln",
        phase=ExecutionPhase.BEFORE,
        exit_code=0,
        filesystem_diff=_diff(["/tmp/kagutsuchi_pwned"]),
        **_COMMON,
    )


def fake_evidence_fixed_after() -> ExecutionEvidence:
    """Marker file not created: the fix blocked the injection."""
    return ExecutionEvidence(
        evidence_id="fake-evidence-after-fixed",
        phase=ExecutionPhase.AFTER,
        exit_code=-1,
        filesystem_diff=_diff([]),
        **_COMMON,
    )


def fake_evidence_still_vulnerable_after() -> ExecutionEvidence:
    """Marker file still created after the "fix": regression case."""
    return ExecutionEvidence(
        evidence_id="fake-evidence-after-still-vuln",
        phase=ExecutionPhase.AFTER,
        exit_code=0,
        filesystem_diff=_diff(["/tmp/kagutsuchi_pwned"]),
        **_COMMON,
    )


def fake_evidence_before_never_vulnerable() -> ExecutionEvidence:
    """Marker never created even before the fix: hypothesis was wrong."""
    return ExecutionEvidence(
        evidence_id="fake-evidence-before-false-positive",
        phase=ExecutionPhase.BEFORE,
        exit_code=-1,
        filesystem_diff=_diff([]),
        **_COMMON,
    )
