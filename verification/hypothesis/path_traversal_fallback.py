"""Hardcoded fallback AttackHypothesis for the fourth (path traversal)
fixture. Same purpose as the other three fallbacks: used when Groq is
unreachable/rate-limited so the demo never dies on a live LLM call.
"""

from __future__ import annotations

from verification.models import AttackHypothesis

PATH_TRAVERSAL_FALLBACK_HYPOTHESIS = AttackHypothesis(
    hypothesis_id="fallback-path-traversal-0001",
    finding_id="",  # filled in by the caller from the real SecurityFinding
    security_property="uploaded filename cannot escape the intended upload directory",
    attack_vector=(
        "filename is joined onto the base directory with os.path.join(), "
        "which silently discards the base directory whenever filename is "
        "an absolute path - so an absolute filename writes directly to "
        "that path, completely outside the intended directory"
    ),
    payload="/tmp/kagutsuchi_pwned",
    expected_if_vulnerable=(
        "filesystem_diff shows /tmp/kagutsuchi_pwned created (the write "
        "landed at the attacker-chosen absolute path, not inside the "
        "intended upload directory)"
    ),
    expected_if_safe=(
        "/tmp/kagutsuchi_pwned is never created; the function raises "
        "ValueError rejecting the path as outside the allowed directory"
    ),
    generated_by="fallback:hardcoded-v1",
)


def with_finding_id(finding_id: str) -> AttackHypothesis:
    return PATH_TRAVERSAL_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": finding_id})
