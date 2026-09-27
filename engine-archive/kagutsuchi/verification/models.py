"""Re-export of the shared contract types from contracts/models.py.

verification/ used to keep an independent mirror of these four types; per
COORDINATION.md ("Fixture CONFIRMED + PR #1 review notes" / "PR #1 is
merged"), that duplication is now collapsed to one source of truth in
contracts/. Import from here (or straight from `contracts`) rather than
redefining these types again.
"""

from __future__ import annotations

from contracts import (
    AttackHypothesis,
    ExecutionEvidence,
    ExecutionPhase,
    SecurityFinding,
    SensitiveOp,
    Severity,
    Verdict,
    VerificationResult,
)

__all__ = [
    "SecurityFinding",
    "AttackHypothesis",
    "ExecutionEvidence",
    "VerificationResult",
    "SensitiveOp",
    "Severity",
    "ExecutionPhase",
    "Verdict",
]
