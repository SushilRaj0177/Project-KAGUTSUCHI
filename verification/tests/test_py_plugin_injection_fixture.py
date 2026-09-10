"""Unit tests for the sixth (Python plugin injection) fixture: the
byte-identical payload must exploit vulnerable() and be inert against
fixed() - same shape as the other five fixture test suites. This class
was AI-discovered (system/analysis/llm_scan.py's new_class_proposal),
not hand-picked - see COORDINATION.md and the fixture module docstring.
"""

from __future__ import annotations

import os
import sys

import pytest

from verification.attacks.run_local import MARKER_PATH, run_local_attack
from verification.fixtures.py_plugin_injection import _PLUGIN_DIR, fixed, vulnerable
from verification.hypothesis.py_plugin_injection_fallback import (
    PY_PLUGIN_INJECTION_FALLBACK_HYPOTHESIS,
)
from verification.models import ExecutionPhase

PAYLOAD = PY_PLUGIN_INJECTION_FALLBACK_HYPOTHESIS.payload

# Reliably writing to the literal "/tmp/..." path is a POSIX filesystem
# assumption - same reason the other fixtures' exploit-side tests are
# POSIX-only (this fixture targets the same Linux Docker sandbox).
posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="marker path targets a POSIX filesystem, see comment above"
)


@posix_only
def test_vulnerable_executes_the_imported_plugin():
    evidence = run_local_attack(vulnerable, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.BEFORE)
    assert evidence.filesystem_diff["created"] == [MARKER_PATH.as_posix()]


def test_fixed_never_imports_the_content():
    # Runs cross-platform: fixed() is pure Python file I/O, no shell/import.
    evidence = run_local_attack(fixed, PAYLOAD, "hyp-1", "run-1", ExecutionPhase.AFTER)
    assert evidence.filesystem_diff["created"] == []
    assert evidence.exit_code == 0


def test_fixed_stores_content_as_inert_text():
    fixed("print('this looks like code but is never executed')")
    expected_path = os.path.join(_PLUGIN_DIR, "latest_plugin.txt")
    assert os.path.exists(expected_path)
    with open(expected_path) as f:
        assert "print(" in f.read()
    os.remove(expected_path)
