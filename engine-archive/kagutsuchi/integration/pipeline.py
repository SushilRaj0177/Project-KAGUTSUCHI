"""
The actual end-to-end wiring: system/'s SecurityFinding in, a real
verification/.VerificationResult out. This is the ONLY module that
imports from both system/ and verification/ — per CONTRIBUTING.md,
neither of those packages imports the other directly.

Sequence: detect (finding, given) -> hypothesize (verification/) ->
attack (system/sandbox) -> replay (system/sandbox) -> verdict
(verification/regression).
"""
from __future__ import annotations

from dataclasses import dataclass

from contracts import AttackHypothesis, ExecutionEvidence, SecurityFinding
from integration.adapters import to_system, to_verification
from system.orchestration import new_run_id, replay_attack, run_attack
from verification.hypothesis.fallback import NETDIAG_FALLBACK_HYPOTHESIS
from verification.hypothesis.generate import generate as generate_hypothesis
from verification.models import AttackHypothesis as VAttackHypothesis
from verification.models import ExecutionEvidence as VExecutionEvidence
from verification.models import SecurityFinding as VSecurityFinding
from verification.models import VerificationResult
from verification.regression.verify import verify as verify_regression


@dataclass
class FullRunBundle:
    """Every artifact produced along the way, not just the final verdict —
    what a real dashboard record needs (see integration/publish_result.py)
    that run_full_verification's plain VerificationResult doesn't carry."""

    finding: VSecurityFinding
    hypothesis: VAttackHypothesis
    before: VExecutionEvidence
    after: VExecutionEvidence
    result: VerificationResult


def run_full_verification_detailed(
    *,
    vulnerable_code: str,
    fixed_code: str,
    finding: SecurityFinding,
    fallback: VAttackHypothesis = NETDIAG_FALLBACK_HYPOTHESIS,
) -> FullRunBundle:
    """Same detect->hypothesize->attack->replay->verdict loop as
    run_full_verification, but returns every intermediate artifact
    instead of just the verdict."""
    v_finding: VSecurityFinding = to_verification(finding, VSecurityFinding)
    v_hypothesis: VAttackHypothesis = generate_hypothesis(v_finding, fallback=fallback)
    s_hypothesis: AttackHypothesis = to_system(v_hypothesis, AttackHypothesis)

    run_id = new_run_id()
    before: ExecutionEvidence = run_attack(
        vulnerable_code=vulnerable_code, hypothesis=s_hypothesis, run_id=run_id
    )
    after: ExecutionEvidence = replay_attack(
        fixed_code=fixed_code, hypothesis=s_hypothesis, run_id=run_id
    )

    v_before: VExecutionEvidence = to_verification(before, VExecutionEvidence)
    v_after: VExecutionEvidence = to_verification(after, VExecutionEvidence)

    result = verify_regression(
        v_hypothesis,
        v_before,
        v_after,
        before_payload=v_hypothesis.payload,
        after_payload=v_hypothesis.payload,
    )
    return FullRunBundle(
        finding=v_finding, hypothesis=v_hypothesis, before=v_before, after=v_after, result=result
    )


def run_full_verification(
    *,
    vulnerable_code: str,
    fixed_code: str,
    finding: SecurityFinding,
    fallback: VAttackHypothesis = NETDIAG_FALLBACK_HYPOTHESIS,
) -> VerificationResult:
    """Run one finding through the full detect->hypothesize->attack->replay
    ->verdict loop against real system/ and verification/ modules.

    `fallback` defaults to the netdiag hypothesis for backward
    compatibility (integration/demo.py's existing call). Pass the
    matching per-fixture fallback for any other fixture, e.g.
    `fallback=SQL_INJECTION_FALLBACK_HYPOTHESIS` for demo_sql.py — see
    verification/hypothesis/generate.py's own `fallback=` parameter, which
    this just threads through.
    """
    return run_full_verification_detailed(
        vulnerable_code=vulnerable_code, fixed_code=fixed_code, finding=finding, fallback=fallback
    ).result
