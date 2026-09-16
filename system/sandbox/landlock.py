"""
Unprivileged kernel-level confinement for system.sandbox.subprocess_runner,
using Landlock (Linux 5.13+, network rules 6.7+) -- the actual fix for the
two gaps that module's docstring disclosed ("no network namespace" and no
filesystem confinement), reachable with ZERO special privileges.

Every other real-isolation mechanism this project looked at (Docker,
hand-rolled namespaces/cgroups) needs the HOST to grant elevated kernel
capabilities to the process asking for it -- confirmed directly, via
system/sandbox/isolation_probe.py, that Render's standard plan refuses
all of them. Landlock is different by design: it's an LSM built
specifically so an ordinary, unprivileged process can restrict ITS OWN
access to the filesystem and network, no CAP_SYS_ADMIN or namespace
delegation required -- the same primitive Chrome and Firefox use to
sandbox their own renderer processes. It works inside exactly the kind
of restricted container the probe found Render running, because it was
built to.

What this actually enforces once applied to a process (and everything it
execve()s afterwards, since Landlock rules persist across exec — the
same property seccomp and namespaces have):
  - Filesystem: WRITE_FILE / MAKE_REG / REMOVE_FILE / REMOVE_DIR are
    handled (default-deny) everywhere except the run's own scratch
    directory and a narrow allowance under /tmp (needed because several
    fixtures' proof of exploitation IS creating /tmp/kagutsuchi_pwned --
    see verification/fixtures/*.py's shared docstring convention). Reads
    are deliberately left unrestricted: the Python interpreter itself
    needs to read its own stdlib/site-packages, and the residual risk of
    read-only disclosure is far smaller than the arbitrary-write risk
    this closes.
  - Network: CONNECT_TCP is handled with zero allow-rules, so every
    outbound TCP connection attempt is denied. This is Landlock's
    current real scope (kernel ABI 4+): UDP, raw sockets, and AF_UNIX
    are NOT covered, and that limitation is surfaced honestly in the
    policy_violations this produces -- never claimed as more than it is.

If the kernel doesn't support Landlock at all (pre-5.13, or the specific
syscalls are themselves blocked by an outer seccomp profile), every
function here fails closed and reports exactly that; subprocess_runner.py
disclosed the reduced-isolation case before this existed, and continues
to whenever this can't apply.
"""
from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from pathlib import Path

_libc = ctypes.CDLL(None, use_errno=True)
_syscall = _libc.syscall
_syscall.restype = ctypes.c_long

# Stable across every architecture Landlock ships on (x86_64, arm64,
# riscv, ...) -- assigned via the shared asm-generic syscall table these
# were added through, not architecture-specific legacy numbering.
_NR_LANDLOCK_CREATE_RULESET = 444
_NR_LANDLOCK_ADD_RULE = 445
_NR_LANDLOCK_RESTRICT_SELF = 446

_LANDLOCK_CREATE_RULESET_VERSION = 1 << 0
_LANDLOCK_RULE_PATH_BENEATH = 1

_ACCESS_FS_WRITE_FILE = 1 << 1
_ACCESS_FS_REMOVE_DIR = 1 << 4
_ACCESS_FS_REMOVE_FILE = 1 << 5
_ACCESS_FS_MAKE_REG = 1 << 8
_HANDLED_ACCESS_FS = _ACCESS_FS_WRITE_FILE | _ACCESS_FS_REMOVE_DIR | _ACCESS_FS_REMOVE_FILE | _ACCESS_FS_MAKE_REG

_ACCESS_NET_CONNECT_TCP = 1 << 1
_HANDLED_ACCESS_NET = _ACCESS_NET_CONNECT_TCP
# Network rules only exist from ABI 4 onward; a kernel stuck on an older
# Landlock ABI still gets the filesystem confinement above, just not this.
_MIN_ABI_FOR_NET_RULES = 4

_PR_SET_NO_NEW_PRIVS = 38


class _RulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64), ("handled_access_net", ctypes.c_uint64)]


