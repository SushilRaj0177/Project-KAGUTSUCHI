"""Unit tests for the fourth (path traversal) fixture: the byte-identical
payload must exploit vulnerable() and be inert against fixed() - same
shape as the other three fixture test suites.
"""

from __future__ import annotations

import os
import sys

import pytest

from verification.attacks.run_local import MARKER_PATH, run_local_attack
from verification.fixtures.path_traversal import _BASE_DIR, fixed, vulnerable
from verification.hypothesis.path_traversal_fallback import PATH_TRAVERSAL_FALLBACK_HYPOTHESIS
from verification.models import ExecutionPhase

PAYLOAD = PATH_TRAVERSAL_FALLBACK_HYPOTHESIS.payload

# Reliably writing to the literal "/tmp/..." path (not some drive-relative
# equivalent) is a POSIX filesystem assumption - same reason the other
# three fixtures' exploit-side tests are POSIX-only (this fixture targets
# the same Linux Docker sandbox).
posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="marker path targets a POSIX filesystem, see comment above"
)


@posix_only
def test_vulnerable_writes_outside_the_base_directory():
    evidence = run_local_attack(vulnerable, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.BEFORE)
    assert evidence.filesystem_diff["created"] == [MARKER_PATH.as_posix()]


def test_fixed_rejects_absolute_path_payload_and_never_writes_it():
    evidence = run_local_attack(fixed, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.AFTER)
    assert evidence.filesystem_diff["created"] == []
    assert evidence.exit_code == -1  # fixed() raises ValueError


@pytest.mark.parametrize(
    "traversal_payload",
    [
        "/tmp/kagutsuchi_pwned",
        "../../../../tmp/kagutsuchi_pwned",
        "../../kagutsuchi_pwned",
    ],
)
def test_fixed_rejects_traversal_variants(traversal_payload):
    with pytest.raises(ValueError):
        fixed(traversal_payload)


def test_fixed_accepts_a_legitimate_relative_filename():
    # Sanity check: fixed() isn't just rejecting everything.
    fixed("legit_upload.txt")
    expected_path = os.path.join(_BASE_DIR, "legit_upload.txt")
    assert os.path.exists(expected_path)
    os.remove(expected_path)
