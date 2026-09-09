"""Unit tests for the single integration entry point, pipeline.score()."""

from __future__ import annotations

from verification.evidence.fakes import fake_evidence_fixed_after, fake_evidence_vulnerable_before
from verification.hypothesis.fallback import NETDIAG_FALLBACK_HYPOTHESIS
from verification.hypothesis.sql_fallback import SQL_INJECTION_FALLBACK_HYPOTHESIS
from verification.models import SecurityFinding, SensitiveOp, Severity, Verdict
from verification.pipeline import score


def _fake_finding() -> SecurityFinding:
    return SecurityFinding(
        finding_id="finding-0001",
        file_path="verification/fixtures/netdiag.py",
        symbol="vulnerable",
        diff_hunk='+    return os.system(f"ping -c 1 {host}")',
        sensitive_op=SensitiveOp.SHELL_EXEC,
        rationale="untrusted host interpolated into a shell command",
        detected_by="manual-p0",
        severity_hint=Severity.HIGH,
    )


def test_score_generates_hypothesis_when_not_given(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)  # force the fallback hypothesis
    result = score(_fake_finding(), fake_evidence_vulnerable_before(), fake_evidence_fixed_after())
    assert result.verdict == Verdict.VERIFIED_FIXED
    assert result.finding_id == "finding-0001"


def test_score_uses_explicit_hypothesis_for_fk_consistency():
    hyp = NETDIAG_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": "finding-0001"})
    result = score(
        _fake_finding(), fake_evidence_vulnerable_before(), fake_evidence_fixed_after(), hypothesis=hyp
    )
    assert result.hypothesis_id == hyp.hypothesis_id
    assert result.verdict == Verdict.VERIFIED_FIXED


def test_score_generates_the_sql_fallback_when_told_to(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)  # force the fallback path
    finding = _fake_finding().model_copy(update={"finding_id": "finding-0002"})

    result = score(
        finding,
        fake_evidence_vulnerable_before(),
        fake_evidence_fixed_after(),
        fallback=SQL_INJECTION_FALLBACK_HYPOTHESIS,
    )

    assert result.hypothesis_id == SQL_INJECTION_FALLBACK_HYPOTHESIS.hypothesis_id
    assert result.verdict == Verdict.VERIFIED_FIXED