class _PathBeneathAttr(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


@dataclass(frozen=True)
class LandlockOutcome:
    applied: bool
    abi_version: int | None
    network_blocked: bool
    detail: str


def landlock_abi_version() -> int | None:
    """The Landlock ABI version this kernel supports, or None if Landlock
    doesn't exist here at all (pre-5.13 kernel, or the syscalls are
    themselves denied by an outer sandboxing layer)."""
    ctypes.set_errno(0)
    ret = _syscall(_NR_LANDLOCK_CREATE_RULESET, None, 0, _LANDLOCK_CREATE_RULESET_VERSION)
    return ret if ret > 0 else None


def _add_path_rule(ruleset_fd: int, path: Path, allowed_access: int) -> bool:
    if not path.exists():
        return False
    parent_fd = os.open(path, os.O_PATH | os.O_DIRECTORY)
    try:
        rule = _PathBeneathAttr(allowed_access=allowed_access, parent_fd=parent_fd)
        ctypes.set_errno(0)
        ret = _syscall(_NR_LANDLOCK_ADD_RULE, ruleset_fd, _LANDLOCK_RULE_PATH_BENEATH, ctypes.byref(rule), 0)
        return ret == 0
    finally:
        os.close(parent_fd)


def restrict_current_process(*, writable_dirs: list[Path]) -> LandlockOutcome:
    """Confines the CALLING process (and everything it execve()s
    afterwards - the whole reason this is called from preexec_fn, between
    fork() and exec() of the actual candidate script) so that:
      - it can only create/write/remove files under one of `writable_dirs`
      - (kernel ABI >=4) it cannot open any outbound TCP connection

    This is a one-way ratchet by kernel design: once applied, there is no
    syscall that removes or loosens it for the remaining lifetime of this
    process or any descendant. Never raises - a failure at any step means
    "confinement not applied," reported honestly in the returned outcome,
    never a crash of the sandbox run itself.
    """
    abi = landlock_abi_version()
    if abi is None:
        return LandlockOutcome(False, None, False, "Landlock unsupported on this kernel (pre-5.13, or blocked)")

    want_net = abi >= _MIN_ABI_FOR_NET_RULES
    attr = _RulesetAttr(
        handled_access_fs=_HANDLED_ACCESS_FS,
        handled_access_net=_HANDLED_ACCESS_NET if want_net else 0,
    )
    ctypes.set_errno(0)
    ruleset_fd = _syscall(_NR_LANDLOCK_CREATE_RULESET, ctypes.byref(attr), ctypes.sizeof(attr), 0)
    if ruleset_fd < 0:
        return LandlockOutcome(False, abi, False, f"landlock_create_ruleset failed (errno {ctypes.get_errno()})")

    try:
        allow = _ACCESS_FS_WRITE_FILE | _ACCESS_FS_MAKE_REG | _ACCESS_FS_REMOVE_FILE | _ACCESS_FS_REMOVE_DIR
        any_rule_added = False
        for d in writable_dirs:
            if _add_path_rule(ruleset_fd, d, allow):
                any_rule_added = True
        if not any_rule_added:
            return LandlockOutcome(False, abi, False, "could not add any filesystem allow-rule")

        # PR_SET_NO_NEW_PRIVS is required before landlock_restrict_self
        # for an unprivileged caller - itself always safe/unprivileged.
        _libc.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)

        ctypes.set_errno(0)
        ret = _syscall(_NR_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)
        if ret != 0:
            return LandlockOutcome(False, abi, False, f"landlock_restrict_self failed (errno {ctypes.get_errno()})")
    finally:
        os.close(ruleset_fd)

    if want_net:
        detail = f"Landlock ABI {abi}: filesystem writes confined, outbound TCP connect() denied"
    else:
        detail = f"Landlock ABI {abi}: filesystem writes confined (network rules need ABI >=4, kernel has {abi})"
    return LandlockOutcome(True, abi, want_net, detail)
