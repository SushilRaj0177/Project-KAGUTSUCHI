"""
M2b (Performance Efficiency slice): real detection of quadratic string
accumulation inside a loop - ISO/IEC 25010's Time Behaviour sub-characteristic
("degree to which response/processing times and throughput meet
requirements").

`result = result + chunk` (or `result += chunk`) executed once per loop
iteration is a well-established Python anti-pattern, not invented for this
project: because `str` is immutable, each iteration allocates an entirely
new string and copies the old contents into it, making the total work
across N iterations O(N^2) instead of O(N). The Python documentation's own
performance tips and long-standing community guidance (e.g. the
`"".join(...)` idiom) exist specifically because of this; `perflint`
(a real, published static analyzer for exactly this class of issue) flags
the same shape.

Detection uses Python's own `ast` module rather than regex/text matching,
for the same correctness reason `reliability.py` does: matching "+="
as text would misfire inside strings, comments, and docstrings.

Deliberately narrow, to keep the false-positive rate low: only flagged
when the accumulator is reassigned via `x = x + <expr>` or `x += <expr>`
directly inside the body of a `for`/`while` loop (at any nesting depth
within it), AND there is strong static evidence the value being built is a
string - the right-hand side contains an f-string, a string literal, or a
call to `str(...)`. A loop accumulating a running numeric total
(`total += price`) is common and correct, so this only fires when the
evidence points at string-building specifically, not at augmented
assignment in a loop in general.
"""
from __future__ import annotations

import ast

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import RepositorySnapshot

_ANALYZER = "wsqfai.measurement.performance"
_LOOP_TYPES = (ast.For, ast.AsyncFor, ast.While)


def _looks_like_string_build(node: ast.expr) -> bool:
    """True if `node` gives strong static evidence of producing a string:
    an f-string, a string literal, or a str(...) call - anywhere in the
    expression, not just at the top level, since e.g. `x + (a + f"{b}")`
    still ends up concatenating a string."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.JoinedStr):
            return True
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            return True
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == "str":
            return True
    return False


def _accumulator_name(stmt: ast.stmt) -> tuple[str, ast.expr] | None:
    """If `stmt` is `x = x + <expr>` or `x += <expr>`, return (x, the
    right-hand expression whose string-ness we should check) - else None."""
    if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add) and isinstance(stmt.target, ast.Name):
        return stmt.target.id, stmt.value
    if (
        isinstance(stmt, ast.Assign)
        and len(stmt.targets) == 1
        and isinstance(stmt.targets[0], ast.Name)
        and isinstance(stmt.value, ast.BinOp)
        and isinstance(stmt.value.op, ast.Add)
    ):
        target_name = stmt.targets[0].id
        left, right = stmt.value.left, stmt.value.right
        if isinstance(left, ast.Name) and left.id == target_name:
            return target_name, stmt.value
        if isinstance(right, ast.Name) and right.id == target_name:
            return target_name, stmt.value
    return None


def _quadratic_string_build_lines(tree: ast.Module) -> list[int]:
    """Line numbers of every accumulator statement found anywhere inside a
    loop body (at any nesting depth) that builds a string. A single
    top-down walk that tracks "are we currently inside a loop", rather than
    a separate walk per loop node, so a statement inside a nested loop is
    counted exactly once."""
    lines: list[int] = []

    def visit(node: ast.AST, in_loop: bool) -> None:
        for child in ast.iter_child_nodes(node):
            child_in_loop = in_loop or isinstance(child, _LOOP_TYPES)
            if in_loop:
                hit = _accumulator_name(child)
                if hit is not None and _looks_like_string_build(hit[1]):
                    lines.append(child.lineno)
            visit(child, child_in_loop)

    visit(tree, False)
    return sorted(set(lines))


def _time_behaviour_finding(path: str, lines: list[int]) -> Finding:
    first = lines[0]
    return Finding(
        title=f"Quadratic string concatenation in a loop in {path}",
        description=(
            f"{len(lines)} loop iteration(s) build a string via '+'/'+=' (first at line {first}) "
            "instead of collecting pieces and joining once. Because Python strings are immutable, "
            "each iteration allocates a new string and copies the old contents into it - O(n) work "
            "per iteration, O(n^2) total across the loop. Prefer accumulating into a list and calling "
            "''.join(...) once after the loop. ISO/IEC 25010's Time Behaviour sub-characteristic: "
            "the degree to which response/processing times and throughput meet requirements."
        ),
        characteristic=QualityCharacteristic.PERFORMANCE_EFFICIENCY,
        sub_characteristic_key="time_behaviour",
        severity=Severity.MEDIUM,
        evidence=[Evidence(
            location=SourceLocation(file_path=path, start_line=first, end_line=first),
            snippet=f"{len(lines)} quadratic string-concatenation site(s) in a loop, first at line {first}",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="quadratic_string_concat_in_loop", confidence=Confidence.MEDIUM),
        )],
    )


def compute_performance_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    """Run every Performance Efficiency metric this module implements
    against every Python file in the snapshot that has retained content
    and parses as valid Python. Files that fail to parse are skipped
    rather than raising - same discipline as reliability.py."""
    findings: list[Finding] = []
    for f in snapshot.files:
        if f.language != "Python" or not f.content:
            continue
        try:
            tree = ast.parse(f.content)
        except (SyntaxError, ValueError):
            continue
        lines = _quadratic_string_build_lines(tree)
        if lines:
            findings.append(_time_behaviour_finding(f.path, lines))
    return findings
