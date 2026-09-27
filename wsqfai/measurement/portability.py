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

requirements.txt gets one Finding per unpinned line (each with a real line
number), not one aggregated Finding per file - deliberately, so
wsqfai/remediation.py can fix each one independently rather than needing
to re-parse a summary string. pyproject.toml's dependencies array doesn't
carry line numbers through tomllib, so it stays a single aggregated,
non-line-precise Finding - reported, not (yet) auto-fixable.
"""
from __future__ import annotations

import re

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import RepositorySnapshot

_ANALYZER = "wsqfai.measurement.portability"
_VERSION_OPERATOR_RE = re.compile(r"(==|>=|<=|~=|!=|>|<)")


def _requirements_txt_unpinned(content: str) -> list[tuple[int, str]]:
    """(line_number, dependency_declaration) for every line with no
    version operator at all - 1-indexed to match SourceLocation.start_line."""
    unpinned: list[tuple[int, str]] = []
    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        if not _VERSION_OPERATOR_RE.search(line):
            unpinned.append((lineno, line))
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


def _requirements_txt_finding(file_path: str, lineno: int, declaration: str) -> Finding:
    return Finding(
        title=f"Unpinned dependency in {file_path}: {declaration}",
        description=(
            f"{declaration!r} (line {lineno} of {file_path}) has no version constraint at all. A "
            "fresh install can silently resolve a different, untested version of this dependency "
            "than the one this repository was last known to work with - ISO/IEC 25010's "
            "Installability sub-characteristic: the degree to which a product can be successfully "
            "installed in a specified environment."
        ),
        characteristic=QualityCharacteristic.PORTABILITY,
        sub_characteristic_key="installability",
        severity=Severity.MEDIUM,
        evidence=[Evidence(
            location=SourceLocation(file_path=file_path, start_line=lineno, end_line=lineno),
            snippet=declaration,
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="unpinned_dependency", confidence=Confidence.HIGH),
        )],
    )


def _pyproject_toml_finding(file_path: str, unpinned: list[str]) -> Finding:
    return Finding(
        title=f"Unpinned dependencies in {file_path}",
        description=(
            f"{len(unpinned)} dependency declaration(s) in {file_path} have no version constraint "
            f"at all (e.g. {', '.join(unpinned[:5])}). Same risk as requirements.txt's own version - "
            "ISO/IEC 25010's Installability sub-characteristic. tomllib doesn't expose source line "
            "numbers for array entries, so this is reported as one aggregated finding, not one "
            "auto-fixable Finding per dependency."
        ),
        characteristic=QualityCharacteristic.PORTABILITY,
        sub_characteristic_key="installability",
        severity=Severity.MEDIUM,
        evidence=[Evidence(
            location=SourceLocation(file_path=file_path),
            snippet=f"{len(unpinned)} unconstrained dependencies: {', '.join(unpinned[:5])}",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="unpinned_dependency_pyproject", confidence=Confidence.HIGH),
        )],
    )


def compute_portability_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    findings: list[Finding] = []
    for f in snapshot.files:
        if f.content is None:
            continue
        name = f.path.rsplit("/", 1)[-1]
        if name == "requirements.txt":
            findings.extend(_requirements_txt_finding(f.path, lineno, decl) for lineno, decl in _requirements_txt_unpinned(f.content))
        elif name == "pyproject.toml":
            unpinned = _pyproject_toml_unpinned(f.content)
            if unpinned:
                findings.append(_pyproject_toml_finding(f.path, unpinned))
    return findings
