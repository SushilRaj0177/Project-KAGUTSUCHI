"""Introspect a target function's parameter count from source, so the
harness and attack/fix prompts can adapt to real-world functions instead
of assuming every one of them takes exactly one string argument.

That single-argument assumption was true of all five hand-built fixtures
but broke live on a real repo (PyGoat's log_code()/api_code() each take
two parameters) - see COORDINATION.md. This module is the first half of
the fix: knowing how many arguments a function actually needs. The
harness (build_script_from_source) and the attack/fix prompts
(verification/hypothesis/generate.py, propose_fix.py) are the other half.
"""
from __future__ import annotations

import ast


class UnsupportedSignature(ValueError):
    """Raised when a function's signature can't be safely driven by the
    sandbox harness: a bound method needing a real `self`/`cls` instance
    the sandbox has no safe way to construct, `*args`/`**kwargs` (no
    fixed arity to generate values for), or required keyword-only
    parameters (the harness only ever calls positionally)."""


def param_count(source: str, function_name: str) -> int:
    """Returns how many positional arguments `function_name` requires,
    by parsing `source` and finding its (first, top-level-or-nested)
    definition. Raises UnsupportedSignature for a shape the harness
    can't drive; raises ValueError (from ast.parse) if `source` itself
    isn't valid Python."""
    tree = ast.parse(source)

    target: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            target = node
            break
    if target is None:
        raise UnsupportedSignature(f"{function_name!r} is not defined as a function in this source")

    args = target.args
    positional = args.posonlyargs + args.args

    if positional and positional[0].arg in ("self", "cls"):
        raise UnsupportedSignature(
            f"{function_name}() appears to be a bound method (first parameter "
            f"{positional[0].arg!r}) — the sandbox has no safe way to construct "
            f"a real instance to call it on."
        )
    if args.vararg or args.kwarg:
        raise UnsupportedSignature(f"{function_name}() takes *args/**kwargs — not supported yet.")
    required_kwonly = [a.arg for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is None]
    if required_kwonly:
        raise UnsupportedSignature(
            f"{function_name}() has required keyword-only parameter(s) {required_kwonly!r} "
            f"— the harness only calls positionally, not supported yet."
        )
    if not positional:
        raise UnsupportedSignature(f"{function_name}() takes no parameters to attack.")

    return len(positional)
