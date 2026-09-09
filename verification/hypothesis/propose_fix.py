"""Automatic fix proposal for arbitrary uploaded code (the real-product
path, not the 3-fixture demo - see COORDINATION.md's "Scope change:
building the real 'upload code, get analyzed and fixed' product" entry).

Unlike attack-hypothesis generation, there is no hardcoded fallback
possible here: we don't know what arbitrary uploaded code looks like
ahead of time, so there's nothing sensible to fall back to. On any Groq
failure, this raises GroqUnavailable (from groq_client) rather than
guessing - the caller should surface "couldn't generate a fix right now"
to the user, not a silently wrong answer.

Whatever this returns is NOT trusted just because it came back well-
formed. It gets run through the exact same build_runnable_script() +
sandbox + regression/verify.py as every hand-written fixture. If the
proposed fix doesn't actually close the vulnerability, the verdict comes
back STILL_VULNERABLE - the sandbox proving it, not this module claiming
it, is what makes trusting an LLM-generated fix safe to ship.
"""

from __future__ import annotations

import ast
import builtins as _builtins_module

from verification.hypothesis.groq_client import generate_hypothesis_json
from verification.models import AttackHypothesis, SecurityFinding

_PROMPT_TEMPLATE = """You are a security engineer fixing a real vulnerability in the \
Python function below. Rewrite ONLY this function so the vulnerability is \
eliminated, while preserving its exact name and its signature (it must \
still take exactly one string parameter - the same parameter it takes now).

sensitive_op: {sensitive_op}
function name: {symbol}
original vulnerable source:
{diff_hunk}

A real attack against this function: {attack_vector}
Concrete payload that exploits it: {payload}
What must be true once it's fixed: {expected_if_safe}

Rewrite the function so that exact payload, and anything like it, no \
longer works - without changing what the function is for or its \
signature. Do not add extra parameters, don't rename it, don't wrap it \
in a class.

CRITICAL - the function must be fully self-contained: it will be run on \
its own, with nothing else from the original file present. Put any \
`import` statements it needs INSIDE the function body itself (not at the \
top of a module that won't exist). Do not call any helper function, or \
reference any variable/constant, that isn't a builtin, a parameter, or \
something you define inside this function - if the original code relied \
on a module-level helper or constant, inline an equivalent directly into \
this function instead of calling out to it.

Respond with a single JSON object with exactly one key, "fixed_source", \
whose value is the complete rewritten function's full source code as a \
plain string (including its `def` line and docstring/comments if any) - \
not a diff, not an explanation, just the function.
"""


class FixValidationError(Exception):
    """Raised when a proposed fix fails basic sanity checks (invalid
    syntax, or doesn't define a function with the expected name/
    signature) before it's ever handed to the sandbox."""


def _build_prompt(finding: SecurityFinding, hypothesis: AttackHypothesis) -> str:
    return _PROMPT_TEMPLATE.format(
        sensitive_op=finding.sensitive_op.value,
        symbol=finding.symbol,
        diff_hunk=finding.diff_hunk,
        attack_vector=hypothesis.attack_vector,
        payload=hypothesis.payload,
        expected_if_safe=hypothesis.expected_if_safe,
    )


def _validate(source: str, expected_function_name: str) -> None:
    """Cheap, fast sanity checks before this ever reaches build_runnable_script
    or the sandbox - not a substitute for the sandbox actually running it."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise FixValidationError(f"proposed fix is not valid Python: {exc}") from exc

    # Must be a plain `def`, not `async def`: build_runnable_script() calls
    # `function_name(sys.argv[1])` with no `await`, so an async function
    # would just create an un-awaited coroutine and silently never run -
    # no exception, no exploit, no evidence, a misleading verdict.
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == expected_function_name
    ]
    if not functions:
        async_functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == expected_function_name
        ]
        if async_functions:
            raise FixValidationError(
                f"{expected_function_name}() must be a plain function, not async - "
                "build_runnable_script() calls it without awaiting"
            )
        raise FixValidationError(
            f"proposed fix does not define a function named {expected_function_name!r}"
        )

    args = functions[0].args
    positional = args.posonlyargs + args.args
    if len(positional) != 1:
        raise FixValidationError(
            f"{expected_function_name}() must take exactly one parameter, "
            f"got {len(positional)}"
        )

    free_names = _free_names(functions[0])
    if free_names:
        raise FixValidationError(
            f"{expected_function_name}() is not self-contained - it references "
            f"{sorted(free_names)}, which aren't builtins, parameters, or "
            f"defined/imported inside the function itself. It will be run "
            f"standalone with nothing else from the original file present "
            f"(see propose_fix()'s prompt requirement), so this would raise "
            f"NameError instead of actually running - and a crash on every "
            f"call would look like 'fixed' to the sandbox (no exploit ever "
            f"fires) instead of a broken fix."
        )


def _free_names(func_node: ast.FunctionDef) -> set[str]:
    """Best-effort static check for names the function reads but never
    defines, imports (within itself), or receives as a parameter - a
    strong signal it depends on module-level context (a helper function,
    an import, a constant) that won't exist when it's run on its own.
    Not a full scope/closure analysis, just enough to catch the common
    real case of "calls a sibling function from the original file" or
    "uses a name that needed a module-level import".
    """
    bound: set[str] = {func_node.name}

    def _add_arglist(a: ast.arguments) -> None:
        for arg in a.posonlyargs + a.args + a.kwonlyargs:
            bound.add(arg.arg)
        if a.vararg:
            bound.add(a.vararg.arg)
        if a.kwarg:
            bound.add(a.kwarg.arg)

    _add_arglist(func_node.args)

    loaded: set[str] = set()
    for node in ast.walk(func_node):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                bound.add(node.id)
            elif isinstance(node.ctx, ast.Load):
                loaded.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node is not func_node:
                bound.add(node.name)
            _add_arglist(node.args)
        elif isinstance(node, ast.Lambda):
            _add_arglist(node.args)
        elif isinstance(node, ast.ClassDef):
            bound.add(node.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)

    return loaded - bound - set(dir(_builtins_module))


def propose_fix(finding: SecurityFinding, hypothesis: AttackHypothesis) -> str:
    """Ask the LLM to rewrite `finding`'s vulnerable function so that
    `hypothesis`'s attack no longer works, validate the result is at
    least syntactically plausible, and return its full source.

    Raises GroqUnavailable if the LLM call itself fails, or
    FixValidationError if it returns something that isn't usable
    (invalid syntax, wrong function name, wrong signature). Neither is
    swallowed - there is no fallback fix to degrade to.
    """
    raw = generate_hypothesis_json(_build_prompt(finding, hypothesis))
    try:
        fixed_source = raw["fixed_source"]
    except (KeyError, TypeError) as exc:
        raise FixValidationError(
            f"expected a JSON object with a 'fixed_source' string key, got: {raw!r}"
        ) from exc
    if not isinstance(fixed_source, str):
        raise FixValidationError(f"'fixed_source' must be a string, got {type(fixed_source).__name__}")

    _validate(fixed_source, finding.symbol)
    return fixed_source
