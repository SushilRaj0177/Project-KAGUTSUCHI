"""Third P0 fixture: insecure deserialization via pickle.loads(), to prove
the pipeline generalizes across a third, structurally different
vulnerability class (`system/analysis`'s `deserialization` sensitive_op,
matched on `pickle.loads`/`eval`/`exec` - see `ast_scan.py`'s `_SIGNATURES`).

`vulnerable()` unpickles attacker-controlled, base64-decoded bytes.
Pickle's `__reduce__` protocol lets a crafted payload call ANY callable
with ANY arguments during unpickling - not "unexpected data", arbitrary
code execution. `fixed()` uses `json.loads()` instead: JSON has no
equivalent to `__reduce__`, so a crafted payload is inert data, at worst
a decode error, never a code path.

Same observable proof convention as the other two fixtures: the exploit
payload's `__reduce__` calls `eval(...)` to run
`os.system("touch /tmp/kagutsuchi_pwned")`, so `regression/verify.py`'s
existing `_marker_created()` check works unmodified here too - three
vulnerability classes, one comparator.
"""

from __future__ import annotations

import base64
import json
import pickle


def vulnerable(data: str) -> object:
    """Insecure deserialization: `pickle.loads()` on attacker-controlled
    bytes can execute arbitrary code via a crafted `__reduce__` method,
    not just produce unexpected data."""
    raw = base64.b64decode(data)
    return pickle.loads(raw)


def fixed(data: str) -> object:
    """Safe: `json.loads()` has no code-execution hook equivalent to
    pickle's `__reduce__` - a malicious payload is either rejected as
    invalid JSON or deserializes into inert plain data."""
    raw = base64.b64decode(data)
    return json.loads(raw)
