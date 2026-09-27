"""Hardcoded fallback AttackHypothesis for the second (SQL injection)
fixture. Same purpose as fallback.py's netdiag fallback: used when Groq is
unreachable/rate-limited so the demo never dies on a live LLM call.
"""

from __future__ import annotations

from verification.models import AttackHypothesis

SQL_INJECTION_FALLBACK_HYPOTHESIS = AttackHypothesis(
    hypothesis_id="fallback-sql-injection-shell-exec-0001",
    finding_id="",  # filled in by the caller from the real SecurityFinding
    security_property="no SQL injection via the name parameter of the users lookup",
    attack_vector=(
        "name is string-interpolated into executescript(), so a `'; ...; --` "
        "payload chains arbitrary extra SQL statements onto the intended "
        "SELECT, rather than being treated as a literal search value"
    ),
    payload="x'; ATTACH DATABASE '/tmp/kagutsuchi_pwned' AS pwn; CREATE TABLE pwn.t(x); --",
    expected_if_vulnerable=(
        "filesystem_diff shows /tmp/kagutsuchi_pwned created (the injected "
        "ATTACH DATABASE + CREATE TABLE ran as additional SQL statements)"
    ),
    expected_if_safe=(
        "/tmp/kagutsuchi_pwned is never created; the parameterized query "
        "treats the whole payload as a literal name and returns no rows"
    ),
    generated_by="fallback:hardcoded-v1",
)


def with_finding_id(finding_id: str) -> AttackHypothesis:
    return SQL_INJECTION_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": finding_id})
