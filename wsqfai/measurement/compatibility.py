"""
M2b (Compatibility slice): real detection of a hardcoded network port
number passed to a `port=` keyword argument - ISO/IEC 25010's Co-existence
sub-characteristic ("degree to which a product can perform required
functions efficiently while sharing an environment with other products,
without negative impact on any of them").

A service that hardcodes the TCP port it binds to (`app.run(port=5000)`,
`uvicorn.run(app, port=8000)`) cannot share a host with another instance of
itself, or with an unrelated service that happens to want the same port,
without the user first finding and editing the source. Reading the port
from the environment instead (`port=int(os.environ.get("PORT", 5000))`) is
long-standing, widely-cited practice for exactly this reason - the Twelve-
Factor App methodology's "Config" factor names port binding as its
canonical example of configuration that must come from the environment,
not be baked into source. This is not specific to any one web framework:
the check is scoped to the keyword name `port=` itself, which is the
common signature across Flask, FastAPI/uvicorn, and plain `socketserver`-
style servers alike.

Detection uses Python's own `ast` module. Deliberately narrow: only a bare
integer literal passed as `port=` is flagged - `port=int(os.environ.get(
"PORT", 5000))` is a `Call`, not a `Constant`, and is correctly left alone,
since the port is already configurable there even though a literal default
still appears in the source. Test files are excluded, since a hardcoded
port bound to `localhost` for the duration of a single test run is normal,
not a real co-existence risk.
"""
from __future__ import annotations

import ast

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import RepositorySnapshot

_ANALYZER = "wsqfai.measurement.compatibility"
_TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs"}


def _is_test_path(path: str) -> bool:
    lower = path.lower()
    parts = lower.split("/")
    if any(part in _TEST_DIR_NAMES for part in parts[:-1]):
        return True
    name = parts[-1]
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def _hardcoded_port_lines(tree: ast.Module) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "port" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int):
                lines.append(node.lineno)
    return sorted(set(lines))


def _co_existence_finding(path: str, lines: list[int]) -> Finding:
    first = lines[0]
    return Finding(
        title=f"Hardcoded network port in {path}",
        description=(
            f"{len(lines)} call(s) pass a literal integer as port= (first at line {first}) instead "
            "of reading it from the environment. A service that hardcodes the port it binds to can't "
            "share a host with another instance of itself, or with an unrelated service that wants "
            "the same port, without the user first finding and editing the source - the Twelve-Factor "
            "App methodology's 'Config' factor names port binding as its canonical example of "
            "configuration that belongs in the environment, not in source. ISO/IEC 25010's "
            "Co-existence sub-characteristic: the degree to which a product can perform required "
            "functions efficiently while sharing an environment with other products."
        ),
        characteristic=QualityCharacteristic.COMPATIBILITY,
        sub_characteristic_key="co_existence",
        severity=Severity.LOW,
        evidence=[Evidence(
            location=SourceLocation(file_path=path, start_line=first, end_line=first),
            snippet=f"{len(lines)} hardcoded port= literal(s), first at line {first}",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="hardcoded_port", confidence=Confidence.MEDIUM),
        )],
    )


def compute_compatibility_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    """Run every Compatibility metric this module implements against every
    non-test Python file in the snapshot that has retained content and
    parses as valid Python. Files that fail to parse are skipped rather
    than raising - same discipline as the other measurement modules."""
    findings: list[Finding] = []
    for f in snapshot.files:
        if f.language != "Python" or not f.content or _is_test_path(f.path):
            continue
        try:
            tree = ast.parse(f.content)
        except (SyntaxError, ValueError):
            continue
        lines = _hardcoded_port_lines(tree)
        if lines:
            findings.append(_co_existence_finding(f.path, lines))
    return findings
