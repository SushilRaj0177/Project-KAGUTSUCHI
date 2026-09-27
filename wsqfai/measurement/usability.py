"""
M2b (Usability slice): real detection of a missing repository README -
ISO/IEC 25010's Appropriateness Recognizability sub-characteristic
("degree to which users can recognize whether a product is appropriate
for their needs").

A repository with no README at all gives a prospective user nothing to
read before deciding whether the project is relevant to them - they'd have
to read source code just to find out what the thing does. This is not an
invented rule: it's the same signal GitHub's own "community standards"
checklist uses, and the reason essentially every open-source contribution
guide starts with "add a README" - a real, long-established convention,
not a stylistic preference invented for this project.

Deliberately narrow: only checks for the file's *presence* at the
repository root, under any of the conventional names/extensions
(`README`, `README.md`, `README.rst`, `README.txt`). It says nothing about
the README's actual content or quality - a one-line README still counts,
since that's a real gap this static check can't reach any further into
without content-quality judgment this tool doesn't have.
"""
from __future__ import annotations

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import RepositorySnapshot

_ANALYZER = "wsqfai.measurement.usability"
_README_NAMES = {"readme", "readme.md", "readme.rst", "readme.txt"}


def _has_root_readme(snapshot: RepositorySnapshot) -> bool:
    return any(
        "/" not in f.path and f.path.lower() in _README_NAMES
        for f in snapshot.files
    )


def _missing_readme_finding(snapshot: RepositorySnapshot) -> Finding:
    return Finding(
        title="No README found at the repository root",
        description=(
            f"{snapshot.owner}/{snapshot.repo} has no README (README/README.md/README.rst/"
            "README.txt) at its root. A prospective user has nothing to read before deciding "
            "whether this project is relevant to their needs - they'd have to read source code "
            "just to find out what it does. This is the same signal GitHub's own community-"
            "standards checklist uses, not an invented rule. ISO/IEC 25010's Appropriateness "
            "Recognizability sub-characteristic: the degree to which users can recognize whether "
            "a product is appropriate for their needs.\n\n"
            "This only checks for the file's presence, not its content or quality - a one-line "
            "README still clears this check."
        ),
        characteristic=QualityCharacteristic.USABILITY,
        sub_characteristic_key="appropriateness_recognizability",
        severity=Severity.LOW,
        evidence=[Evidence(
            location=SourceLocation(file_path="."),
            snippet="no README/README.md/README.rst/README.txt found at the repository root",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="missing_readme", confidence=Confidence.HIGH),
        )],
    )


def compute_usability_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    """Run every Usability metric this module implements against the
    snapshot. Returns an empty list once a root README is found - never
    claims anything about the README's actual content, only its presence."""
    if _has_root_readme(snapshot):
        return []
    return [_missing_readme_finding(snapshot)]
