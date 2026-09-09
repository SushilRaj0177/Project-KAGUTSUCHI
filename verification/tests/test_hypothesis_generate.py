"""generate() must degrade to the hardcoded fallback when Groq is unavailable
(no GROQ_API_KEY set in this test env), never raise."""

from __future__ import annotations

import pytest

import verification.hypothesis.generate as generate_module
from verification.hypothesis.generate import generate
from verification.hypothesis.groq_client import GroqUnavailable
from verification.hypothesis.sql_fallback import SQL_INJECTION_FALLBACK_HYPOTHESIS
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


def test_generate_falls_back_on_response_missing_expected_keys(monkeypatch):
    # Valid JSON, but not shaped like the prompt asked for.
    monkeypatch.setattr(
        generate_module, "generate_hypothesis_json", lambda prompt: {"unexpected": "shape"}
    )
    hyp = generate(_fake_finding())
    assert hyp.generated_by == "fallback:hardcoded-v1"


def test_generate_falls_back_on_non_dict_response(monkeypatch):
    # Valid JSON (an array), but not a dict at all.
    monkeypatch.setattr(generate_module, "generate_hypothesis_json", lambda prompt: [1, 2, 3])
    hyp = generate(_fake_finding())
    assert hyp.generated_by == "fallback:hardcoded-v1"


def test_generate_falls_back_on_wrong_typed_field(monkeypatch):
    # `payload` must be a string per the contract; here it's a nested object.
    monkeypatch.setattr(
        generate_module,
        "generate_hypothesis_json",
        lambda prompt: {
            "security_property": "no injection",
            "attack_vector": "shell metacharacter",
            "payload": {"not": "a string"},
            "expected_if_vulnerable": "marker file created",
            "expected_if_safe": "marker file absent",
        },
    )
    hyp = generate(_fake_finding())
    assert hyp.generated_by == "fallback:hardcoded-v1"


def test_generate_falls_back_to_the_given_fallback_not_always_netdiag(monkeypatch):
    # Regression test: generate() used to hardcode the netdiag fallback
    # for every fixture. Passing a different fallback must actually be
    # honored, not silently ignored.
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    finding = _fake_finding()

    hyp = generate(finding, fallback=SQL_INJECTION_FALLBACK_HYPOTHESIS)

    assert hyp.hypothesis_id == SQL_INJECTION_FALLBACK_HYPOTHESIS.hypothesis_id
    assert hyp.finding_id == finding.finding_id
    assert "ATTACH DATABASE" in hyp.payload


def test_generate_with_no_fallback_propagates_groq_unavailable(monkeypatch):
    # fallback=None is for arbitrary/unknown code (see
    # integration/upload_pipeline.py) where no hardcoded fallback is
    # safe - the original failure must propagate, not be swallowed.
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(GroqUnavailable):
        generate(_fake_finding(), fallback=None)


def test_generate_with_no_fallback_propagates_validation_error(monkeypatch):
    monkeypatch.setattr(
        generate_module,
        "generate_hypothesis_json",
        lambda prompt: {
            "security_property": "x",
            "attack_vector": "x",
            "payload": {"not": "a string"},
            "expected_if_vulnerable": "x",
            "expected_if_safe": "x",
        },
    )

    with pytest.raises(Exception):  # noqa: B017 - ValidationError, not swallowed into a fallback
        generate(_fake_finding(), fallback=None)


def test_generate_uses_live_response_when_well_formed(monkeypatch):
    monkeypatch.setattr(
        generate_module,
        "generate_hypothesis_json",
        lambda prompt: {
            "security_property": "no injection",
            "attack_vector": "shell metacharacter",
            "payload": "127.0.0.1; id",
            "expected_if_vulnerable": "marker file created",
            "expected_if_safe": "marker file absent",
        },
    )
    hyp = generate(_fake_finding())
    assert hyp.payload == "127.0.0.1; id"
    assert hyp.generated_by != "fallback:hardcoded-v1"
