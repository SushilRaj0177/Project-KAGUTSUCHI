"""Fifth fixture: tar-extraction path traversal (`filesystem` sensitive_op)
- CVE-2007-4559-class, a genuinely famous Python stdlib footgun that went
unpatched-by-default for roughly 15 years: `tarfile.extractall()` does
not validate member paths unless the caller explicitly passes a `filter`
(Python 3.12+ ships a safe default; every earlier version, and any 3.12+
code that doesn't opt in, extracts a member's path exactly as the archive
says to, including `../` traversal and, on some platforms, absolute
paths).

`vulnerable()` builds a one-entry in-memory tar archive whose member name
is the attacker-controlled input, then extracts it into a "safe"
directory with no filter - a member name containing `../` escapes that
directory entirely, onto the filesystem the extracting process can reach.

`fixed()` resolves each member's target path before extracting it and
rejects anything that would land outside the safe directory - the same
technique Python 3.12's built-in `filter="data"` and the original
CVE-2007-4559 advisories both recommend.

Same observable proof as `path_traversal.py`: the exploit's target IS the
marker path (no extra mechanism needed), so `regression/verify.py`'s
`_marker_created()` check works unmodified - five vulnerability classes,
one comparator.
"""

from __future__ import annotations

import io
import os
import tarfile

_SAFE_DIR = "/tmp/kagutsuchi_safe_extract"


def _make_tar_bytes(member_name: str, content: bytes = b"payload") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def vulnerable(member_name: str) -> int:
    """Path traversal via tarfile.extractall(): a member name containing
    '../' is extracted exactly as named, escaping the intended directory,
    since no filter is passed (CVE-2007-4559's exact shape)."""
    os.makedirs(_SAFE_DIR, exist_ok=True)
    raw = _make_tar_bytes(member_name)
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        tar.extractall(path=_SAFE_DIR)  # noqa: S202 - the vulnerability under test
    return 0


def fixed(member_name: str) -> int:
    """Safe: resolve each member's target path before extracting it and
    reject anything that doesn't stay inside the safe directory."""
    os.makedirs(_SAFE_DIR, exist_ok=True)
    raw = _make_tar_bytes(member_name)
    safe_dir_real = os.path.realpath(_SAFE_DIR)
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for member in tar.getmembers():
            target = os.path.realpath(os.path.join(_SAFE_DIR, member.name))
            if os.path.commonpath([target, safe_dir_real]) != safe_dir_real:
                raise ValueError(
                    f"unsafe tar member path: {member.name!r} (extraction traversal attempt)"
                )
        tar.extractall(path=_SAFE_DIR)
    return 0
