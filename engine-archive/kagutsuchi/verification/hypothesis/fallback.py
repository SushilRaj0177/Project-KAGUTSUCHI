"""Hardcoded fallback AttackHypothesis for the P0 netdiag fixture.

Used when the Groq API is unreachable or rate-limited, so the demo never
dies on a live LLM call (see PLAN.md's "degrade, don't die" principle).
This is the exact hypothesis proposed in COORDINATION.md's P0 fixture entry.
"""

from __future__ import annotations

from verification.models import AttackHypothesis

NETDIAG_FALLBACK_HYPOTHESIS = AttackHypothesis(
    hypothesis_id="fallback-netdiag-shell-exec-0001",
    finding_id="",  # filled in by the caller from the real SecurityFinding
    security_property="no command injection via the host parameter of netdiag ping",
    attack_vector=(
        "host is concatenated into a shell string via os.system(); a ';' "
        "chains a second, attacker-controlled command onto the ping call"
    ),
    payload="127.0.0.1; touch /tmp/kagutsuchi_pwned",
    expected_if_vulnerable=(
        "filesystem_diff shows /tmp/kagutsuchi_pwned created "
        "(the injected `touch` executed as a second shell command)"
    ),
    expected_if_safe=(
        "/tmp/kagutsuchi_pwned is never created; the call either raises "
        "ValueError (invalid host) or exits without running injected commands"
    ),
    generated_by="fallback:hardcoded-v1",
)


def with_finding_id(finding_id: str) -> AttackHypothesis:
    return NETDIAG_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": finding_id})
