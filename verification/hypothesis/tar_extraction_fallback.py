"""Hardcoded fallback AttackHypothesis for the fifth (tar-extraction path
traversal) fixture. Same purpose as the other four fallbacks: used when
Groq is unreachable/rate-limited so the demo never dies on a live LLM call.
"""

from __future__ import annotations

from verification.models import AttackHypothesis

TAR_EXTRACTION_FALLBACK_HYPOTHESIS = AttackHypothesis(
    hypothesis_id="fallback-tar-extraction-0001",
    finding_id="",  # filled in by the caller from the real SecurityFinding
    security_property="an extracted tar member cannot escape the intended extraction directory",
    attack_vector=(
        "member_name becomes the literal path of the archive's one entry, "
        "and tarfile.extractall() is called with no filter, so a member "
        "name containing '../' is extracted exactly as named - escaping "
        "the intended directory entirely (CVE-2007-4559's exact shape)"
    ),
    payload="../kagutsuchi_pwned",
    expected_if_vulnerable=(
        "filesystem_diff shows /tmp/kagutsuchi_pwned created (the "
        "extracted member landed one directory above the intended "
        "extraction directory, at the attacker-chosen path)"
    ),
    expected_if_safe=(
        "/tmp/kagutsuchi_pwned is never created; the function raises "
        "ValueError rejecting the member path as outside the extraction directory"
    ),
    generated_by="fallback:hardcoded-v1",
)


def with_finding_id(finding_id: str) -> AttackHypothesis:
    return TAR_EXTRACTION_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": finding_id})
