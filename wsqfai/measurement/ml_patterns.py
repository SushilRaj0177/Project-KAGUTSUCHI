"""
M3a: the first slice of the ISO/IEC 25059 AI/ML quality extension - real
detection of whether a repository is ML-containing, plus one concrete
finding grounded in Washizaki et al.'s own ML design-pattern catalogue
rather than a generic linting rule with his name attached to it after the
fact.

Source: Washizaki, Khomh, Gueheneuc, Takeuchi, Natori, Okuda, "Software
Engineering Design Patterns for Machine Learning Applications", IEEE
Computer, Vol. 55, No. 3, March 2022 - a multivocal literature review that
catalogued 12 ML architecture patterns, 13 ML design patterns, and 8 ML
anti-patterns, building in part on Sculley et al.'s "Hidden Technical Debt
in Machine Learning Systems" (NeurIPS 2015). "ML Versioning" is one of the
13 cataloged design patterns: it addresses the fact that ML systems, unlike
conventional software, need traceability across code AND the data/model
artifacts trained from it - without it, reproducing or rolling back a
model's behaviour becomes guesswork.

M3b adds one more of the catalogue's 8 anti-patterns: Dead Experimental
Codepaths. Sculley et al.'s original paper describes it directly - ML
development often proceeds by trying an alternative approach behind a
conditional, and "it is often the case that the branches taken by such
[dead] codepaths never fire in production... over time, it is common for
these branches to become increasingly stale," accumulating debt and
obscuring what the system actually does. A branch gated on a literal
`False`/`0` (`if False: ...`) can never fire at all - the least ambiguous,
lowest-false-positive instance of this pattern a purely static, no-
execution read of the source can identify: no semantic analysis needed to
know it's dead, since the condition can never be true regardless of any
runtime state.

The catalogue's remaining patterns and anti-patterns (Glue Code, Pipeline
Jungles, Test Infrastructure Independence, Wrap Black-box Packages...)
still don't have a detection heuristic here that's reliable enough not to
be mostly false positives from a purely static, no-execution read of the
source - building one honestly, rather than shipping a rule that just
pattern-matches import statements and calls it done, is real further M3
work.
"""
from __future__ import annotations

import ast
import re

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot

_ANALYZER = "wsqfai.measurement.ml_patterns"

# Common, general-purpose ML/DL frameworks. Deliberately not exhaustive -
# see this module's docstring on scoping - but each entry here is a
# genuinely widely-used framework whose import is a strong, low-noise
# signal that a repository trains or serves ML models, not just uses
# statistics incidentally (e.g. plain numpy/pandas are excluded for that
# reason).
_ML_LIBRARIES = ("sklearn", "torch", "tensorflow", "keras", "xgboost", "lightgbm", "catboost", "transformers", "jax")
_ML_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(?:" + "|".join(_ML_LIBRARIES) + r")\b",
    re.MULTILINE,
)

_VERSIONING_FILENAMES = {"dvc.yaml", "dvc.lock", "MLproject"}
_VERSIONING_CONTENT_RE = re.compile(r"\b(mlflow|dvc\.api|model_registry|ModelRegistry)\b")
_VERSIONED_ARTIFACT_RE = re.compile(r".*_v\d+\.(pkl|pt|pth|h5|onnx|joblib)$", re.IGNORECASE)


def _ml_importing_files(snapshot: RepositorySnapshot) -> list[FileRecord]:
    return [
        f for f in snapshot.files
        if f.language == "Python" and f.content and _ML_IMPORT_RE.search(f.content)
    ]


def is_ml_repository(snapshot: RepositorySnapshot) -> bool:
    """Whether this snapshot shows direct evidence of using a general-
    purpose ML/DL framework - the gate for whether ISO/IEC 25059's
    AI-specific quality characteristics, and this module's findings, even
    apply to this repository at all."""
    return bool(_ml_importing_files(snapshot))


def _has_ml_versioning_signal(snapshot: RepositorySnapshot) -> bool:
    for f in snapshot.files:
        name = f.path.rsplit("/", 1)[-1]
        if name in _VERSIONING_FILENAMES:
            return True
        if _VERSIONED_ARTIFACT_RE.match(f.path):
            return True
        if f.content and _VERSIONING_CONTENT_RE.search(f.content):
            return True
    return False


