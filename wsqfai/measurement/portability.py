"""
M2b (Portability slice): real detection of unpinned dependencies in a
repository's own dependency manifest (`requirements.txt` or the
`[project.dependencies]` table of `pyproject.toml`).

ISO/IEC 25010 defines Installability as "the degree of effectiveness and
efficiency with which a product can be successfully installed... in a
specified environment" - a manifest that names a dependency with no
version constraint at all (`requests` instead of `requests==2.31.0`)
means a fresh install can silently pull a different, untested version of
that dependency than the one the repository was last known to work with,
directly threatening exactly that. This is a long-established supply-chain
hygiene practice (pip's own docs recommend pinning for reproducible
installs), not invented for this project.

Deliberately narrow: a dependency with *any* version operator (`==`,
`>=`, `~=`, ...) is treated as constrained and left unflagged, even though
a range like `>=2.0` is weaker than an exact pin - the goal here is
catching completely unconstrained dependencies, the clearest and lowest-
false-positive signal, not grading pin strictness.
"""
from __future__ import annotations

import re

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import RepositorySnapshot

_ANALYZER = "wsqfai.measurement.portability"
_VERSION_OPERATOR_RE = re.compile(r"(==|>=|<=|~=|!=|>|<)")


def _requirements_txt_unpinned(content: str) -> list[str]:
    unpinned: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        if not _VERSION_OPERATOR_RE.search(line):
            unpinned.append(line)
    return unpinned


def _pyproject_toml_unpinned(content: str) -> list[str]:
    try:
        import tomllib
    except ImportError:
        return []
    try:
        data = tomllib.loads(content)
    except (tomllib.TOMLDecodeError, ValueError):
        return []
    dependencies = data.get("project", {}).get("dependencies", [])
    unpinned: list[str] = []
    for dep in dependencies:
        if not isinstance(dep, str):
            continue
        name_part = dep.split(";", 1)[0]  # drop an environment marker before checking
        if not _VERSION_OPERATOR_RE.search(name_part):
            unpinned.append(dep)
    return unpinned


def compute_portability_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    findings: list[Finding] = []
    for f in snapshot.files:
        if f.content is None:
            continue
        name = f.path.rsplit("/", 1)[-1]
        if name == "requirements.txt":
            unpinned = _requirements_txt_unpinned(f.content)
        elif name == "pyproject.toml":
            unpinned = _pyproject_toml_unpinned(f.content)
        else:
            continue
        if not unpinned:
            continue
        findings.append(Finding(
            title=f"Unpinned dependencies in {f.path}",
            description=(
                f"{len(unpinned)} dependency declaration(s) in {f.path} have no version constraint "
                f"at all (e.g. {', '.join(unpinned[:5])}). A fresh install can silently resolve a "
                "different, untested version of that dependency than the one this repository was "
                "last known to work with - ISO/IEC 25010's Installability sub-characteristic: the "
                "degree to which a product can be successfully installed in a specified environment."
            ),
            characteristic=QualityCharacteristic.PORTABILITY,
            sub_characteristic_key="installability",
            severity=Severity.MEDIUM,
            evidence=[Evidence(
                location=SourceLocation(file_path=f.path),
                snippet=f"{len(unpinned)} unconstrained dependencies: {', '.join(unpinned[:5])}",
                analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="unpinned_dependency", confidence=Confidence.HIGH),
            )],
        ))
    return findings
