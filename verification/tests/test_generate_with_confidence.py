"""Unit tests for generate_with_confidence() - mocks generate_hypothesis_json
at the same layer generate()'s own tests do."""

from __future__ import annotations

import pytest

import verification.hypothesis.generate as generate_module
from verification.hypothesis.generate import generate_with_confidence
from verification.hypothesis.groq_client import GroqUnavailable
from verification.models import SecurityFinding, SensitiveOp, Severity

_WELL_FORMED = {
    "security_property": "no injection",
    "attack_vector": "shell metacharacter",
    "payload": "127.0.0.1; touch /tmp/kagutsuchi_pwned",
    "expected_if_vulnerable": "marker file created",
    "expected_if_safe": "marker file absent",
    "confidence": 0.85,
}


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


def test_returns_the_stated_confidence_when_well_formed(monkeypatch):
    monkeypatch.setattr(generate_module, "generate_hypothesis_json", lambda prompt: _WELL_FORMED)

    hyp, confidence = generate_with_confidence(_fake_finding())

    assert hyp.payload == _WELL_FORMED["payload"]
    assert confidence == 0.85


def test_defaults_to_half_when_confidence_key_missing(monkeypatch):
    raw = {k: v for k, v in _WELL_FORMED.items() if k != "confidence"}
    monkeypatch.setattr(generate_module, "generate_hypothesis_json", lambda prompt: raw)

    _, confidence = generate_with_confidence(_fake_finding())

    assert confidence == 0.5


def test_defaults_to_half_when_confidence_is_not_a_number(monkeypatch):
    raw = {**_WELL_FORMED, "confidence": "very confident"}
    monkeypatch.setattr(generate_module, "generate_hypothesis_json", lambda prompt: raw)

    _, confidence = generate_with_confidence(_fake_finding())

    assert confidence == 0.5


def test_bool_is_not_accepted_as_a_confidence_value(monkeypatch):
    # bool is a subclass of int in Python - True/False must not silently
    # become confidence 1.0/0.0.
    raw = {**_WELL_FORMED, "confidence": True}
    monkeypatch.setattr(generate_module, "generate_hypothesis_json", lambda prompt: raw)

    _, confidence = generate_with_confidence(_fake_finding())

    assert confidence == 0.5


def test_clamps_out_of_range_confidence(monkeypatch):
    raw = {**_WELL_FORMED, "confidence": 1.7}
    monkeypatch.setattr(generate_module, "generate_hypothesis_json", lambda prompt: raw)

    _, confidence = generate_with_confidence(_fake_finding())

    assert confidence == 1.0

    raw2 = {**_WELL_FORMED, "confidence": -0.3}
    monkeypatch.setattr(generate_module, "generate_hypothesis_json", lambda prompt: raw2)

    _, confidence2 = generate_with_confidence(_fake_finding())

    assert confidence2 == 0.0


def test_fallback_path_returns_none_confidence(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    hyp, confidence = generate_with_confidence(_fake_finding())

    assert confidence is None
    assert hyp.generated_by == "fallback:hardcoded-v1"


def test_fallback_none_propagates_like_generate(monkeypatch):
    def _raise(prompt):
        raise GroqUnavailable("down")

    monkeypatch.setattr(generate_module, "generate_hypothesis_json", _raise)

    with pytest.raises(GroqUnavailable):
        generate_with_confidence(_fake_finding(), fallback=None)
