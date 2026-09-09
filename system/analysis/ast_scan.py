"""
AST-based structural analysis.

Parses Python source, walks each function body, and flags calls that match
a known sensitive-operation signature (shell exec, subprocess, filesystem,
SQL, deserialization, ...). Each match becomes a SecurityFinding — the
system/ side's only output, consumed by verification/hypothesis.

This is intentionally a signature match over the AST, not a taint/dataflow
analysis: P0 scope is proving ONE demonstrated vulnerability class end to
end, not building a general static analyzer.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

from contracts import SecurityFinding, SensitiveOp

# Qualified call name -> (SensitiveOp, rationale, detector id)
_SIGNATURES: dict[str, tuple[SensitiveOp, str, str]] = {
    "os.system": (
        SensitiveOp.SHELL_EXEC,
        "os.system runs its argument through the shell — string-built "
        "input here is a classic command injection sink.",
        "ast.shell_exec.os_system",
    ),
    "subprocess.run": (
        SensitiveOp.SUBPROCESS,
        "subprocess.run can invoke a shell (shell=True) or pass an "
        "attacker-influenced argv.",
        "ast.subprocess.run",
    ),
    "subprocess.Popen": (
        SensitiveOp.SUBPROCESS,
        "subprocess.Popen can invoke a shell (shell=True) or pass an "
        "attacker-influenced argv.",
        "ast.subprocess.popen",
    ),
    "subprocess.call": (
        SensitiveOp.SUBPROCESS,
        "subprocess.call can invoke a shell (shell=True) or pass an "
        "attacker-influenced argv.",
        "ast.subprocess.call",
    ),
    "eval": (
        SensitiveOp.DESERIALIZATION,
        "eval executes arbitrary Python from its argument.",
        "ast.eval",
    ),
    "exec": (
        SensitiveOp.DESERIALIZATION,
        "exec executes arbitrary Python from its argument.",
        "ast.exec",
    ),
    "pickle.loads": (
        SensitiveOp.DESERIALIZATION,
        "pickle.loads can execute arbitrary code during unpickling of "
        "untrusted data.",
        "ast.pickle.loads",
    ),
    "os.popen": (
        SensitiveOp.SHELL_EXEC,
        "os.popen runs its argument through the shell.",
        "ast.shell_exec.os_popen",
    ),
}


@dataclass
class _CallSite:
    function_name: str
    call_name: str
    lineno: int
    op: SensitiveOp | None = None
    rationale: str | None = None
    detector: str | None = None


def _is_string_built(node: ast.expr) -> bool:
    """True if `node` looks like a runtime-assembled string: an f-string,
    or string concatenation (`"..." + var`), rather than a plain literal."""
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return True
    return False


def _sql_call_hit(node: ast.Call) -> _CallSite | None:
    """Heuristic: cursor.execute(...)/.executescript(...) where the query
    argument is string-built, not a parameterized literal — the actual
    SQL-injection-relevant pattern, independent of the cursor's module."""
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in ("execute", "executescript"):
        return None
    if not node.args or not _is_string_built(node.args[0]):
        return None
    return _CallSite(
        function_name="",
        call_name=f"<obj>.{func.attr}",
        lineno=node.lineno,
        op=SensitiveOp.SQL_QUERY,
        rationale=(
            f".{func.attr} is called with a string built at runtime "
            "(f-string/concatenation) instead of a parameterized query — "
            "classic SQL injection sink."
        ),
        detector="ast.sql_injection.string_built_query",
    )


def _dotted_call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        cur: ast.expr = func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            return ".".join(reversed(parts))
    return None


def sensitive_ops_in_function(func_node: ast.FunctionDef) -> list[_CallSite]:
    hits: list[_CallSite] = []
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Call):
            continue
        name = _dotted_call_name(node)
        if name in _SIGNATURES:
            hits.append(_CallSite(func_node.name, name, node.lineno))
            continue
        sql_hit = _sql_call_hit(node)
        if sql_hit is not None:
            sql_hit.function_name = func_node.name
            hits.append(sql_hit)
    return hits


def _function_source(source_lines: list[str], func_node: ast.FunctionDef) -> str:
    end = getattr(func_node, "end_lineno", func_node.lineno)
    return "\n".join(source_lines[func_node.lineno - 1 : end])


def scan_source(source: str, file_path: str) -> list[SecurityFinding]:
    """Parse `source`, return one SecurityFinding per sensitive call site
    found inside any top-level or nested function definition."""
    tree = ast.parse(source, filename=file_path)
    source_lines = source.splitlines()
    findings: list[SecurityFinding] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for hit in sensitive_ops_in_function(node):  # type: ignore[arg-type]
                if hit.op is not None:
                    op, rationale, detector = hit.op, hit.rationale, hit.detector
                else:
                    op, rationale, detector = _SIGNATURES[hit.call_name]
                findings.append(
                    SecurityFinding(
                        file_path=file_path,
                        symbol=hit.function_name,
                        diff_hunk=_function_source(source_lines, node),
                        sensitive_op=op,
                        rationale=f"{rationale} (call: {hit.call_name}, line {hit.lineno})",
                        detected_by=detector,
                    )
                )
    return findings
