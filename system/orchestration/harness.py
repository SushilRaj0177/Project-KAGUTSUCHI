"""
Generic harness builder: turns an arbitrary Python module + one of its
function names into a standalone script the sandbox can execute.

This is what makes the pipeline NOT a single hardcoded demo trick. Any
vulnerability class where the flagged sensitive operation lives in a
function taking one string argument (the attacker-controlled input) can
be run through this same harness, with no per-class special-casing here.
That's a real, load-bearing limitation to be upfront about — it doesn't
handle a function that depends on live app state (a DB connection, a
request object, etc.) — but it covers a meaningful slice of real
injection-shaped vulnerabilities, not just one fixture.
"""
from __future__ import annotations

import inspect
from types import ModuleType


def build_runnable_script(module: ModuleType, function_name: str) -> str:
    """Embed the WHOLE module (not just one function) so its module-level
    dependencies — imports, compiled regexes, constants — are present
    regardless of which function in it actually runs, then call
    `function_name(sys.argv[1])` so the sandbox's argv-based payload
    delivery (see system/sandbox/docker_runner.py) reaches it."""
    module_source = inspect.getsource(module)
    return f"{module_source}\nimport sys\n{function_name}(sys.argv[1])\n"
