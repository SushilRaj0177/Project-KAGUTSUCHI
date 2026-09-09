"""Every payload variant in attacks/payload_variants.py must actually
exploit vulnerable() and be rejected by fixed() - not just look
plausible. Confirms the fixture's vulnerability isn't an artifact of one
specific shell metacharacter."""

from __future__ import annotations

import sys

import pytest

from verification.attacks.payload_variants import MARKER, PAYLOAD_VARIANTS
from verification.attacks.run_local import run_local_attack
from verification.fixtures.netdiag import fixed, vulnerable
from verification.models import ExecutionPhase

posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="payloads target a POSIX shell, see attacks/payload_variants.py"
)


@posix_only
@pytest.mark.parametrize("name,payload", PAYLOAD_VARIANTS.items())
def test_variant_exploits_vulnerable(name, payload):
    evidence = run_local_attack(vulnerable, payload, "hyp-1", f"run-{name}", ExecutionPhase.BEFORE)
    assert evidence.filesystem_diff["created"] == [MARKER], (
        f"payload variant {name!r} ({payload!r}) did not create the marker file"
    )


@pytest.mark.parametrize("name,payload", PAYLOAD_VARIANTS.items())
def test_variant_rejected_by_fixed(name, payload):
    with pytest.raises(ValueError):
        fixed(payload)
