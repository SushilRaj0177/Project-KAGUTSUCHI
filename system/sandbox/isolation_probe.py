"""Diagnostic-only probe: does THIS process have the raw Linux privileges
a hand-rolled container runtime (namespaces + cgroups, no Docker daemon
involved) would need to actually isolate a sandboxed run?

This exists to answer one question honestly before any of that runtime
gets built: Render's standard web-service containers already can't do
Docker-in-Docker (see system/sandbox/docker_runner.py's fallback and
COORDINATION.md) - the open question is whether the SAME restriction
also blocks the lower-level primitives (unshare(2) into new namespaces,
cgroup v2 delegation, chroot) a bespoke runtime would use instead of
calling out to a Docker daemon. If Render blocks those too, for the
same reason it blocks Docker-in-Docker (a locked-down container with no
CAP_SYS_ADMIN and/or a seccomp policy denying `unshare`/`clone` with
namespace flags), building a bespoke runtime doesn't get us anywhere
Docker-in-Docker didn't already fail to get us - it needs to be proven
possible on the real target (Render) before real effort goes into it,
not assumed.

Every check here is read-only in effect: each spawns a short-lived
child process (so a failed/denied syscall can never corrupt this
process's own state) and cleans up anything it creates (a scratch
cgroup directory, a scratch chroot directory). Safe to call from a live
request.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
import shutil
import tempfile
from dataclasses import dataclass, field

_CLONE_NEWUSER = 0x10000000
_CLONE_NEWNET = 0x40000000
_CLONE_NEWNS = 0x00020000
_CLONE_NEWPID = 0x20000000

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    required: bool = True  # False = informational only, doesn't gate the verdict


@dataclass
class ProbeReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        required = [c for c in self.checks if c.required]
        return bool(required) and all(c.ok for c in required)

    def as_dict(self) -> dict:
        return {
            "all_ok": self.all_ok,
            "checks": [
                {"name": c.name, "ok": c.ok, "detail": c.detail, "required": c.required} for c in self.checks
            ],
            "verdict": (
                "This process can build its own isolated namespaces/cgroups - a bespoke "
                "runtime is technically viable here."
                if self.all_ok
                else "At least one required primitive is unavailable - a bespoke runtime "
                "would NOT get real isolation here, for the same underlying reason "
                "Docker-in-Docker doesn't work here."
            ),
        }


def _try_unshare_in_child(flags: int) -> tuple[bool, str]:
    """Forks so a denied/failed unshare(2) can never affect this process -
    the child either succeeds and exits 0, or fails and exits 1/2, and
    the parent just reads that exit code."""
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            ret = _libc.unshare(flags)
            if ret == 0:
                os._exit(0)
            err = ctypes.get_errno()
            os.write(write_fd, os.strerror(err).encode())
            os._exit(1)
        except Exception as exc:  # noqa: BLE001 - must never let the child escape abnormally
            try:
                os.write(write_fd, str(exc).encode())
            except OSError:
                pass
            os._exit(2)
    os.close(write_fd)
    _, status = os.waitpid(pid, 0)
    message = os.read(read_fd, 256).decode(errors="replace")
    os.close(read_fd)
    ok = os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    return ok, ("" if ok else (message or f"exited {os.WEXITSTATUS(status) if os.WIFEXITED(status) else status}"))


def _check_user_namespace() -> CheckResult:
    ok, detail = _try_unshare_in_child(_CLONE_NEWUSER)
    return CheckResult("user_namespace (CLONE_NEWUSER)", ok, detail or "unshare(CLONE_NEWUSER) succeeded")


def _check_network_namespace() -> CheckResult:
    ok, detail = _try_unshare_in_child(_CLONE_NEWNET)
    return CheckResult("network_namespace (CLONE_NEWNET)", ok, detail or "unshare(CLONE_NEWNET) succeeded")


def _check_mount_namespace() -> CheckResult:
    ok, detail = _try_unshare_in_child(_CLONE_NEWNS)
    return CheckResult("mount_namespace (CLONE_NEWNS)", ok, detail or "unshare(CLONE_NEWNS) succeeded")


def _check_pid_namespace() -> CheckResult:
    ok, detail = _try_unshare_in_child(_CLONE_NEWPID)
    return CheckResult("pid_namespace (CLONE_NEWPID)", ok, detail or "unshare(CLONE_NEWPID) succeeded")


def _check_unprivileged_userns_sysctl() -> CheckResult:
    """Some distros allow the unshare(2) syscall itself but gate it
    behind this sysctl (0 = kernel-level deny regardless of
    capabilities) - worth reporting separately since it explains an
    otherwise-confusing CLONE_NEWUSER failure."""
    path = "/proc/sys/kernel/unprivileged_userns_clone"
    if not os.path.exists(path):
        return CheckResult(
            "unprivileged_userns_clone sysctl (informational)",
            True,
            "sysctl doesn't exist on this kernel - nothing gating it here",
            required=False,
        )
    try:
        value = open(path).read().strip()
    except OSError as exc:
        return CheckResult("unprivileged_userns_clone sysctl (informational)", False, f"couldn't read: {exc}", required=False)
    return CheckResult(
        "unprivileged_userns_clone sysctl (informational)",
        value == "1",
        f"value={value!r} (needs '1' to allow unprivileged userns)",
        required=False,
    )


def _check_cgroup_v2_delegation() -> CheckResult:
    """Creating a real, resource-limited container needs write access to
    a cgroup v2 subtree (to cap memory/CPU for the sandboxed process) -
    a locked-down PaaS container commonly mounts /sys/fs/cgroup
    read-only or doesn't delegate a writable subtree at all."""
    root = "/sys/fs/cgroup"
    if not os.path.isdir(root):
        return CheckResult("cgroup_v2_delegation", False, f"{root} doesn't exist (no cgroup v2 mount)")
    if not os.path.exists(os.path.join(root, "cgroup.controllers")):
        return CheckResult("cgroup_v2_delegation", False, f"{root} exists but isn't cgroup v2 (no cgroup.controllers)")

    scratch = os.path.join(root, "kagutsuchi-probe-scratch")
    try:
        os.mkdir(scratch)
    except OSError as exc:
        return CheckResult("cgroup_v2_delegation", False, f"can't create a subtree under {root}: {exc}")
    try:
        with open(os.path.join(scratch, "memory.max"), "w") as f:
            f.write("100000000")
        return CheckResult("cgroup_v2_delegation", True, f"created + wrote memory.max under {scratch}")
    except OSError as exc:
        return CheckResult("cgroup_v2_delegation", False, f"subtree created but not writable: {exc}")
    finally:
        try:
            os.rmdir(scratch)
        except OSError:
            pass  # best-effort cleanup; a stray empty dir here is harmless


