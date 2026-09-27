"""Unit tests for verification/calibration.py's scoring functions."""

from __future__ import annotations

import pytest

from verification.calibration import (
    CalibrationEntry,
    brier_score,
    calibration_summary,
    entry_from_evidence,
)
from verification.evidence.fakes import fake_evidence_vulnerable_before, fake_evidence_fixed_after


def test_brier_score_zero_for_perfect_calibration():
    entries = [
        CalibrationEntry("h1", 1.0, True),
        CalibrationEntry("h2", 0.0, False),
    ]
    assert brier_score(entries) == 0.0


def test_brier_score_quarter_for_always_guessing_half():
    entries = [
        CalibrationEntry("h1", 0.5, True),
        CalibrationEntry("h2", 0.5, False),
    ]
    assert brier_score(entries) == pytest.approx(0.25)


def test_brier_score_one_for_maximally_overconfident_and_wrong():
    entries = [CalibrationEntry("h1", 1.0, False)]
    assert brier_score(entries) == pytest.approx(1.0)


def test_brier_score_raises_on_empty_input():
    with pytest.raises(ValueError):
        brier_score([])


def test_calibration_summary_buckets_by_decile():
    entries = [
        CalibrationEntry("h1", 0.82, True),
        CalibrationEntry("h2", 0.88, True),
        CalibrationEntry("h3", 0.15, False),
    ]
    summary = calibration_summary(entries)

    assert summary["n"] == 3
    assert summary["buckets"]["80-90%"]["n"] == 2
    assert summary["buckets"]["80-90%"]["actual_success_rate"] == 1.0
    assert summary["buckets"]["10-20%"]["n"] == 1
    assert summary["buckets"]["10-20%"]["actual_success_rate"] == 0.0


def test_calibration_summary_confidence_of_exactly_one_lands_in_top_bucket():
    # int(1.0 * 10) == 10, which must clamp into the 90-100% bucket, not
    # overflow into a nonexistent 11th bucket.
    entries = [CalibrationEntry("h1", 1.0, True)]
    summary = calibration_summary(entries)
    assert "90-100%" in summary["buckets"]
    assert summary["buckets"]["90-100%"]["n"] == 1


def test_calibration_summary_raises_on_empty_input():
    with pytest.raises(ValueError):
        calibration_summary([])


def test_entry_from_evidence_reads_the_real_marker_check():
    vuln_entry = entry_from_evidence("h1", 0.9, fake_evidence_vulnerable_before())
    assert vuln_entry.actually_succeeded is True
    assert vuln_entry.stated_confidence == 0.9

    fixed_entry = entry_from_evidence("h2", 0.9, fake_evidence_fixed_after())
    assert fixed_entry.actually_succeeded is False
