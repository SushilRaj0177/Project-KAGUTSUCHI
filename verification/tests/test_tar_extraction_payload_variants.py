"""Every tar-extraction payload variant in attacks/payload_variants.py
must actually exploit vulnerable() and be inert against fixed() -
confirms the vulnerability isn't tied to one specific traversal shape.
"""

from __future__ import annotations

import sys

import pytest

from verification.attacks.payload_variants import MARKER, TAR_EXTRACTION_PAYLOAD_VARIANTS
from verification.attacks.run_local import run_local_attack
from verification.fixtures.tar_extraction import fixed, vulnerable
from verification.models import ExecutionPhase

posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="marker path targets a POSIX filesystem"
)


@posix_only
@pytest.mark.parametrize("name,payload", TAR_EXTRACTION_PAYLOAD_VARIANTS.items())
def test_variant_exploits_vulnerable(name, payload):
    evidence = run_local_attack(vulnerable, payload, "hyp-1", f"run-{name}", ExecutionPhase.BEFORE)
    assert evidence.filesystem_diff["created"] == [MARKER], (
        f"tar-extraction payload variant {name!r} ({payload!r}) did not create the marker file"
    )


@pytest.mark.parametrize("name,payload", TAR_EXTRACTION_PAYLOAD_VARIANTS.items())
def test_variant_rejected_by_fixed(name, payload):
    with pytest.raises(ValueError):
        fixed(payload)
