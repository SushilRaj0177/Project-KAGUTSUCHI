"""Unit tests for the fifth (tar-extraction path traversal) fixture: the
byte-identical payload must exploit vulnerable() and be inert against
fixed() - same shape as the other four fixture test suites.
"""

from __future__ import annotations

import os
import sys

import pytest

from verification.attacks.run_local import MARKER_PATH, run_local_attack
from verification.fixtures.tar_extraction import _SAFE_DIR, fixed, vulnerable
from verification.hypothesis.tar_extraction_fallback import TAR_EXTRACTION_FALLBACK_HYPOTHESIS
from verification.models import ExecutionPhase

PAYLOAD = TAR_EXTRACTION_FALLBACK_HYPOTHESIS.payload

# Reliably writing to the literal "/tmp/..." path is a POSIX filesystem
# assumption - same reason the other traversal-shaped fixtures' exploit-
# side tests are POSIX-only (this fixture targets the same Linux Docker
# sandbox).
posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="marker path targets a POSIX filesystem, see comment above"
)


@posix_only
def test_vulnerable_extracts_outside_the_safe_directory():
    evidence = run_local_attack(vulnerable, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.BEFORE)
    assert evidence.filesystem_diff["created"] == [MARKER_PATH.as_posix()]


def test_fixed_rejects_traversal_payload_and_never_extracts_it():
    evidence = run_local_attack(fixed, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.AFTER)
    assert evidence.filesystem_diff["created"] == []
    assert evidence.exit_code == -1  # fixed() raises ValueError


@pytest.mark.parametrize(
    "traversal_payload",
    [
        "../kagutsuchi_pwned",
        "../../tmp/kagutsuchi_pwned",
        "subdir/../../kagutsuchi_pwned",
    ],
)
def test_fixed_rejects_traversal_variants(traversal_payload):
    with pytest.raises(ValueError):
        fixed(traversal_payload)


def test_fixed_accepts_a_legitimate_member_name():
    # Sanity check: fixed() isn't just rejecting everything.
    fixed("legit_member.txt")
    expected_path = os.path.join(_SAFE_DIR, "legit_member.txt")
    assert os.path.exists(expected_path)
    os.remove(expected_path)
