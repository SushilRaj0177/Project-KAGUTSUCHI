"""Splice a self-contained fixed function back into its original file.

verify_upload()'s propose_fix() only ever returns ONE function's full,
self-contained source (see verification/hypothesis/propose_fix.py's
docstring: "it will be run on its own, with nothing else from the
original file present") - it never touches the rest of the file, and
never sees the file's other functions, imports, or classes.

Turning a verified fix into a real commit means replacing just that one
function's lines in the ORIGINAL file text, not overwriting the whole
file with the isolated function (which would delete everything else in
it). This is what makes integration/github_pr.py's PR content correct
instead of destructive.
"""
from __future__ import annotations

import ast


class SymbolNotFound(ValueError):
    """Raised when `symbol` can't be located as a function in `original_source`."""


def apply_function_fix(original_source: str, symbol: str, fixed_function_source: str) -> str:
    """Replace the `def symbol(...)` (or `async def`) block in
    `original_source` with `fixed_function_source`, leaving every other
    line - including any decorators on the original function, which
    `fixed_function_source` never includes - untouched.
    """
    try:
        tree = ast.parse(original_source)
    except SyntaxError as exc:
        raise SymbolNotFound(f"original file is not valid Python: {exc}") from exc

    target: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            target = node
            break
    if target is None:
        raise SymbolNotFound(f"{symbol!r} is not defined as a function in the original file")

    lines = original_source.splitlines(keepends=True)
    start = target.lineno - 1  # ast linenos are 1-based; this is the `def` line itself
    end = target.end_lineno  # inclusive 1-based -> works directly as an exclusive slice end

    indent = len(lines[start]) - len(lines[start].lstrip(" "))
    fixed_lines = fixed_function_source.rstrip("\n").splitlines()
    reindented = "\n".join((f"{' ' * indent}{line}" if line.strip() else line) for line in fixed_lines) + "\n"

    return "".join(lines[:start]) + reindented + "".join(lines[end:])
