"""Every deserialization payload variant in attacks/payload_variants.py
must actually exploit vulnerable() and be inert against fixed() -
confirms the vulnerability isn't tied to one specific __reduce__ callable
(eval vs. exec vs. subprocess.run vs. os.popen).
"""

from __future__ import annotations

import sys

import pytest

from verification.attacks.payload_variants import DESERIALIZATION_PAYLOAD_VARIANTS, MARKER
from verification.attacks.run_local import run_local_attack
from verification.fixtures.insecure_deserialization import fixed, vulnerable
from verification.models import ExecutionPhase

posix_only = pytest.mark.skipif(
    sys.platform == "win32",
    reason="every variant's __reduce__ shells out via a POSIX 'touch' command",
)


@posix_only
@pytest.mark.parametrize("name,payload", DESERIALIZATION_PAYLOAD_VARIANTS.items())
def test_variant_exploits_vulnerable(name, payload):
    evidence = run_local_attack(vulnerable, payload, "hyp-1", f"run-{name}", ExecutionPhase.BEFORE)
    assert evidence.filesystem_diff["created"] == [MARKER], (
        f"deserialization payload variant {name!r} did not create the marker file"
    )


@pytest.mark.parametrize("name,payload", DESERIALIZATION_PAYLOAD_VARIANTS.items())
def test_variant_rejected_by_fixed(name, payload):
    # json.loads() can't parse pickle bytes - every variant fails to
    # decode rather than executing anything.
    evidence = run_local_attack(fixed, payload, "hyp-1", "run-1", ExecutionPhase.AFTER)
    assert evidence.filesystem_diff["created"] == []
    assert evidence.exit_code == -1
