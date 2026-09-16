"""
Real, unmocked tests: these run actual subprocesses through
system.sandbox.subprocess_runner.run_in_subprocess_sandbox and confirm
the kernel itself enforces the confinement Landlock is supposed to add -
not that some Python-level flag got set, but that a real malicious
payload actually fails when it tries to escape.

Skipped entirely on a kernel without Landlock (pre-5.13, or a host whose
own outer sandbox blocks the landlock_* syscalls) rather than failing -
consistent with how the rest of this project treats infrastructure that
may or may not be available (see test_isolation_probe.py), and with
subprocess_runner.py's own honest-disclosure-over-silent-degradation
design.
"""
from __future__ import annotations

import sys

import pytest

from contracts import ExecutionPhase
from system.sandbox.landlock import landlock_abi_version
from system.sandbox.subprocess_runner import run_in_subprocess_sandbox

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or landlock_abi_version() is None,
    reason="Landlock unavailable on this platform/kernel",
)


def test_reports_landlock_confinement_in_policy_violations():
    evidence = run_in_subprocess_sandbox(
        candidate_code="print('hi')",
        payload="x",
        hypothesis_id="h",
        run_id="r",
        phase=ExecutionPhase.BEFORE,
    )
    assert any("Landlock ABI" in v for v in evidence.policy_violations)


def test_write_outside_scratch_dir_is_actually_blocked_by_the_kernel():
    candidate = """
try:
    with open("/tmp/../etc/kagutsuchi_test_should_not_exist", "w") as f:
        f.write("x")
    print("WROTE")
except PermissionError:
    print("BLOCKED")
"""
    evidence = run_in_subprocess_sandbox(
        candidate_code=candidate, payload="x", hypothesis_id="h", run_id="r", phase=ExecutionPhase.BEFORE
    )
    assert evidence.stdout.strip() == "BLOCKED"
    import os

    assert not os.path.exists("/etc/kagutsuchi_test_should_not_exist")


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
    evidence = run_in_subprocess_sandbox(
        candidate_code=candidate, payload="x", hypothesis_id="h", run_id="r", phase=ExecutionPhase.BEFORE
    )
    assert evidence.stdout.strip() == "BLOCKED"


def test_marker_file_mechanism_still_works_under_confinement():
    # This is the regression that matters most: every attack fixture's
    # proof-of-exploit is creating /tmp/kagutsuchi_pwned. If Landlock
    # confinement broke that, every existing detector would silently stop
    # proving anything.
    candidate = """
from pathlib import Path
Path("/tmp/kagutsuchi_pwned").write_text("proof")
"""
    evidence = run_in_subprocess_sandbox(
        candidate_code=candidate, payload="x", hypothesis_id="h", run_id="r", phase=ExecutionPhase.BEFORE
    )
    assert evidence.filesystem_diff["created"] == ["/tmp/kagutsuchi_pwned"]


def test_read_access_is_left_unrestricted():
    # Deliberate: Landlock here only handles write-ish access rights, so
    # the interpreter can still read its own stdlib/site-packages, and a
    # candidate reading ordinary files isn't broken by this.
    candidate = """
with open("/etc/hostname") as f:
    f.read()
print("READ_OK")
"""
    evidence = run_in_subprocess_sandbox(
        candidate_code=candidate, payload="x", hypothesis_id="h", run_id="r", phase=ExecutionPhase.BEFORE
    )
    assert evidence.stdout.strip() == "READ_OK"
