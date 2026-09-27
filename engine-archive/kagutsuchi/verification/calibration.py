"""Confidence calibration: compare the LLM's own stated confidence in a
hypothesis against whether the sandbox actually proved it correct.

This is research direction D from the original brief (KAGUTSUCHI.md §22):
"Compare LLM confidence against actual execution outcomes." More
pitch/research value than end-user value, but cheap to add since
hypothesis generation already runs - see
verification/hypothesis/generate.py::generate_with_confidence().

Deliberately NOT a contracts/ type: confidence is verification/-internal
calibration data, not part of the SecurityFinding -> AttackHypothesis ->
ExecutionEvidence -> VerificationResult pipeline. Adding it here required
no contract change and no coordination with system/.
"""

from __future__ import annotations

from dataclasses import dataclass

from verification.attacks.run_local import MARKER_PATH
from verification.models import ExecutionEvidence


@dataclass(frozen=True)
class CalibrationEntry:
    hypothesis_id: str
    stated_confidence: float  # the model's own 0-1 estimate, from generate_with_confidence()
    actually_succeeded: bool  # ground truth: did the marker actually get created?


def entry_from_evidence(
    hypothesis_id: str, stated_confidence: float, before_evidence: ExecutionEvidence
) -> CalibrationEntry:
    """Build a CalibrationEntry from real evidence - the same marker
    check regression/verify.py uses, so "actually_succeeded" means
    exactly what it means everywhere else in this codebase."""
    succeeded = MARKER_PATH.as_posix() in before_evidence.filesystem_diff.get("created", [])
    return CalibrationEntry(hypothesis_id, stated_confidence, succeeded)


def brier_score(entries: list[CalibrationEntry]) -> float:
    """Mean squared error between stated confidence and the binary
    outcome. 0.0 is perfect calibration; 0.25 is what you'd get by always
    guessing 50%; 1.0 is maximally confident and wrong every time."""
    if not entries:
        raise ValueError("no calibration entries to score")
    return sum(
        (e.stated_confidence - (1.0 if e.actually_succeeded else 0.0)) ** 2 for e in entries
    ) / len(entries)


def calibration_summary(entries: list[CalibrationEntry]) -> dict:
    """Bucket entries into confidence deciles and report the actual
    success rate per bucket - the standard calibration-curve view. A
    well-calibrated model's "70-80% confident" bucket should succeed
    roughly 70-80% of the time, not 30% or 100%."""
    if not entries:
        raise ValueError("no calibration entries to summarize")

    buckets: dict[int, list[CalibrationEntry]] = {}
    for e in entries:
        bucket = min(int(e.stated_confidence * 10), 9)
        buckets.setdefault(bucket, []).append(e)

    return {
        "n": len(entries),
        "brier_score": brier_score(entries),
        "buckets": {
            f"{b * 10}-{b * 10 + 10}%": {
                "n": len(es),
                "actual_success_rate": sum(e.actually_succeeded for e in es) / len(es),
                "mean_stated_confidence": sum(e.stated_confidence for e in es) / len(es),
            }
            for b, es in sorted(buckets.items())
        },
    }