def _check_cgroup_v1_delegation() -> CheckResult:
    """Fallback for a host still on the legacy cgroup v1 hierarchy
    (common - e.g. this very sandbox is v1, not v2). Only meaningful if
    the v2 check above failed; a v1-capable host is still enough to cap
    memory/CPU for a bespoke runtime, just with the older API."""
    memdir = "/sys/fs/cgroup/memory"
    if not os.path.isdir(memdir):
        return CheckResult("cgroup_v1_delegation (fallback)", False, f"{memdir} doesn't exist (no cgroup v1 memory controller)")

    scratch = os.path.join(memdir, "kagutsuchi-probe-scratch")
    try:
        os.mkdir(scratch)
    except OSError as exc:
        return CheckResult("cgroup_v1_delegation (fallback)", False, f"can't create a subtree under {memdir}: {exc}")
    try:
        with open(os.path.join(scratch, "memory.limit_in_bytes"), "w") as f:
            f.write("100000000")
        return CheckResult("cgroup_v1_delegation (fallback)", True, f"created + wrote memory.limit_in_bytes under {scratch}")
    except OSError as exc:
        return CheckResult("cgroup_v1_delegation (fallback)", False, f"subtree created but not writable: {exc}")
    finally:
        try:
            os.rmdir(scratch)
        except OSError:
            pass


def _check_chroot() -> CheckResult:
    """Filesystem isolation via chroot/pivot_root needs CAP_SYS_CHROOT -
    checked in a forked child, same reasoning as the unshare checks."""
    scratch = tempfile.mkdtemp(prefix="kagutsuchi-chroot-probe-")
    try:
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            try:
                os.chroot(scratch)
                os._exit(0)
            except OSError as exc:
                os.write(write_fd, str(exc).encode())
                os._exit(1)
            except Exception as exc:  # noqa: BLE001
                os.write(write_fd, str(exc).encode())
                os._exit(2)
        os.close(write_fd)
        _, status = os.waitpid(pid, 0)
        message = os.read(read_fd, 256).decode(errors="replace")
        os.close(read_fd)
        ok = os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
        return CheckResult("chroot (CAP_SYS_CHROOT)", ok, message or "chroot() succeeded")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def run_isolation_probe() -> ProbeReport:
    report = ProbeReport()
    for check_fn in (
        _check_user_namespace,
        _check_unprivileged_userns_sysctl,
        _check_network_namespace,
        _check_mount_namespace,
        _check_pid_namespace,
        _check_cgroup_v2_delegation,
        _check_cgroup_v1_delegation,
        _check_chroot,
    ):
        try:
            report.checks.append(check_fn())
        except Exception as exc:  # noqa: BLE001 - a probe crashing is itself informative, not fatal
            report.checks.append(CheckResult(check_fn.__name__, False, f"probe itself raised: {exc!r}"))

    # Only ONE cgroup hierarchy needs to work (v2 preferred, v1 as a
    # fallback) - neither individual check should gate the verdict on
    # its own, only their combination.
    v2 = next(c for c in report.checks if c.name == "cgroup_v2_delegation")
    v1 = next(c for c in report.checks if c.name == "cgroup_v1_delegation (fallback)")
    v2.required = False
    v1.required = False
    report.checks.append(
        CheckResult(
            "cgroup_delegation (v2 or v1)",
            ok=v2.ok or v1.ok,
            detail=f"v2={'OK' if v2.ok else 'failed'}, v1={'OK' if v1.ok else 'failed'}",
        )
    )
    return report
