"""Unit tests for the third (insecure deserialization) fixture: the
byte-identical payload must exploit vulnerable() and be inert against
fixed() - same shape as the other two fixture test suites, proving the
pipeline generalizes to a third, structurally different vulnerability
class (see COORDINATION.md's generalization milestone entries).
"""

from __future__ import annotations

import base64
import json
import sys

import pytest

from verification.attacks.run_local import MARKER_PATH, run_local_attack
from verification.fixtures.insecure_deserialization import fixed, vulnerable
from verification.hypothesis.deserialization_fallback import (
    DESERIALIZATION_FALLBACK_HYPOTHESIS,
)
from verification.models import ExecutionPhase

PAYLOAD = DESERIALIZATION_FALLBACK_HYPOTHESIS.payload

# The exploit's __reduce__ calls os.system("touch ...") - a POSIX shell
# command, same reason the other two fixtures' exploit-side tests are
# POSIX-only (this fixture targets the same Linux Docker sandbox).
posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="exploit shells out via os.system('touch ...'), see comment above"
)


@posix_only
def test_vulnerable_creates_marker_file_via_reduce():
    evidence = run_local_attack(
        vulnerable, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.BEFORE
    )
    assert evidence.filesystem_diff["created"] == [MARKER_PATH.as_posix()]


def test_fixed_json_loads_never_creates_marker():
    # Runs cross-platform: fixed() never calls pickle.loads at all.
    evidence = run_local_attack(fixed, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.AFTER)
    assert evidence.filesystem_diff["created"] == []
    assert evidence.exit_code == -1  # json.loads raises on the non-UTF-8 pickle bytes


def test_fixed_accepts_legitimate_json_payloads():
    # Sanity check: fixed() isn't just rejecting everything - real JSON
    # data round-trips correctly.
    legit = base64.b64encode(json.dumps({"name": "alice"}).encode()).decode()
    assert fixed(legit) == {"name": "alice"}


def test_vulnerable_unpickles_legitimate_data_too():
    # Sanity check: vulnerable() isn't only exploitable, it "works" for
    # normal, non-malicious callers too (that's what makes it plausible
    # in real code, not an obviously-broken function).
    import pickle

    legit = base64.b64encode(pickle.dumps({"name": "alice"})).decode()
    assert vulnerable(legit) == {"name": "alice"}
