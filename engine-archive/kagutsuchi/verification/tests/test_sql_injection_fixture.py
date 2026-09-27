"""Unit tests for the second (SQL injection) fixture: the byte-identical
payload must exploit vulnerable() and be inert against fixed() - same
shape as test_netdiag_fixture.py, proving the pipeline generalizes rather
than being netdiag-specific (see COORDINATION.md's "Next milestone" entry).
"""

from __future__ import annotations

import sys

import pytest

from verification.attacks.run_local import MARKER_PATH, run_local_attack
from verification.fixtures.sql_injection import fixed, vulnerable
from verification.hypothesis.sql_fallback import SQL_INJECTION_FALLBACK_HYPOTHESIS
from verification.models import ExecutionPhase

PAYLOAD = SQL_INJECTION_FALLBACK_HYPOTHESIS.payload

# ATTACH DATABASE '/tmp/...' only resolves as a real path on a POSIX
# filesystem - same reason test_netdiag_fixture.py's exploit-side test is
# POSIX-only (this fixture targets the same Linux Docker sandbox).
posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="marker path targets a POSIX filesystem, see comment above"
)


@posix_only
def test_vulnerable_creates_marker_file_via_attach_database():
    evidence = run_local_attack(
        vulnerable, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.BEFORE
    )
    assert evidence.filesystem_diff["created"] == [MARKER_PATH.as_posix()]


def test_fixed_parameterized_query_never_creates_marker():
    # Runs cross-platform: fixed() never attempts to open the ATTACH
    # target at all, since the payload is bound as an inert literal value.
    evidence = run_local_attack(fixed, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.AFTER)
    assert evidence.filesystem_diff["created"] == []
    assert evidence.exit_code == 0  # no exception - just zero matching rows


def test_fixed_returns_no_rows_for_a_legitimate_lookup_too():
    # Sanity check: fixed() isn't just rejecting everything - a real name
    # seeded in _seed() should be found.
    assert fixed("alice") == 1
    assert fixed("nobody-by-this-name") == 0
