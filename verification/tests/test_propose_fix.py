"""Unit tests for propose_fix() - mocks generate_hypothesis_json at the
same layer generate()'s own tests do, so no real Groq call is needed.
"""

from __future__ import annotations

import pytest

import verification.hypothesis.propose_fix as propose_fix_module
from verification.hypothesis.groq_client import GroqUnavailable
from verification.hypothesis.propose_fix import FixValidationError, propose_fix
from verification.models import AttackHypothesis, SecurityFinding, SensitiveOp, Severity


def _fake_finding() -> SecurityFinding:
    return SecurityFinding(
        finding_id="finding-0001",
        file_path="uploads/tmp123.py",
        symbol="vulnerable",
        diff_hunk='def vulnerable(host):\n    return os.system(f"ping -c 1 {host}")',
        sensitive_op=SensitiveOp.SHELL_EXEC,
        rationale="untrusted host interpolated into a shell command",
        detected_by="ast.shell_exec.os_system",
        severity_hint=Severity.HIGH,
    )


def _fake_hypothesis() -> AttackHypothesis:
    return AttackHypothesis(
        hypothesis_id="hyp-0001",
        finding_id="finding-0001",
        security_property="no command injection via host",
        attack_vector="host is interpolated into a shell string",
        payload="127.0.0.1; touch /tmp/kagutsuchi_pwned",
        expected_if_vulnerable="marker file created",
        expected_if_safe="marker file never created",
        generated_by="test",
    )


def test_propose_fix_returns_valid_source_when_well_formed(monkeypatch):
    good_source = (
        "def vulnerable(host):\n"
        "    import subprocess\n"
        "    return subprocess.run(['ping', '-c', '1', host], shell=False).returncode\n"
    )
    monkeypatch.setattr(
        propose_fix_module,
        "generate_hypothesis_json",
        lambda prompt: {"fixed_source": good_source},
    )

    result = propose_fix(_fake_finding(), _fake_hypothesis())

    assert result == good_source


def test_propose_fix_raises_on_syntax_error(monkeypatch):
    monkeypatch.setattr(
        propose_fix_module,
        "generate_hypothesis_json",
        lambda prompt: {"fixed_source": "def vulnerable(host)\n    pass"},  # missing colon
    )

    with pytest.raises(FixValidationError, match="not valid Python"):
        propose_fix(_fake_finding(), _fake_hypothesis())


def test_propose_fix_raises_on_wrong_function_name(monkeypatch):
    monkeypatch.setattr(
        propose_fix_module,
        "generate_hypothesis_json",
        lambda prompt: {"fixed_source": "def totally_different_name(host):\n    return 0\n"},
    )

    with pytest.raises(FixValidationError, match="does not define a function named"):
        propose_fix(_fake_finding(), _fake_hypothesis())


def test_propose_fix_raises_on_wrong_signature(monkeypatch):
    monkeypatch.setattr(
        propose_fix_module,
        "generate_hypothesis_json",
        lambda prompt: {"fixed_source": "def vulnerable(host, extra_arg):\n    return 0\n"},
    )

    with pytest.raises(FixValidationError, match="must take exactly one parameter"):
        propose_fix(_fake_finding(), _fake_hypothesis())


def test_propose_fix_raises_on_missing_key(monkeypatch):
    monkeypatch.setattr(
        propose_fix_module,
        "generate_hypothesis_json",
        lambda prompt: {"unexpected": "shape"},
    )

    with pytest.raises(FixValidationError, match="fixed_source"):
        propose_fix(_fake_finding(), _fake_hypothesis())


def test_propose_fix_raises_on_non_string_fixed_source(monkeypatch):
    monkeypatch.setattr(
        propose_fix_module,
        "generate_hypothesis_json",
        lambda prompt: {"fixed_source": {"not": "a string"}},
    )

    with pytest.raises(FixValidationError, match="must be a string"):
        propose_fix(_fake_finding(), _fake_hypothesis())


def test_propose_fix_does_not_swallow_groq_unavailable(monkeypatch):
    # No fallback exists here - a Groq failure must propagate, not be
    # silently converted into a fake fix.
    def _raise(prompt):
        raise GroqUnavailable("rate limited")

    monkeypatch.setattr(propose_fix_module, "generate_hypothesis_json", _raise)

    with pytest.raises(GroqUnavailable):
        propose_fix(_fake_finding(), _fake_hypothesis())


def test_propose_fix_rejects_async_function(monkeypatch):
    # build_runnable_script() calls `function_name(sys.argv[1])` with no
    # `await` - an async fix would silently never execute (an un-awaited
    # coroutine, not an exception), producing a misleading verdict rather
    # than a loud failure. Must be rejected before it ever reaches the
    # sandbox.
    monkeypatch.setattr(
        propose_fix_module,
        "generate_hypothesis_json",
        lambda prompt: {"fixed_source": "async def vulnerable(host):\n    return 0\n"},
    )

    with pytest.raises(FixValidationError, match="not async"):
        propose_fix(_fake_finding(), _fake_hypothesis())
