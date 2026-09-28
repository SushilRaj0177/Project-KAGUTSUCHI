"""
M4a (new slice): static detection of a hardcoded credential literal -
ISO/IEC 25010's Confidentiality sub-characteristic ("degree to which data
is accessible only to those authorized to have access").

Unlike the rest of ast_scan.py's detectors, this mints a real `Finding`
directly rather than an unverified `Observation`: there is nothing to
sandbox-verify here. A command-injection *hypothesis* needs proving
because whether attacker input actually reaches the shell depends on
runtime behaviour a static match can't see; a hardcoded secret literal
*is* the evidence - the string is sitting in the source right now, no
execution needed to confirm it. This is the same distinction reliability.py
draws for bare `except:` clauses: the AST match itself is the complete
proof.

This is a long-established, real static-analysis practice, not invented
for this project - Bandit's B105/B106/B107 hardcoded-password checks and
secret-scanning tools like gitleaks/truffleHog work the same way: flag an
assignment to a credential-shaped variable name whose value is a plain
string literal.

Deliberately narrow to keep the false-positive rate low:
  - Only a bare string `Constant` counts as a "hardcoded" value -
    `os.environ.get("API_KEY")` or `settings.SECRET_KEY` are calls/
    attribute lookups, not literals, and are correctly left alone.
  - The variable name must match a credential-shaped pattern (password,
    secret, api key, access key, private key, auth/bearer token) - a
    plain `key = "..."` for an unrelated dict key is not flagged.
  - Obvious placeholders (`changeme`, `xxx`, `<your-key-here>`, `todo`,
    an empty string, anything under 8 characters) are excluded - these are
    documentation/example values, not real leaked credentials.
  - Test files are excluded, matching wsqfai.measurement.compatibility's
    precedent: fixture credentials in test setup are a different, lower-
    severity concern than a real leaked secret in application code, and
    including them would mostly add noise.
"""
from __future__ import annotations

import ast
import re

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.ingestion.repository import RepositorySnapshot

_ANALYZER = "wsqfai.security.secrets"
_TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs"}

_CREDENTIAL_NAME_RE = re.compile(
    r"(?i)(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|private[_-]?key|auth[_-]?token|bearer[_-]?token)"
)
_PLACEHOLDER_RE = re.compile(r"(?i)(changeme|change_me|xxx|todo|fixme|example|placeholder|insert|your|_here$|<.*>|\*{3,})")
_MIN_SECRET_LENGTH = 8


def _is_test_path(path: str) -> bool:
    lower = path.lower()
    parts = lower.split("/")
    if any(part in _TEST_DIR_NAMES for part in parts[:-1]):
        return True
    name = parts[-1]
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def _looks_like_a_real_secret(value: str) -> bool:
    if len(value) < _MIN_SECRET_LENGTH:
        return False
    if _PLACEHOLDER_RE.search(value):
        return False
    return True


def _target_names(target: ast.expr) -> list[str]:
    """Variable name(s) an assignment target introduces - just plain
    `Name` targets (`x = ...`), not attributes/subscripts/tuples, which
    aren't the common way a credential constant gets declared."""
    if isinstance(target, ast.Name):
        return [target.id]
    return []


def _hardcoded_secret_lines(tree: ast.Module) -> list[tuple[int, str]]:
    """(line_number, matched_variable_name) for every assignment whose
    target name looks credential-shaped and whose value is a plausible
    hardcoded secret literal."""
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [name for t in node.targets for name in _target_names(t)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = _target_names(node.target)
            value = node.value
        else:
            continue
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        for name in targets:
            if _CREDENTIAL_NAME_RE.search(name) and _looks_like_a_real_secret(value.value):
                hits.append((node.lineno, name))
    return hits


def _hardcoded_secret_finding(path: str, lineno: int, name: str) -> Finding:
    return Finding(
        title=f"Hardcoded credential in {path}",
        description=(
            f"'{name}' (line {lineno} of {path}) is assigned a plain string literal that looks like a "
            "real credential, not a placeholder. A secret committed to source is exposed to anyone with "
            "read access to the repository (and its full history, even if removed later) - it should be "
            "read from the environment or a secrets manager instead. This is the same class of check "
            "Bandit's hardcoded-password rules and secret scanners like gitleaks/truffleHog perform. "
            "ISO/IEC 25010's Confidentiality sub-characteristic: the degree to which data is accessible "
            "only to those authorized to have access."
        ),
        characteristic=QualityCharacteristic.SECURITY,
        sub_characteristic_key="confidentiality",
        severity=Severity.HIGH,
        evidence=[Evidence(
            location=SourceLocation(file_path=path, start_line=lineno, end_line=lineno),
            snippet=f"{name} = <redacted>",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="hardcoded_credential", confidence=Confidence.MEDIUM),
        )],
    )


def compute_hardcoded_secret_findings(snapshot: RepositorySnapshot) -> list[Finding]:
    """Run this detector against every non-test Python file in the
    snapshot that has retained content and parses as valid Python. Files
    that fail to parse are skipped rather than raising - same discipline
    as every other measurement/security module."""
    findings: list[Finding] = []
    for f in snapshot.files:
        if f.language != "Python" or not f.content or _is_test_path(f.path):
            continue
        try:
            tree = ast.parse(f.content)
        except (SyntaxError, ValueError):
            continue
        for lineno, name in _hardcoded_secret_lines(tree):
            findings.append(_hardcoded_secret_finding(f.path, lineno, name))
    return findings
