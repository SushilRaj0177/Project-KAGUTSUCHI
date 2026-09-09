"""Every SQL injection payload variant in attacks/payload_variants.py must
actually exploit vulnerable() and be inert against fixed() - confirms the
vulnerability isn't tied to one specific comment/termination style.
"""

from __future__ import annotations

import sys

import pytest

from verification.attacks.payload_variants import MARKER, SQL_PAYLOAD_VARIANTS
from verification.attacks.run_local import run_local_attack
from verification.fixtures.sql_injection import fixed, vulnerable
from verification.models import ExecutionPhase

posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="ATTACH DATABASE '/tmp/...' targets a POSIX filesystem"
)


@posix_only
@pytest.mark.parametrize("name,payload", SQL_PAYLOAD_VARIANTS.items())
def test_variant_exploits_vulnerable(name, payload):
    evidence = run_local_attack(vulnerable, payload, "hyp-1", f"run-{name}", ExecutionPhase.BEFORE)
    assert evidence.filesystem_diff["created"] == [MARKER], (
        f"SQL payload variant {name!r} ({payload!r}) did not create the marker file"
    )


@pytest.mark.parametrize("name,payload", SQL_PAYLOAD_VARIANTS.items())
def test_variant_inert_against_fixed(name, payload):
    # fixed()'s parameterized query never raises on this input - it just
    # binds the whole payload as a literal name and finds no match.
    evidence = run_local_attack(fixed, payload, "hyp-1", "run-1", ExecutionPhase.AFTER)
    assert evidence.filesystem_diff["created"] == []
    assert evidence.exit_code == 0
