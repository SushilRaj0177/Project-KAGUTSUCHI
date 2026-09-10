"""
Generic harness builder: turns an arbitrary Python module + one of its
function names into a standalone script the sandbox can execute.

This is what makes the pipeline NOT a single hardcoded demo trick. Any
vulnerability class where the flagged sensitive operation lives in a
plain function (not a bound method) can be run through this same
harness, with no per-class special-casing here. That's still a real,
load-bearing limitation to be upfront about — it doesn't handle a
function that depends on live app state (a DB connection, a request
object, etc.), or one needing `self` — but it now covers functions
taking ANY number of positional arguments, not just exactly one string
(see system/orchestration/signature.py for how the caller determines
`arg_count`; verification/hypothesis/generate.py's prompt is what makes
the payload for arg_count > 1 a JSON-array-of-arguments string instead
of a plain string).

`arg_count` defaults to 1 everywhere below, which reproduces the exact
`function_name(sys.argv[1])` call this harness has always emitted — so
every existing caller that doesn't pass it is untouched.
"""
from __future__ import annotations

import inspect
from types import ModuleType


def build_script_from_source(module_source: str, function_name: str, arg_count: int = 1) -> str:
    """Same idea as build_runnable_script, but takes source TEXT directly
    instead of a live module object.

    This is the version the web backend uses for user-uploaded code: that
    code must never be imported or exec'd in the server process (only
    inside the Docker sandbox) — importing an untrusted module would run
    its top-level code outside any sandbox. Taking plain text sidesteps
    that entirely; nothing here ever executes the uploaded source.

    When `arg_count` > 1, the payload delivered via sys.argv[1] (see
    system/sandbox/docker_runner.py) is expected to be a JSON-encoded
    array of exactly `arg_count` values, which gets unpacked positionally
    into the call — the attack/fix prompts are told this explicitly so
    they produce a payload in that shape."""
    if arg_count == 1:
        return f"{module_source}\nimport sys\n{function_name}(sys.argv[1])\n"
    return (
        f"{module_source}\n"
        f"import json\nimport sys\n"
        f"__kagutsuchi_args__ = json.loads(sys.argv[1])\n"
        f"{function_name}(*__kagutsuchi_args__)\n"
    )


def build_runnable_script(module: ModuleType, function_name: str, arg_count: int = 1) -> str:
    """Embed the WHOLE module (not just one function) so its module-level
    dependencies — imports, compiled regexes, constants — are present
    regardless of which function in it actually runs, then call
    `function_name` with `arg_count` positional argument(s) so the
    sandbox's argv-based payload delivery (see system/sandbox/docker_runner.py)
    reaches it.

    Only for OUR OWN trusted fixture modules (already imported/trusted by
    virtue of being in this repo) — see build_script_from_source for
    untrusted, uploaded code."""
    return build_script_from_source(inspect.getsource(module), function_name, arg_count)
