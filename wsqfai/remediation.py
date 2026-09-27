"""
M7 (first slice): "clean it up", not just "here's a list of problems."

A report full of Findings tells you what's wrong. It doesn't fix anything.
This module is what turns some of those Findings into a real, applicable
code change - a unified diff, generated from the repository's own actual
file content, not a generic snippet.

Deliberately narrow, and honest about exactly how narrow: only a Finding
whose fix is mechanical and unambiguous gets auto-patched here. A god
file needs a human to decide how to split it. A missing test needs
someone to actually write the test. Auto-generating a fake fix for either
would be worse than reporting the problem and stopping - this module's
whole point is that a patch it produces is something you can `git apply`
with confidence, not something that merely looks like code.

Coverage today (keyed by the `rule_id` a Finding's Evidence carries):
  - `bare_except`                  -> narrow `except:` to `except Exception:`
  - `unpinned_dependency`          -> pin to the dependency's current
                                       latest release on PyPI (real network
                                       lookup; the finding's own line
                                       number makes this a precise,
                                       single-line edit)
  - `sandbox_verified_shell_injection` -> NOT auto-patched (rewriting a
                                       shell-exec call correctly needs
                                       understanding the intended command,
                                       which this doesn't have) - instead
                                       returns human-actionable guidance
                                       text, not a diff.

Everything else returns None: a real, stated gap, not a silent no-op.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from difflib import unified_diff

from pydantic import BaseModel

from wsqfai.domain.evidence import Finding

_BARE_EXCEPT_RE = re.compile(r"^(\s*)except(\s*):(.*)$")


class Fix(BaseModel):
    finding_id: str
    file_path: str
    diff: str
    summary: str
    patched_content: str


class Suggestion(BaseModel):
    """For a Finding this module recognizes but won't auto-patch (the risk
    of getting it wrong mechanically is too high) - human-actionable
    guidance instead of a diff."""

    finding_id: str
    guidance: str


def _unified_diff(file_path: str, before: str, after: str) -> str | None:
    if before == after:
        return None
    return "".join(unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    ))


def _fix_bare_except(finding: Finding, file_content: str) -> Fix | None:
    lineno = finding.evidence[0].location.start_line
    if lineno is None:
        return None
    lines = file_content.splitlines(keepends=True)
    if not (1 <= lineno <= len(lines)):
        return None
    match = _BARE_EXCEPT_RE.match(lines[lineno - 1].rstrip("\n").rstrip("\r"))
    if match is None:
        return None
    indent, _, rest = match.groups()
    line_ending = lines[lineno - 1][len(lines[lineno - 1].rstrip("\r\n")):]
    new_lines = list(lines)
    new_lines[lineno - 1] = f"{indent}except Exception:{rest}{line_ending}"
    after = "".join(new_lines)
    diff = _unified_diff(finding.evidence[0].location.file_path, file_content, after)
    if diff is None:
        return None
    return Fix(
        finding_id=finding.finding_id,
        file_path=finding.evidence[0].location.file_path,
        diff=diff,
        summary="Narrowed bare 'except:' to 'except Exception:' so SystemExit/KeyboardInterrupt/GeneratorExit propagate normally.",
        patched_content=after,
    )


def pypi_latest_version(package_name: str, *, timeout_s: float = 5.0) -> str | None:
    """The current latest release of `package_name` on PyPI, or None if the
    lookup fails for any reason (package doesn't exist, no network, PyPI
    is down, a malformed response) - never raises, since a failed version
    lookup should just mean "don't produce a fix for this one", not crash
    a whole remediation run over one dependency."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:  # noqa: S310 - a fixed, hardcoded host
            data = json.loads(response.read())
        version = data.get("info", {}).get("version")
        return version if isinstance(version, str) and version else None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return None


def _fix_unpinned_dependency(finding: Finding, file_content: str, *, version_lookup=pypi_latest_version) -> Fix | None:
    evidence = finding.evidence[0]
    lineno = evidence.location.start_line
    if lineno is None:
        return None
    package_name = evidence.snippet.strip()
    if not package_name or not re.match(r"^[A-Za-z0-9_.-]+$", package_name):
        return None  # not a bare package name we can safely re-pin (e.g. has extras/markers)
    latest = version_lookup(package_name)
    if latest is None:
        return None

    lines = file_content.splitlines(keepends=True)
    if not (1 <= lineno <= len(lines)):
        return None
    line_ending = lines[lineno - 1][len(lines[lineno - 1].rstrip("\r\n")):]
    new_lines = list(lines)
    new_lines[lineno - 1] = f"{package_name}=={latest}{line_ending}"
    after = "".join(new_lines)
    diff = _unified_diff(evidence.location.file_path, file_content, after)
    if diff is None:
        return None
    return Fix(
        finding_id=finding.finding_id,
        file_path=evidence.location.file_path,
        diff=diff,
        summary=f"Pinned {package_name} to its current latest release ({latest}) from PyPI.",
        patched_content=after,
    )


def _suggest_shell_injection_fix(finding: Finding) -> Suggestion:
    return Suggestion(
        finding_id=finding.finding_id,
        guidance=(
            "Rewrite the shell-string call as an argument list with no shell involved at all - e.g. "
            "subprocess.run([\"ping\", \"-c\", \"1\", host], check=True) instead of "
            "os.system(\"ping -c 1 \" + host). This isn't auto-applied: correctly reconstructing the "
            "intended command and its arguments needs understanding what the code was trying to do, "
            "which this tool doesn't have - only you (or the original author) does."
        ),
    )


_FIXERS = {
    "bare_except": _fix_bare_except,
    "unpinned_dependency": _fix_unpinned_dependency,
}
_SUGGESTERS = {
    "sandbox_verified_shell_injection": _suggest_shell_injection_fix,
}


def propose_fix(finding: Finding, file_contents: dict[str, str]) -> Fix | None:
    """Attempt a real, mechanical fix for `finding`, given a map of
    {file_path: current file content} (e.g. from a RepositorySnapshot's
    FileRecords). Returns None for any Finding this module doesn't
    recognize, can't safely fix, or whose file content isn't available -
    never a best-effort guess presented as a real diff."""
    if not finding.evidence:
        return None
    rule_id = finding.evidence[0].analyzer.rule_id
    fixer = _FIXERS.get(rule_id)
    if fixer is None:
        return None
    file_path = finding.evidence[0].location.file_path
    content = file_contents.get(file_path)
    if content is None:
        return None
    return fixer(finding, content)


def propose_suggestion(finding: Finding) -> Suggestion | None:
    """For a Finding this module recognizes but deliberately won't
    auto-patch - see this module's docstring for why."""
    if not finding.evidence:
        return None
    rule_id = finding.evidence[0].analyzer.rule_id
    suggester = _SUGGESTERS.get(rule_id)
    return suggester(finding) if suggester else None
