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


def build_script_from_source(module_source: str, function_name: str) -> str:
    """Same idea as build_runnable_script, but takes source TEXT directly
    instead of a live module object.

    This is the version the web backend uses for user-uploaded code: that
    code must never be imported or exec'd in the server process (only
    inside the Docker sandbox) — importing an untrusted module would run
    its top-level code outside any sandbox. Taking plain text sidesteps
    that entirely; nothing here ever executes the uploaded source."""
    return f"{module_source}\nimport sys\n{function_name}(sys.argv[1])\n"


def build_runnable_script(module: ModuleType, function_name: str) -> str:
    """Embed the WHOLE module (not just one function) so its module-level
    dependencies — imports, compiled regexes, constants — are present
    regardless of which function in it actually runs, then call
    `function_name(sys.argv[1])` so the sandbox's argv-based payload
    delivery (see system/sandbox/docker_runner.py) reaches it.

    Only for OUR OWN trusted fixture modules (already imported/trusted by
    virtue of being in this repo) — see build_script_from_source for
    untrusted, uploaded code."""
    return build_script_from_source(inspect.getsource(module), function_name)
