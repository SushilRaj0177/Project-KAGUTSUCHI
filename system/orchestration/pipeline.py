"""
Orchestration glue: analysis -> sandbox, and before/after replay.

Verdict computation (comparing before/after evidence into a
VerificationResult) is owned by verification/regression, not here — this
module only produces the two ExecutionEvidence objects that feed it.
"""
from __future__ import annotations

import uuid

from contracts import AttackHypothesis, ExecutionEvidence, ExecutionPhase
from system.sandbox import run_in_sandbox


def new_run_id() -> str:
    return str(uuid.uuid4())


def run_attack(
    *, vulnerable_code: str, hypothesis: AttackHypothesis, run_id: str
) -> ExecutionEvidence:
    """Run the hypothesis's payload against the vulnerable ("before") code."""
    return run_in_sandbox(
        candidate_code=vulnerable_code,
        payload=hypothesis.payload,
        hypothesis_id=hypothesis.hypothesis_id,
        run_id=run_id,
        phase=ExecutionPhase.BEFORE,
    )


def replay_attack(
    *, fixed_code: str, hypothesis: AttackHypothesis, run_id: str
) -> ExecutionEvidence:
    """Replay the EXACT SAME payload against the fixed ("after") code."""
    return run_in_sandbox(
        candidate_code=fixed_code,
        payload=hypothesis.payload,
        hypothesis_id=hypothesis.hypothesis_id,
        run_id=run_id,
        phase=ExecutionPhase.AFTER,
    )
