"""
Real, unmocked tests: these run actual subprocesses through
wsqfai.security.sandbox.run_in_subprocess_sandbox and confirm the kernel
itself enforces the confinement Landlock is supposed to add - not that
some Python-level flag got set, but that a real payload actually fails
when it tries to escape. Ported from
engine-archive/kagutsuchi/tests/system/test_landlock.py.

Skipped entirely on a kernel without Landlock (pre-5.13, or a host whose
own outer sandbox blocks the landlock_* syscalls) rather than failing -
consistent with subprocess_runner's own honest-disclosure-over-silent-
degradation design.
"""
from __future__ import annotations

import os
import sys

import pytest

from wsqfai.security.landlock import landlock_abi_version
from wsqfai.security.sandbox import run_in_subprocess_sandbox

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or landlock_abi_version() is None,
    reason="Landlock unavailable on this platform/kernel",
)


def test_reports_landlock_confinement_in_policy_violations():
    evidence = run_in_subprocess_sandbox(candidate_code="print('hi')", payload="x")
    assert any("Landlock ABI" in v for v in evidence.policy_violations)


def test_write_outside_scratch_dir_is_actually_blocked_by_the_kernel():
    candidate = """
try:
    with open("/tmp/../etc/wsqfai_test_should_not_exist", "w") as f:
        f.write("x")
    print("WROTE")
except PermissionError:
    print("BLOCKED")
"""
    evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload="x")
    assert evidence.stdout.strip() == "BLOCKED"
    assert not os.path.exists("/etc/wsqfai_test_should_not_exist")


def test_outbound_tcp_connect_is_actually_blocked_by_the_kernel():
    candidate = """
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect(("1.1.1.1", 80))
    print("CONNECTED")
except PermissionError:
    print("BLOCKED")
except OSError:
    print("BLOCKED")
"""
    evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload="x")
    assert evidence.stdout.strip() == "BLOCKED"


def test_marker_file_mechanism_still_works_under_confinement():
    # The regression that matters most: verification's proof-of-exploit is
    # creating /tmp/wsqfai_pwned. If Landlock confinement broke that,
    # every verification run would silently stop proving anything.
    candidate = """
from pathlib import Path
Path("/tmp/wsqfai_pwned").write_text("proof")
"""
    evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload="x")
    assert evidence.marker_created is True


def test_read_access_is_left_unrestricted():
    # Deliberate: Landlock here only handles write-ish access rights, so
    # the interpreter can still read its own stdlib/site-packages, and a
    # candidate reading ordinary files isn't broken by this.
    candidate = """
with open("/etc/hostname") as f:
    f.read()
print("READ_OK")
"""
    evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload="x")
    assert evidence.stdout.strip() == "READ_OK"
