"""P0 fixture: a tiny network-diagnostics CLI with one real sink.

`vulnerable()` builds a shell command by string-interpolating untrusted
input, so shell metacharacters in `host` let an attacker chain arbitrary
commands. `fixed()` validates `host` against a strict allowlist and
executes via an argv list with shell=False, so metacharacters are inert.

Both functions are exercised with the byte-identical payload by
verification/attacks and system/sandbox — see COORDINATION.md's P0
fixture entry for the attack contract this fixture is built against.
"""

from __future__ import annotations

import os
import re
import subprocess

_HOSTNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9\-\.]{0,253}[A-Za-z0-9])?$")


def vulnerable(host: str) -> int:
    """Command injection: `host` is interpolated straight into a shell string."""
    return os.system(f"ping -c 1 {host}")


def fixed(host: str) -> int:
    """Safe: allowlist-validate `host`, then exec with shell=False (no shell parsing)."""
    if not _HOSTNAME_RE.match(host):
        raise ValueError(f"invalid host: {host!r}")
    result = subprocess.run(
        ["ping", "-c", "1", host],
        shell=False,
        capture_output=True,
        timeout=5,
    )
    return result.returncode
