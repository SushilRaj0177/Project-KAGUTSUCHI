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

This module deliberately implements only ML-repository detection and the
ML Versioning check for now. The catalogue's remaining patterns and
anti-patterns (Glue Code, Pipeline Jungles, Dead Experimental Codepaths,
Test Infrastructure Independence, Wrap Black-box Packages...) don't yet
have a detection heuristic here that's reliable enough not to be mostly
false positives from a purely static, no-execution read of the source -
building one honestly, rather than shipping a rule that just pattern-
matches import statements and calls it done, is real further M3 work.
"""
from __future__ import annotations

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
    return findings
