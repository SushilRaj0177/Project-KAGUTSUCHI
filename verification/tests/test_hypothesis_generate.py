"""generate() must degrade to the hardcoded fallback when Groq is unavailable
(no GROQ_API_KEY set in this test env), never raise."""

from __future__ import annotations

from verification.hypothesis.generate import generate
from verification.models import SecurityFinding, SensitiveOp, Severity


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


def test_generate_falls_back_without_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    finding = _fake_finding()

    hyp = generate(finding)

    assert hyp.finding_id == finding.finding_id
    assert hyp.generated_by == "fallback:hardcoded-v1"
    assert "touch /tmp/kagutsuchi_pwned" in hyp.payload
