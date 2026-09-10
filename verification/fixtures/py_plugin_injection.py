"""Sixth fixture: writing attacker-controlled content to a `.py` file that
is then imported and executed (`deserialization` sensitive_op - same
"arbitrary code execution from untrusted data" bucket as pickle/eval).

AI-discovered, not hand-picked in advance: `system/analysis/llm_scan.py`'s
`new_class_proposal` mechanism flagged this exact pattern
(`write_user_controlled_python_file`) as HIGH severity, independently
spotted in `adeyosemanputra/pygoat` - see the `/detector-proposals` page
and COORDINATION.md's "AI scanner now proposes new deterministic detector
classes" entry. This fixture hand-verifies that AI-flagged class the same
way every other fixture here does, rather than trusting the proposal.

`vulnerable()` writes attacker-controlled `code` verbatim to a fixed
"plugin" path, then loads it with `importlib` - a realistic "drop a
plugin file, load it" pattern real plugin systems use. The imported
module's top-level code runs with full interpreter privileges the moment
it loads, so controlling `code` is immediate arbitrary code execution,
not just an oddly-named file sitting on disk.

`fixed()` writes the exact same content, but to a `.txt` file instead of
`.py`, and never imports anything - the payload is stored as inert text,
never executed. (A more complete real-world fix would also validate/
sandbox legitimate plugins; this fixture isolates the one load-bearing
decision - do we ever exec attacker-supplied file contents - the same
way every other fixture here isolates one decision rather than modeling
a whole subsystem.)
"""

from __future__ import annotations

import importlib.util
import os

_PLUGIN_DIR = "/tmp/kagutsuchi_plugins"


def vulnerable(code: str) -> int:
    """Writes `code` to a .py file and imports it - arbitrary code
    execution the moment the "plugin" loads."""
    os.makedirs(_PLUGIN_DIR, exist_ok=True)
    path = os.path.join(_PLUGIN_DIR, "latest_plugin.py")
    with open(path, "w") as f:
        f.write(code)
    spec = importlib.util.spec_from_file_location("kagutsuchi_plugin", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # noqa: S -- the vulnerability under test
    return 0


def fixed(code: str) -> int:
    """Safe: the same content is written as plain text, never as a .py
    file, and never imported - inert data, no execution path."""
    os.makedirs(_PLUGIN_DIR, exist_ok=True)
    path = os.path.join(_PLUGIN_DIR, "latest_plugin.txt")
    with open(path, "w") as f:
        f.write(code)
    return 0
