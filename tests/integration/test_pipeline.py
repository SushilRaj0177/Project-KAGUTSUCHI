"""Tests for integration/pipeline.py's wiring logic.

These mock out system.orchestration.pipeline's run_in_sandbox so they run
without a Docker daemon (unavailable in this dev environment) - they
verify the finding->hypothesis->evidence->verdict wiring and the
contracts<->verification/models adapters, not the sandbox's own
execution semantics (that's system/sandbox's own concern, and needs a
real Docker daemon to test for real).
"""
from __future__ import annotations

from unittest.mock import patch

from contracts import ExecutionEvidence, ExecutionPhase, SecurityFinding, SensitiveOp, Severity
from integration.pipeline import run_full_verification, run_full_verification_detailed
from verification.hypothesis.sql_fallback import SQL_INJECTION_FALLBACK_HYPOTHESIS
from verification.models import Verdict


def _fake_run_in_sandbox(
    *, candidate_code, payload, hypothesis_id, run_id, phase, timeout_s=10
):
    """Stand-in for the real Docker sandbox: 'vulnerable' code creates the
    marker file when the payload contains a shell separator, 'fixed' code
    never does, regardless of payload - mirrors the netdiag fixture's
    actual before/after behavior without needing Docker or `ping`."""
    is_vulnerable_code = "def vulnerable" in candidate_code
    created = ["/tmp/kagutsuchi_pwned"] if (is_vulnerable_code and ";" in payload) else []
    return ExecutionEvidence(
        hypothesis_id=hypothesis_id,
        run_id=run_id,
        phase=phase,
        container_id="fake-container",
        exit_code=0,
        filesystem_diff={"created": created, "modified": [], "deleted": []},
    )


def _netdiag_finding() -> SecurityFinding:
    return SecurityFinding(
        file_path="verification/fixtures/netdiag.py",
        symbol="vulnerable",
        diff_hunk="os.system(f'ping -c 1 {host}')",
        sensitive_op=SensitiveOp.SHELL_EXEC,
        rationale="test finding",
        detected_by="test",
        severity_hint=Severity.HIGH,
    )


@patch("system.orchestration.pipeline.run_in_sandbox", side_effect=_fake_run_in_sandbox)
def test_full_pipeline_verifies_the_fix(mock_run, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)  # force the hardcoded fallback hypothesis
    result = run_full_verification(
        vulnerable_code="def vulnerable(host): pass",
        fixed_code="def fixed(host): pass",
        finding=_netdiag_finding(),
    )
    assert result.verdict == Verdict.VERIFIED_FIXED
    assert result.replay_identical is True
    assert mock_run.call_count == 2


@patch("system.orchestration.pipeline.run_in_sandbox", side_effect=_fake_run_in_sandbox)
def test_full_pipeline_catches_an_incomplete_fix(mock_run, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    # "fixed_code" still contains the vulnerable path - simulates a patch
    # that didn't actually remove the injection.
    result = run_full_verification(
        vulnerable_code="def vulnerable(host): pass",
        fixed_code="def vulnerable(host): pass  # unpatched",
        finding=_netdiag_finding(),
    )
    assert result.verdict == Verdict.STILL_VULNERABLE


@patch("system.orchestration.pipeline.run_in_sandbox", side_effect=_fake_run_in_sandbox)
def test_full_pipeline_generalizes_to_a_second_vulnerability_class(mock_run, monkeypatch):
    # The actual "generalizes, no special-casing" proof: same
    # run_full_verification, same regression logic, a completely
    # different vulnerability class (SQL injection instead of command
    # injection), only the fallback hypothesis and finding differ.
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    finding = SecurityFinding(
        file_path="verification/fixtures/sql_injection.py",
        symbol="vulnerable",
        diff_hunk="cur.executescript(f\"SELECT * FROM users WHERE name = '{name}'\")",
        sensitive_op=SensitiveOp.SQL_QUERY,
        rationale="test finding",
        detected_by="test",
        severity_hint=Severity.HIGH,
    )
    result = run_full_verification(
        vulnerable_code="def vulnerable(name): pass",
        fixed_code="def fixed(name): pass",
        finding=finding,
        fallback=SQL_INJECTION_FALLBACK_HYPOTHESIS,
    )
    assert result.verdict == Verdict.VERIFIED_FIXED


@patch("system.orchestration.pipeline.run_in_sandbox", side_effect=_fake_run_in_sandbox)
def test_detailed_bundle_carries_every_intermediate_artifact(mock_run, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    finding = _netdiag_finding()
    bundle = run_full_verification_detailed(
        vulnerable_code="def vulnerable(host): pass",
        fixed_code="def fixed(host): pass",
        finding=finding,
    )
    assert bundle.result.verdict == Verdict.VERIFIED_FIXED
    assert bundle.finding.file_path == finding.file_path
    assert bundle.hypothesis.payload  # non-empty
    assert bundle.before.phase.value == "before"
    assert bundle.after.phase.value == "after"
