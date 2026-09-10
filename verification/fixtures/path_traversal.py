"""Fourth fixture: path traversal / arbitrary file write (`filesystem`
sensitive_op), to prove the pipeline generalizes to a class that isn't
"attacker input reaches an interpreter" (shell/SQL/pickle) but "attacker
input reaches a filesystem path" instead - a real, extremely common
class (CWE-22), often introduced by exactly this footgun.

`vulnerable()` builds a target path with `os.path.join(BASE_DIR,
filename)`, assuming `filename` is always a plain relative name. It
isn't: `os.path.join` silently DISCARDS the base directory whenever the
second argument is an absolute path (documented Python behavior, not a
bug in `os.path.join` itself - the bug is trusting attacker input as if
it could only ever be relative). So `filename="/tmp/kagutsuchi_pwned"`
writes directly to that path, completely outside the intended directory.

`fixed()` resolves the joined path with `os.path.realpath()` and rejects
anything that doesn't stay inside the base directory - closing both the
absolute-path override above and a relative `../../` traversal.

Same observable proof as the other three fixtures: the exploit's target
IS the marker path itself here (no extra mechanism needed to reach it -
the vulnerability's "damage" and "the marker file" are the same write),
so `regression/verify.py`'s existing `_marker_created()` check works
unmodified once again.
"""

from __future__ import annotations

import os

_BASE_DIR = "/tmp/kagutsuchi_safe_uploads"


def vulnerable(filename: str) -> int:
    """Path traversal: os.path.join() silently discards _BASE_DIR when
    `filename` is an absolute path, so attacker-controlled input can
    write anywhere on disk, not just inside the intended directory."""
    os.makedirs(_BASE_DIR, exist_ok=True)
    path = os.path.join(_BASE_DIR, filename)
    with open(path, "w") as f:
        f.write("uploaded content")
    return 0


def fixed(filename: str) -> int:
    """Safe: resolve the joined path and verify it's still inside
    _BASE_DIR before writing - rejects both an absolute-path override and
    a relative '../' traversal attempt."""
    os.makedirs(_BASE_DIR, exist_ok=True)
    base_real = os.path.realpath(_BASE_DIR)
    target_real = os.path.realpath(os.path.join(_BASE_DIR, filename))
    if os.path.commonpath([target_real, base_real]) != base_real:
        raise ValueError(f"invalid filename: {filename!r} (path traversal attempt)")
    with open(target_real, "w") as f:
        f.write("uploaded content")
    return 0