def _missing_ml_versioning_finding(snapshot: RepositorySnapshot) -> Finding | None:
    ml_files = _ml_importing_files(snapshot)
    if not ml_files or _has_ml_versioning_signal(snapshot):
        return None
    return Finding(
        title="No model/data versioning signal detected in an ML-containing repository",
        description=(
            f"{len(ml_files)} file(s) import a general-purpose ML/DL framework (e.g. "
            f"{ml_files[0].path}), but no versioning signal was found repo-wide - no DVC config "
            "(dvc.yaml/dvc.lock), no MLflow or model-registry usage, no MLproject file, and no "
            "model artifact filename following a *_v<N>.<ext> convention. Washizaki et al.'s ML "
            "design-pattern catalogue (IEEE Computer, Vol. 55 No. 3, March 2022) documents 'ML "
            "Versioning' as a recurring good pattern precisely because ML systems need "
            "traceability across both code and the data/model artifacts trained from it; without "
            "it, reproducing or rolling back a model's behaviour becomes guesswork - ISO/IEC "
            "25010's Modifiability sub-characteristic.\n\n"
            "This is a structural check for known versioning-tool signals, not proof that no "
            "versioning discipline exists at all (e.g. in a separate infrastructure repository "
            "this scan doesn't see)."
        ),
        characteristic=QualityCharacteristic.MAINTAINABILITY,
        sub_characteristic_key="modifiability",
        severity=Severity.MEDIUM,
        evidence=[Evidence(
            location=SourceLocation(file_path=ml_files[0].path),
            snippet="imports an ML framework; no DVC/MLflow/model-registry/versioned-artifact signal found repo-wide",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="missing_ml_versioning_signal", confidence=Confidence.LOW),
        )],
    )


def _is_always_false_test(test: ast.expr) -> bool:
    return isinstance(test, ast.Constant) and test.value in (False, 0)


def _is_trivial_body(body: list[ast.stmt]) -> bool:
    """True if `body` is empty of real logic - just `pass` and/or a bare
    string literal (a docstring/inline comment) - in which case there's no
    accumulated debt worth reporting, just an inert placeholder."""
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            continue
        return False
    return True


def _dead_experimental_codepath_lines(tree: ast.Module) -> list[int]:
    return sorted({
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.If) and _is_always_false_test(node.test) and not _is_trivial_body(node.body)
    })


def _dead_experimental_codepath_finding(path: str, lines: list[int]) -> Finding:
    first = lines[0]
    return Finding(
        title=f"Dead experimental codepath(s) in {path}",
        description=(
            f"{len(lines)} branch(es) gated on a literal 'if False:'/'if 0:' (first at line {first}) "
            "contain real code that can never execute, regardless of any runtime state. Sculley et "
            "al.'s 'Hidden Technical Debt in Machine Learning Systems' (NeurIPS 2015) describes this "
            "exact pattern - ML development often proceeds by trying an alternative approach behind a "
            "conditional that's later disabled rather than removed, and these branches accumulate as "
            "debt, obscuring what the system actually does. Washizaki et al.'s ML design-pattern "
            "catalogue (IEEE Computer, Vol. 55 No. 3, March 2022) documents 'Dead Experimental "
            "Codepaths' as one of its 8 cataloged anti-patterns. ISO/IEC 25010's Analysability "
            "sub-characteristic: a reader has to reason about a path that can never run."
        ),
        characteristic=QualityCharacteristic.MAINTAINABILITY,
        sub_characteristic_key="analysability",
        severity=Severity.LOW,
        evidence=[Evidence(
            location=SourceLocation(file_path=path, start_line=first, end_line=first),
            snippet=f"{len(lines)} 'if False:'/'if 0:' branch(es) with real code, first at line {first}",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="dead_experimental_codepath", confidence=Confidence.HIGH),
        )],
    )


def _dead_experimental_codepath_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    findings: list[Finding] = []
    for f in snapshot.files:
        if f.language != "Python" or not f.content:
            continue
        try:
            tree = ast.parse(f.content)
        except (SyntaxError, ValueError):
            continue
        lines = _dead_experimental_codepath_lines(tree)
        if lines:
            findings.append(_dead_experimental_codepath_finding(f.path, lines))
    return findings


def compute_ml_pattern_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    """Run every ML-pattern check this module implements. Returns an empty
    list for a repository with no detected ML framework usage - these
    findings only make a claim about ML-specific practice, never about a
    repository that isn't doing ML in the first place."""
    if not is_ml_repository(snapshot):
        return []
    findings: list[Finding] = []
    versioning_finding = _missing_ml_versioning_finding(snapshot)
    if versioning_finding is not None:
        findings.append(versioning_finding)
    findings.extend(_dead_experimental_codepath_findings(snapshot))
    return findings
