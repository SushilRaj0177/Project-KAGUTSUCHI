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
from verification.hypothesis.sql_fallback import SQL_INJECTION_FALLBACK_HYPOTHESIS
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


def test_mismatched_run_ids_are_inconclusive():
    before = fake_evidence_vulnerable_before()
    after = fake_evidence_fixed_after().model_copy(update={"run_id": "a-different-run"})

    result = verify(HYP, before, after, PAYLOAD, PAYLOAD)

    assert result.verdict == Verdict.INCONCLUSIVE
    assert result.confidence == 0.0
    assert before.run_id in result.summary
    assert after.run_id in result.summary


def test_missing_created_key_treated_as_not_vulnerable():
    # Malformed evidence: filesystem_diff has no "created" key at all,
    # rather than an empty list - must not raise, must not be treated as
    # exploited.
    before = fake_evidence_vulnerable_before().model_copy(update={"filesystem_diff": {}})
    after = fake_evidence_fixed_after().model_copy(update={"filesystem_diff": {}})

    result = verify(HYP, before, after, PAYLOAD, PAYLOAD)

    assert result.verdict == Verdict.FALSE_POSITIVE


def test_incidental_docker_files_do_not_count_as_the_marker():
    # Regression test for the real-Docker bug (see COORDINATION.md's "real
    # Docker run just caught a genuine verdict-logic bug" entry): a real
    # container's filesystem_diff["created"] always contains incidental
    # noise (.pyc bytecode cache, /workspace, /workspace/candidate.py) in
    # BOTH before and after runs, regardless of whether the exploit fired.
    # _marker_created() must key on the specific marker path, not on
    # "created" being non-empty.
    noise = [
        "/workspace",
        "/workspace/candidate.py",
        "/workspace/__pycache__",
        "/workspace/__pycache__/re.cpython-311.pyc",
        "/workspace/__pycache__/subprocess.cpython-311.pyc",
    ]
    before = fake_evidence_vulnerable_before().model_copy(
        update={"filesystem_diff": {"created": noise + ["/tmp/kagutsuchi_pwned"], "modified": [], "deleted": []}}
    )
    # after (fixed): same incidental noise, but the marker itself is absent.
    after = fake_evidence_fixed_after().model_copy(
        update={"filesystem_diff": {"created": list(noise), "modified": [], "deleted": []}}
    )

    result = verify(HYP, before, after, PAYLOAD, PAYLOAD)

    assert result.verdict == Verdict.VERIFIED_FIXED


def test_verify_is_fixture_agnostic_same_check_scores_the_sql_hypothesis():
    # The actual "no special-casing" proof: swap in the SQL injection
    # hypothesis (a completely different vulnerability class, different
    # payload/attack_vector text) and verify() still scores it correctly
    # using the exact same _marker_created() check - because both fixtures
    # share the same observable proof convention (the marker file path),
    # not because regression/verify.py knows anything about SQL vs. shell.
    sql_hyp = SQL_INJECTION_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": "finding-0002"})
    sql_payload = sql_hyp.payload

    result = verify(
        sql_hyp, fake_evidence_vulnerable_before(), fake_evidence_fixed_after(), sql_payload, sql_payload
    )

    assert result.verdict == Verdict.VERIFIED_FIXED
    assert result.hypothesis_id == sql_hyp.hypothesis_id
    assert result.finding_id == "finding-0002"
