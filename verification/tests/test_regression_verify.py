"""Unit tests for regression/verify.py using hand-written fake
ExecutionEvidence (verification/evidence/fakes.py) - no system/ needed."""

from __future__ import annotations

from verification.evidence.fakes import (
    fake_evidence_before_never_vulnerable,
    fake_evidence_fixed_after,
    fake_evidence_still_vulnerable_after,
    fake_evidence_vulnerable_before,
)
from verification.hypothesis.fallback import NETDIAG_FALLBACK_HYPOTHESIS
from verification.models import Verdict
from verification.regression.verify import verify

HYP = NETDIAG_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": "finding-0001"})
PAYLOAD = HYP.payload


def test_verified_fixed():
    result = verify(
        HYP, fake_evidence_vulnerable_before(), fake_evidence_fixed_after(), PAYLOAD, PAYLOAD
    )
    assert result.verdict == Verdict.VERIFIED_FIXED
    assert result.replay_identical is True
    assert result.confidence == 1.0


def test_still_vulnerable():
    result = verify(
        HYP,
        fake_evidence_vulnerable_before(),
        fake_evidence_still_vulnerable_after(),
        PAYLOAD,
        PAYLOAD,
    )
    assert result.verdict == Verdict.STILL_VULNERABLE


def test_false_positive():
    result = verify(
        HYP,
        fake_evidence_before_never_vulnerable(),
        fake_evidence_fixed_after(),
        PAYLOAD,
        PAYLOAD,
    )
    assert result.verdict == Verdict.FALSE_POSITIVE


def test_replay_not_identical_lowers_confidence():
    result = verify(
        HYP,
        fake_evidence_vulnerable_before(),
        fake_evidence_fixed_after(),
        PAYLOAD,
        "a different payload",
    )
    assert result.verdict == Verdict.VERIFIED_FIXED
    assert result.replay_identical is False
    assert result.confidence < 1.0
