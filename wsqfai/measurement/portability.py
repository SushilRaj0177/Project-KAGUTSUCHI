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
to re-parse a summary string.

pyproject.toml's dependencies array doesn't carry line numbers through
tomllib, so line numbers for it are recovered separately here with a
narrow raw-text scan of the `[project]` table's `dependencies = [...]`
array (tomllib stays the source of truth for *which* entries are
unpinned; the raw scan only supplies *where*). If that scan can't find a
line for every entry tomllib reports as unpinned - a dependencies array
built some other way this scan doesn't recognize - it falls back to one
aggregated, non-line-precise Finding rather than reporting a wrong line
number. The per-entry Finding is auto-fixable after all
(`remediation.py`'s `_fix_unpinned_dependency_pyproject` - a quoted-string
line-splice, not the whole-line replacement `requirements.txt` uses,
since a TOML array entry shares its line with brackets/commas/siblings);
only the aggregated fallback, with no precise line at all, genuinely
stays unfixable.

Also covers `package.json`'s `dependencies`/`devDependencies` - the same
Installability risk, but with npm's opposite ecosystem convention: a bare
version (`"2.31.0"`) IS an exact pin in npm, and `npm install` itself
writes a caret range (`^2.31.0`) by default, constraining to a major
version at minimum. Flagging every `^`/`~` range the way a Python range
operator is left alone would just be noise inconsistent with how the
ecosystem is actually used - so only the genuinely unconstrained
specifiers (`*`, `x`, `latest`, or an empty string - "whatever's
currently published, no constraint at all") are flagged, the npm-shaped
equivalent of requirements.txt's bare `requests`. A `workspace:`/`file:`/
`link:`/`git+`/URL specifier is deliberately never flagged either, even
though it carries no semver constraint: it pins to a specific known
source (a monorepo's own local package, a fixed commit, a fixed file),
not "whatever the registry currently serves". `dependencies` and
`devDependencies` only - `peerDependencies`/`optionalDependencies` aren't
covered, a stated narrowing rather than a silent gap.
"""
from __future__ import annotations

import json
import re

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import RepositorySnapshot

_ANALYZER = "wsqfai.measurement.portability"
_VERSION_OPERATOR_RE = re.compile(r"(==|>=|<=|~=|!=|>|<)")
_PROJECT_HEADER_RE = re.compile(r"^\s*\[project\]\s*$")
_TABLE_HEADER_RE = re.compile(r"^\s*\[")
_DEPENDENCIES_KEY_RE = re.compile(r"^\s*dependencies\s*=\s*\[")
_STRING_LITERAL_RE = re.compile(r'"([^"]*)"|\'([^\']*)\'')

_NPM_DEPENDENCY_GROUPS = ("dependencies", "devDependencies")
_NPM_FULLY_UNCONSTRAINED = {"*", "x", "latest", ""}
_NPM_PINNED_SOURCE_PREFIXES = ("workspace:", "file:", "link:", "git+", "git:", "http://", "https://")
_PACKAGE_JSON_GROUP_HEADER_RE_TEMPLATE = r'^\s*"{group}"\s*:\s*\{{\s*$'
_PACKAGE_JSON_DEP_LINE_RE = re.compile(r'^\s*"([^"]+)"\s*:\s*"([^"]*)"\s*,?\s*$')


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


def _pyproject_toml_dependency_lines(content: str) -> list[tuple[int, str]]:
    """(line_number, raw_dependency_string) for every string literal found
    inside the `[project]` table's `dependencies = [...]` array, via a raw
    text scan (tomllib itself doesn't expose array-entry line numbers).
    Deliberately narrow: only the first such array is scanned, and only a
    plain `[project]` dependencies array is recognized - `dynamic`
    dependencies or a dependencies array assembled some other way just
    yields no lines, which callers treat as "line numbers unavailable"
    rather than a wrong guess."""
    in_project = False
    in_deps_array = False
    entries: list[tuple[int, str]] = []
    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        if not in_deps_array:
            if _PROJECT_HEADER_RE.match(raw_line):
                in_project = True
                continue
            if in_project and _TABLE_HEADER_RE.match(raw_line):
                break  # left the [project] table without finding dependencies
            if not (in_project and _DEPENDENCIES_KEY_RE.match(raw_line)):
                continue
            in_deps_array = True
        for match in _STRING_LITERAL_RE.finditer(raw_line):
            entries.append((lineno, match.group(1) if match.group(1) is not None else match.group(2)))
        if "]" in raw_line:
            break
    return entries


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


def _pyproject_toml_line_finding(file_path: str, lineno: int, declaration: str) -> Finding:
    return Finding(
        title=f"Unpinned dependency in {file_path}: {declaration}",
        description=(
            f"{declaration!r} (line {lineno} of {file_path}) has no version constraint at all. Same "
            "risk as an unpinned requirements.txt entry - ISO/IEC 25010's Installability "
            "sub-characteristic: a fresh install can silently resolve a different, untested version."
        ),
        characteristic=QualityCharacteristic.PORTABILITY,
        sub_characteristic_key="installability",
        severity=Severity.MEDIUM,
        evidence=[Evidence(
            location=SourceLocation(file_path=file_path, start_line=lineno, end_line=lineno),
            snippet=declaration,
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="unpinned_dependency_pyproject", confidence=Confidence.HIGH),
        )],
    )


def _pyproject_toml_findings(file_path: str, content: str) -> list[Finding]:
    unpinned = _pyproject_toml_unpinned(content)
    if not unpinned:
        return []
    # Consume each raw (line, declaration) entry at most once so a duplicate
    # declaration string doesn't collapse onto a single line.
    remaining = list(_pyproject_toml_dependency_lines(content))
    resolved: list[tuple[int, str]] = []
    for declaration in unpinned:
        match_index = next((i for i, (_, raw) in enumerate(remaining) if raw == declaration), None)
        if match_index is None:
            return [_pyproject_toml_finding(file_path, unpinned)]  # scan couldn't place every entry
        lineno, _ = remaining.pop(match_index)
        resolved.append((lineno, declaration))
    return [_pyproject_toml_line_finding(file_path, lineno, declaration) for lineno, declaration in resolved]


def _package_json_unpinned(content: str) -> list[tuple[str, str, str]]:
    """(dependency_group, name, version_spec) for every `dependencies`/
    `devDependencies` entry whose specifier is genuinely unconstrained -
    see this module's docstring for exactly which specifiers that means
    and why a caret/tilde range doesn't count. Returns an empty list for
    anything that doesn't parse as a JSON object - a malformed manifest is
    a different problem this check doesn't claim to diagnose."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    unpinned: list[tuple[str, str, str]] = []
    for group in _NPM_DEPENDENCY_GROUPS:
        deps = data.get(group)
        if not isinstance(deps, dict):
            continue
        for dep_name, spec in deps.items():
            if not isinstance(spec, str):
                continue
            stripped = spec.strip()
            if stripped.startswith(_NPM_PINNED_SOURCE_PREFIXES):
                continue
            if stripped in _NPM_FULLY_UNCONSTRAINED:
                unpinned.append((group, dep_name, spec))
    return unpinned


def _package_json_dependency_lines(content: str, group: str) -> dict[str, int]:
    """name -> line number for every entry inside `package.json`'s
    top-level `"<group>": { ... }` object, via a narrow raw-text scan -
    the stdlib `json` module doesn't expose source positions. Unlike
    requirements.txt/pyproject.toml, duplicate keys can't occur (a JSON
    object's keys are already unique), so a plain dict is enough - no
    "consume each line at most once" bookkeeping needed."""
    header_re = re.compile(_PACKAGE_JSON_GROUP_HEADER_RE_TEMPLATE.format(group=re.escape(group)))
    lines: dict[str, int] = {}
    in_group = False
    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        if not in_group:
            if header_re.match(raw_line):
                in_group = True
            continue
        if raw_line.strip().startswith("}"):
            break
        match = _PACKAGE_JSON_DEP_LINE_RE.match(raw_line)
        if match:
            lines[match.group(1)] = lineno
    return lines


def _package_json_finding(file_path: str, group: str, name: str, spec: str, lineno: int | None) -> Finding:
    location_note = f" (line {lineno})" if lineno else ""
    return Finding(
        title=f"Unpinned npm dependency in {file_path}: {name}",
        description=(
            f'"{name}": "{spec}" in {group} of {file_path}{location_note} has no version '
            "constraint at all - unlike a caret/tilde range (which still constrains to at least a "
            "major version) or an exact pin, npm resolves this to whatever is currently published "
            "on install. A fresh `npm install` can silently pull a different, untested version - "
            "ISO/IEC 25010's Installability sub-characteristic, the same risk a bare "
            "requirements.txt entry carries for a Python project."
        ),
        characteristic=QualityCharacteristic.PORTABILITY,
        sub_characteristic_key="installability",
        severity=Severity.MEDIUM,
        evidence=[Evidence(
            location=SourceLocation(file_path=file_path, start_line=lineno, end_line=lineno),
            snippet=f'"{name}": "{spec}"',
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="unpinned_dependency_package_json", confidence=Confidence.HIGH),
        )],
    )


def _package_json_findings(file_path: str, content: str) -> list[Finding]:
    unpinned = _package_json_unpinned(content)
    if not unpinned:
        return []
    lines_by_group = {group: _package_json_dependency_lines(content, group) for group in _NPM_DEPENDENCY_GROUPS}
    return [
        _package_json_finding(file_path, group, name, spec, lines_by_group[group].get(name))
        for group, name, spec in unpinned
    ]


def compute_portability_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    findings: list[Finding] = []
    for f in snapshot.files:
        if f.content is None:
            continue
        name = f.path.rsplit("/", 1)[-1]
        if name == "requirements.txt":
            findings.extend(_requirements_txt_finding(f.path, lineno, decl) for lineno, decl in _requirements_txt_unpinned(f.content))
        elif name == "pyproject.toml":
            findings.extend(_pyproject_toml_findings(f.path, f.content))
        elif name == "package.json":
            findings.extend(_package_json_findings(f.path, f.content))
    return findings
