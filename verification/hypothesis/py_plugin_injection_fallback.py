"""Hardcoded fallback AttackHypothesis for the sixth (Python plugin
injection) fixture. Same purpose as the other five fallbacks: used when
Groq is unreachable/rate-limited so the demo never dies on a live LLM call.
"""

from __future__ import annotations

from verification.models import AttackHypothesis

PY_PLUGIN_INJECTION_FALLBACK_HYPOTHESIS = AttackHypothesis(
    hypothesis_id="fallback-py-plugin-injection-0001",
    finding_id="",  # filled in by the caller from the real SecurityFinding
    security_property="attacker-controlled content written to a .py plugin file cannot execute arbitrary code",
    attack_vector=(
        "code is written verbatim to a .py file and then imported via "
        "importlib - the imported module's top-level statements run with "
        "full interpreter privileges the moment it loads, so any Python "
        "code in `code` executes immediately"
    ),
    payload="open('/tmp/kagutsuchi_pwned', 'w').close()",
    expected_if_vulnerable=(
        "filesystem_diff shows /tmp/kagutsuchi_pwned created (the "
        "imported plugin's top-level statement ran as real Python code)"
    ),
    expected_if_safe=(
        "/tmp/kagutsuchi_pwned is never created; the content is written "
        "as plain text and never imported or executed"
    ),
    generated_by="fallback:hardcoded-v1",
)


def with_finding_id(finding_id: str) -> AttackHypothesis:
    return PY_PLUGIN_INJECTION_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": finding_id})
