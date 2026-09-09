"""Hand-written fake ExecutionEvidence instances for unit-testing regression/
without waiting on the real system/sandbox, per CONTRIBUTING.md's contract
boundary rule.
"""

from __future__ import annotations

from verification.models import EvidencePhase, ExecutionEvidence

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


def fake_evidence_vulnerable_before() -> ExecutionEvidence:
    """Marker file created: the injected command executed."""
    return ExecutionEvidence(
        evidence_id="fake-evidence-before-vuln",
        phase=EvidencePhase.before,
        exit_code=0,
        filesystem_diff={"created": ["/tmp/kagutsuchi_pwned"]},
        **_COMMON,
    )


def fake_evidence_fixed_after() -> ExecutionEvidence:
    """Marker file not created: the fix blocked the injection."""
    return ExecutionEvidence(
        evidence_id="fake-evidence-after-fixed",
        phase=EvidencePhase.after,
        exit_code=-1,
        filesystem_diff={"created": []},
        **_COMMON,
    )


def fake_evidence_still_vulnerable_after() -> ExecutionEvidence:
    """Marker file still created after the "fix": regression case."""
    return ExecutionEvidence(
        evidence_id="fake-evidence-after-still-vuln",
        phase=EvidencePhase.after,
        exit_code=0,
        filesystem_diff={"created": ["/tmp/kagutsuchi_pwned"]},
        **_COMMON,
    )


def fake_evidence_before_never_vulnerable() -> ExecutionEvidence:
    """Marker never created even before the fix: hypothesis was wrong."""
    return ExecutionEvidence(
        evidence_id="fake-evidence-before-false-positive",
        phase=EvidencePhase.before,
        exit_code=-1,
        filesystem_diff={"created": []},
        **_COMMON,
    )
