"""Single entry point for integration/: finding + evidence in, verdict out.

Collapses the internal call sequence (hypothesis.generate -> regression.verify)
into one function so integration/ doesn't need to know verification/'s
internal module layout - see COORDINATION.md "PR #1 is merged" entry, item 2.
"""

from __future__ import annotations

from verification.hypothesis.generate import generate
from verification.models import AttackHypothesis, ExecutionEvidence, SecurityFinding, VerificationResult
from verification.regression.verify import verify


def score(
    finding: SecurityFinding,
    before_evidence: ExecutionEvidence,
    after_evidence: ExecutionEvidence,
    hypothesis: AttackHypothesis | None = None,
) -> VerificationResult:
    """Score a before/after evidence pair produced from `finding`.

    `hypothesis` should be the *same* AttackHypothesis object whose payload
    was fed to system/sandbox for both the before and after runs (real
    verdicts depend on the replay being byte-identical, which this function
    can't guarantee on its own). Pass it explicitly whenever you already
    have it. If omitted, a new hypothesis is generated from `finding` here
    and its payload is treated as what was run for both phases - only
    correct if the caller made sure of that out-of-band; note its
    `hypothesis_id` may then differ from `before_evidence.hypothesis_id` /
    `after_evidence.hypothesis_id` if those were produced against an
    earlier hypothesis, so this fallback exists for convenience/demo use,
    not as the integration-correct path.
    """
    if hypothesis is None:
        hypothesis = generate(finding)

    return verify(
        hypothesis,
        before_evidence,
        after_evidence,
        before_payload=hypothesis.payload,
        after_payload=hypothesis.payload,
    )
