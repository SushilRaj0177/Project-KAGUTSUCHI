"""
M2: deterministic measurement of ISO/IEC 25010's Maintainability
sub-characteristics - Modularity, Analysability, and Testability - against
a RepositorySnapshot (wsqfai/ingestion/repository.py).

These are chosen first because, per ROADMAP.md, they have the most direct,
uncontroversial static measures reachable from what RepositorySnapshot
actually records: per-file path, language, size in bytes, and line count.
No file content is retained after ingestion (see repository.py's own
docstring on why), so every metric here is deliberately structural - it
measures shape, not semantics. That is a real, honestly-stated limitation,
not a shortcut: a metric that needed source content (cyclomatic complexity,
real duplicate-code detection, actual test-to-code call-graph coverage)
belongs in a later milestone that re-clones and reads files, not here.

Every Finding this module produces cites the exact sub_characteristic_key
it measures (from wsqfai.domain.quality_model) and carries at least one
Evidence item pointing at the file(s) that produced it - the same
provenance discipline evidence.py's docstring describes.
"""
from __future__ import annotations

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot

_ANALYZER = "wsqfai.measurement.maintainability"

# Languages that are code in the sense these metrics care about. Markdown,
# JSON, and YAML are excluded: a large lockfile or a long changelog is not
# evidence of a "god file", and their presence-or-absence says nothing
# about test coverage.
_NON_CODE_LANGUAGES = {"Markdown", "JSON", "YAML", "TOML"}

# A file this long is very likely mixing more than one responsibility.
# 1000/2000 lines are the commonly-cited "God Class/File" thresholds in
# static-analysis literature (e.g. Checkstyle's and PMD's default
# FileLength rules sit in this range) - not invented for this project.
_GOD_FILE_LINES_HIGH = 1000
_GOD_FILE_LINES_CRITICAL = 2000

# Average characters-per-line this high is characteristic of minified or
# machine-generated code, not hand-written source meant to be read.
_LONG_AVERAGE_LINE_LEN = 300
_VERY_LONG_AVERAGE_LINE_LEN = 600

# Below this fraction of code files matching a test-file convention, treat
# testability as measurably weak. This is a structural proxy (naming/path
# convention), not real coverage measurement - stated explicitly in every
# Finding this rule produces, not just here.
_LOW_TEST_FILE_RATIO = 0.10

_TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs"}


def _is_code_file(f: FileRecord) -> bool:
    return f.language is not None and f.language not in _NON_CODE_LANGUAGES


def _is_test_file(path: str) -> bool:
    lower = path.lower()
    parts = lower.split("/")
    if any(part in _TEST_DIR_NAMES for part in parts[:-1]):
        return True
    name = parts[-1]
    if name.startswith("test_") or name.endswith(("_test.py", "_test.go", "test.java", "tests.java", "test.kt")):
        return True
    if ".test." in name or ".spec." in name:
        return True
    return False


def _god_file_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    findings: list[Finding] = []
    for f in snapshot.files:
        if not _is_code_file(f):
            continue
        if f.line_count >= _GOD_FILE_LINES_CRITICAL:
            severity = Severity.HIGH
        elif f.line_count >= _GOD_FILE_LINES_HIGH:
            severity = Severity.MEDIUM
        else:
            continue
        findings.append(Finding(
            title=f"Large file reduces modularity: {f.path}",
            description=(
                f"{f.path} has {f.line_count} lines. Files this large typically mix multiple "
                "responsibilities, making it more likely that a change made for one reason "
                "affects unrelated behaviour in the same file - ISO/IEC 25010's Modularity "
                "sub-characteristic: 'a system composed of discrete components such that a "
                "change to one has minimal impact on others.'"
            ),
            characteristic=QualityCharacteristic.MAINTAINABILITY,
            sub_characteristic_key="modularity",
            severity=severity,
            evidence=[Evidence(
                location=SourceLocation(file_path=f.path),
                snippet=f"{f.line_count} lines, {f.size_bytes} bytes",
                analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="god_file_line_count", confidence=Confidence.HIGH),
            )],
        ))
    return findings


def _low_analysability_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    findings: list[Finding] = []
    for f in snapshot.files:
        if not _is_code_file(f) or f.line_count == 0:
            continue
        avg_len = f.size_bytes / f.line_count
        if avg_len < _LONG_AVERAGE_LINE_LEN:
            continue
        severity = Severity.MEDIUM if avg_len >= _VERY_LONG_AVERAGE_LINE_LEN else Severity.LOW
        findings.append(Finding(
            title=f"Unusually long lines reduce analysability: {f.path}",
            description=(
                f"{f.path} averages {avg_len:.0f} characters per line ({f.size_bytes} bytes over "
                f"{f.line_count} lines). This is characteristic of minified, generated, or "
                "otherwise unformatted code, which is materially harder to read when assessing "
                "the impact of a change - ISO/IEC 25010's Analysability sub-characteristic."
            ),
            characteristic=QualityCharacteristic.MAINTAINABILITY,
            sub_characteristic_key="analysability",
            severity=severity,
            evidence=[Evidence(
                location=SourceLocation(file_path=f.path),
                snippet=f"avg {avg_len:.0f} chars/line over {f.line_count} lines",
                analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="long_average_line_length", confidence=Confidence.MEDIUM),
            )],
        ))
    return findings


def _low_testability_finding(snapshot: RepositorySnapshot) -> Finding | None:
    code_files = [f for f in snapshot.files if _is_code_file(f)]
    if not code_files:
        return None
    test_files = [f for f in code_files if _is_test_file(f.path)]
    ratio = len(test_files) / len(code_files)
    if ratio >= _LOW_TEST_FILE_RATIO:
        return None
    severity = Severity.CRITICAL if ratio == 0 else Severity.HIGH
    return Finding(
        title="Few or no test files detected",
        description=(
            f"{len(test_files)} of {len(code_files)} code files ({ratio:.1%}) match a test-file "
            "naming or location convention (a test/tests/__tests__/spec directory, or a "
            "test_/_test/.test./.spec. naming pattern). A codebase with this little visible test "
            "structure is harder to change safely - ISO/IEC 25010's Testability sub-characteristic. "
            "This is a structural proxy based on naming conventions, not a measurement of actual "
            "test coverage or test quality."
        ),
        characteristic=QualityCharacteristic.MAINTAINABILITY,
        sub_characteristic_key="testability",
        severity=severity,
        evidence=[Evidence(
            location=SourceLocation(file_path="."),
            snippet=f"{len(test_files)}/{len(code_files)} code files match a test convention ({ratio:.1%})",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="low_test_file_ratio", confidence=Confidence.LOW),
        )],
    )


def compute_maintainability_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    """Run every Maintainability metric this module implements against a
    RepositorySnapshot and return the combined list of Findings. Order is
    modularity, then analysability, then testability - matches the order
    ROADMAP.md and this module's docstring describe them in."""
    findings: list[Finding] = []
    findings.extend(_god_file_findings(snapshot))
    findings.extend(_low_analysability_findings(snapshot))
    testability_finding = _low_testability_finding(snapshot)
    if testability_finding is not None:
        findings.append(testability_finding)
    return findings
