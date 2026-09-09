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
        if isinstance(node, ast.Call):
            name = _dotted_call_name(node)
            if name in _SIGNATURES:
                hits.append(_CallSite(func_node.name, name, node.lineno))
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
