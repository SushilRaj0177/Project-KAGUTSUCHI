"""
M2b: the first content-based SQuaRE characteristic beyond Maintainability
- Reliability's Fault Tolerance sub-characteristic ("degree to which a
system operates as intended despite hardware or software faults").

Unlike M2a's Maintainability slice, these metrics need to actually read
and parse source, which is why they waited on the content-retention
extension to `wsqfai/ingestion/repository.py` built for M3a. Detection
uses Python's own `ast` module rather than regex/text matching, since
matching "except" as text would misfire inside strings, comments, and
docstrings - a real correctness requirement, not a style preference.

Two patterns, both long-established in static-analysis tooling (e.g.
pylint's W0702 bare-except and broad-except checks) rather than invented
here:

  - A bare `except:` catches every exception, including SystemExit,
    KeyboardInterrupt, and GeneratorExit - it can swallow a Ctrl-C or mask
    an unrelated bug as "the operation being tried failed". Always flagged.
  - `except Exception:` / `except BaseException:` whose handler body does
    nothing but `pass` (or a string literal used as an inline comment) is
    a *swallowed* exception: a fault occurred and the system pretends it
    didn't, which is close to the opposite of fault tolerance - the
    handler doesn't retry, log, re-raise, or degrade gracefully, it just
    hides that anything happened. A handler catching the same broad types
    but that logs, re-raises, or returns a value is NOT flagged - the
    breadth of the `except` clause isn't itself the problem, silently
    discarding the fault is.
"""
from __future__ import annotations

import ast

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import RepositorySnapshot

_ANALYZER = "wsqfai.measurement.reliability"
_BROAD_EXCEPTION_NAMES = {"Exception", "BaseException"}


def _is_broad_exception_type(type_node: ast.expr | None) -> bool:
    return isinstance(type_node, ast.Name) and type_node.id in _BROAD_EXCEPTION_NAMES


def _is_swallowed(body: list[ast.stmt]) -> bool:
    """True if a handler body does nothing but `pass` and/or hold a bare
    string-literal expression (an inline comment written as a string) -
    no logging call, no re-raise, no return, no other side effect."""
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            continue
        return False
    return True


def _fault_tolerance_findings_for_file(path: str, content: str) -> list[Finding]:
    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return []

    bare_lines: list[int] = []
    swallowed_handlers: list[ast.ExceptHandler] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None:
            bare_lines.append(node.lineno)
        elif _is_broad_exception_type(node.type) and _is_swallowed(node.body):
            swallowed_handlers.append(node)
    swallowed_lines = [h.lineno for h in swallowed_handlers]

    findings: list[Finding] = []
    if bare_lines:
        findings.append(Finding(
            title=f"Bare 'except:' clause(s) in {path}",
            description=(
                f"{len(bare_lines)} bare 'except:' clause(s) found (first at line {bare_lines[0]}). "
                "A bare except catches every exception, including SystemExit, KeyboardInterrupt, "
                "and GeneratorExit - not just the fault the code was trying to guard against - which "
                "can mask an unrelated bug as if it were an expected failure, or swallow a Ctrl-C/"
                "shutdown signal entirely. ISO/IEC 25010's Fault Tolerance sub-characteristic: "
                "'degree to which a system operates as intended despite hardware or software faults'."
            ),
            characteristic=QualityCharacteristic.RELIABILITY,
            sub_characteristic_key="fault_tolerance",
            severity=Severity.HIGH,
            evidence=[Evidence(
                location=SourceLocation(file_path=path, start_line=bare_lines[0]),
                snippet=f"{len(bare_lines)} bare except clause(s), first at line {bare_lines[0]}",
                analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="bare_except", confidence=Confidence.HIGH),
            )],
        ))
    if swallowed_handlers:
        first_handler = swallowed_handlers[0]
        # Only a handler whose body is a single bare `pass` (the common real-
        # world shape) gets a precise enough location for remediation.py to
        # safely replace with a logging call - multi-statement or
        # comment-string bodies stay None here, which remediation.py treats
        # as "not precise enough to auto-fix", falling back to its Suggestion.
        body_line = (
            first_handler.body[0].lineno
            if len(first_handler.body) == 1 and isinstance(first_handler.body[0], ast.Pass)
            else None
        )
        findings.append(Finding(
            title=f"Swallowed exception(s) in {path}",
            description=(
                f"{len(swallowed_lines)} handler(s) catching Exception/BaseException do nothing but "
                f"'pass' (first at line {swallowed_lines[0]}) - no logging, no re-raise, no return "
                "value signalling failure. A fault occurred and the system proceeds as if it hadn't, "
                "which is close to the opposite of fault tolerance: tolerating a fault means "
                "recovering from or reporting it, not hiding that it happened. ISO/IEC 25010's "
                "Fault Tolerance sub-characteristic."
            ),
            characteristic=QualityCharacteristic.RELIABILITY,
            sub_characteristic_key="fault_tolerance",
            severity=Severity.MEDIUM,
            evidence=[Evidence(
                location=SourceLocation(file_path=path, start_line=swallowed_lines[0], end_line=body_line),
                snippet=f"{len(swallowed_lines)} swallowed broad-exception handler(s), first at line {swallowed_lines[0]}",
                analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="swallowed_broad_exception", confidence=Confidence.MEDIUM),
            )],
        ))
    return findings


def compute_reliability_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    """Run every Reliability metric this module implements against every
    Python file in the snapshot that has retained content and parses as
    valid Python. Files that fail to parse (encoding issues, a non-Python
    dialect, truncated content) are skipped rather than raising - a
    measurement layer that crashes on one malformed file in a 5000-file
    repository is worse than one that skips it and keeps going."""
    findings: list[Finding] = []
    for f in snapshot.files:
        if f.language != "Python" or not f.content:
            continue
        findings.extend(_fault_tolerance_findings_for_file(f.path, f.content))
    return findings
