"""Unit tests for the P0 fixture itself: the byte-identical payload must
exploit vulnerable() and be inert against fixed()."""

from __future__ import annotations

import sys

import pytest

from verification.attacks.run_local import MARKER_PATH, run_local_attack
from verification.fixtures.netdiag import fixed, vulnerable
from verification.hypothesis.fallback import NETDIAG_FALLBACK_HYPOTHESIS
from verification.models import ExecutionPhase

PAYLOAD = NETDIAG_FALLBACK_HYPOTHESIS.payload

# The fixture targets a POSIX shell (`;` as a command separator, `ping -c`),
# matching the Linux Docker sandbox system/sandbox will execute it in - not
# a Windows dev box's cmd.exe. Run these on Linux/macOS or inside the
# sandbox; skip locally on Windows.
posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="fixture targets a POSIX shell, see comment above"
)


@posix_only
def test_vulnerable_creates_marker_file():
    evidence = run_local_attack(
        vulnerable, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.BEFORE
    )
    assert evidence.filesystem_diff["created"] == [str(MARKER_PATH)]


def test_fixed_rejects_payload_and_never_creates_marker():
    evidence = run_local_attack(fixed, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.AFTER)
    assert evidence.filesystem_diff["created"] == []
    assert evidence.exit_code == -1  # fixed() raises ValueError on invalid host


@posix_only
def test_fixed_accepts_a_legitimate_host():
    # Sanity check: fixed() isn't just rejecting everything (POSIX `ping -c`).
    assert fixed("127.0.0.1") in (0, 1)  # 0 = reachable, 1 = unreachable, both valid
