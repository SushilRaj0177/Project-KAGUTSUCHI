"""Given a before/after ExecutionEvidence pair (byte-identical payload),
score against the AttackHypothesis's expected signals and emit a
VerificationResult - the final verification/-owned artifact in the pipeline.

Verdict is derived from observable evidence (filesystem_diff / exit_code),
never from LLM self-assessment, per PLAN.md's "definition of done".
"""

from __future__ import annotations

import uuid

from verification.attacks.run_local import MARKER_PATH
from verification.models import (
    AttackHypothesis,
    ExecutionEvidence,
    Verdict,
    VerificationResult,
)


def _marker_created(evidence: ExecutionEvidence) -> bool:
    # Check for the specific attack marker, not "was anything created" -
    # a real Docker container creates incidental .pyc/workspace files on
    # every run regardless of exploit success (see COORDINATION.md's
    # "real Docker run just caught a genuine verdict-logic bug" entry).
    return MARKER_PATH.as_posix() in evidence.filesystem_diff.get("created", [])


def verify(
    hypothesis: AttackHypothesis,
    before: ExecutionEvidence,
    after: ExecutionEvidence,
    before_payload: str,
    after_payload: str,
) -> VerificationResult:
    replay_identical = before_payload == after_payload == hypothesis.payload

    if before.run_id != after.run_id:
        verdict = Verdict.INCONCLUSIVE
        confidence = 0.0
        summary = (
            f"before/after evidence come from different run_ids "
            f"({before.run_id!r} vs {after.run_id!r}) - not a comparable pair."
        )
        return VerificationResult(
            verdict_id=str(uuid.uuid4()),
            finding_id=hypothesis.finding_id,
            hypothesis_id=hypothesis.hypothesis_id,
            before_evidence_id=before.evidence_id,
            after_evidence_id=after.evidence_id,
            verdict=verdict,
            replay_identical=replay_identical,
            confidence=confidence,
            summary=summary,
        )

    before_vulnerable = _marker_created(before)
    after_vulnerable = _marker_created(after)

    if not before_vulnerable:
        verdict = Verdict.FALSE_POSITIVE
        confidence = 0.9
        summary = "Exploit never succeeded before the fix - hypothesis was wrong."
    elif before_vulnerable and not after_vulnerable:
        verdict = Verdict.VERIFIED_FIXED
        confidence = 1.0 if replay_identical else 0.6
        summary = "Exploit succeeded before the fix, blocked after - verified fixed."
    elif before_vulnerable and after_vulnerable:
        verdict = Verdict.STILL_VULNERABLE
        confidence = 1.0 if replay_identical else 0.6
        summary = "Exploit succeeds both before and after - still vulnerable."
    else:
        verdict = Verdict.INCONCLUSIVE
        confidence = 0.0
        summary = "Evidence did not resolve to a clear verdict."

    return VerificationResult(
        verdict_id=str(uuid.uuid4()),
        finding_id=hypothesis.finding_id,
        hypothesis_id=hypothesis.hypothesis_id,
        before_evidence_id=before.evidence_id,
        after_evidence_id=after.evidence_id,
        verdict=verdict,
        replay_identical=replay_identical,
        confidence=confidence,
        summary=summary,
    )
