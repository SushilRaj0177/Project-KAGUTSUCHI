"""
A real bug (report.py's dropped findings.extend(...) calls, see ROADMAP.md's
M2b entry) shipped past every test in this project because the symptom -
an import with nothing left using it after a merge-conflict resolution
silently dropped the one call site - is exactly what a static "unused
import" check catches for free. Every module's own unit tests passed the
whole time, since none of them exercise the wiring in report.py itself.

This doesn't replace test_report.py's own
test_analyze_snapshot_wiring_covers_every_implemented_characteristic (that
one proves the *behavior* - a Finding actually appears - which is the
real thing that matters, and is what actually caught that exact bug).
This test is the cheap, generic backstop: an import nobody uses anymore is
almost always a sign something was wired in, then silently unwired, which
is worth catching for any future module, not just report.py.

Skipped rather than failed when `pyflakes` isn't installed (`pip install
-e ".[lint]"`) - this is a hygiene check, not something the base install
should require.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys

import pytest

pyflakes_available = importlib.util.find_spec("pyflakes") is not None


@pytest.mark.skipif(not pyflakes_available, reason='pyflakes not installed - run `pip install -e ".[lint]"`')
def test_wsqfai_package_has_no_unused_imports_or_undefined_names():
    result = subprocess.run(
        [sys.executable, "-m", "pyflakes", "wsqfai"],
        capture_output=True,
        text=True,
    )
    assert result.stdout == "", f"pyflakes found issues:\n{result.stdout}"
