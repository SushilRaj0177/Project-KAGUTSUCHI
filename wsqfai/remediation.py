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
  - `unpinned_dependency_package_json` -> pin to the package's current
                                       latest release on the npm registry,
                                       as a caret range (`^X.Y.Z`) rather
                                       than an exact pin - matching npm's
                                       own convention (`npm install` itself
                                       writes a caret range), unlike the
                                       PyPI fixer above, which follows
                                       Python's opposite convention of an
                                       exact `==` pin
  - `sandbox_verified_shell_injection` -> NOT auto-patched (rewriting a
                                       shell-exec call correctly needs
                                       understanding the intended command,
                                       which this doesn't have) - instead
                                       returns human-actionable guidance
                                       text, not a diff.
  - `swallowed_broad_exception`     -> auto-patched only in the one shape
                                       this can do safely: a handler whose
                                       body is a single bare `pass`, in a
                                       file that already imports `logging`
                                       (this module never adds an import).
                                       Only ever inserts a
                                       `logging.exception(...)` call -
                                       never re-raises, returns, or
                                       otherwise changes control flow -
                                       because whether swallowing was ever
                                       actually intentional is a judgment
                                       call this tool can't make; logging
                                       is the one response that's correct
                                       regardless of that answer. Every
                                       other shape (a multi-statement body,
                                       a body that's just a comment-string,
                                       no `logging` import) falls back to
                                       the guidance text below.

Everything else returns None: a real, stated gap, not a silent no-op.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
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


def npm_registry_latest_version(package_name: str, *, timeout_s: float = 5.0) -> str | None:
    """The current latest release of `package_name` on the npm registry, or
    None if the lookup fails for any reason - mirrors `pypi_latest_version`'s
    same never-raises discipline. Scoped package names (`@scope/name`) need
    their `/` percent-encoded for the registry's URL scheme
    (`@scope%2fname`); `urllib.parse.quote` with `safe=""` does that (and is
    a no-op for an unscoped name, which has nothing to encode)."""
    encoded_name = urllib.parse.quote(package_name, safe="")
    url = f"https://registry.npmjs.org/{encoded_name}/latest"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:  # noqa: S310 - a fixed, hardcoded host
            data = json.loads(response.read())
        version = data.get("version")
        return version if isinstance(version, str) and version else None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return None


# Matches exactly the shape ast_scan.py's _package_json_finding snippet
# always produces: `"name": "spec"`, with no surrounding text - see
# portability.py's _package_json_finding.
_PACKAGE_JSON_SNIPPET_RE = re.compile(r'^"([^"]+)":\s*"([^"]*)"$')
# Matches the corresponding real source line, capturing everything up to
# and including the value's opening quote (group 1, preserved verbatim -
# indentation, the key's own quoting) and everything from the value's
# closing quote onward (group 2, preserved verbatim - a trailing comma or
# not, trailing whitespace) so only the version string itself is replaced.
_PACKAGE_JSON_LINE_RE = re.compile(r'^(\s*"[^"]+"\s*:\s*")[^"]*("\s*,?\s*)$')


def _fix_unpinned_dependency_package_json(
    finding: Finding, file_content: str, *, version_lookup=npm_registry_latest_version
) -> Fix | None:
    evidence = finding.evidence[0]
    lineno = evidence.location.start_line
    if lineno is None:
        return None  # line-recovery failed upstream (see portability.py) - nothing precise to edit
    snippet_match = _PACKAGE_JSON_SNIPPET_RE.match(evidence.snippet.strip())
    if snippet_match is None:
        return None
    package_name = snippet_match.group(1)
    latest = version_lookup(package_name)
    if latest is None:
        return None

    lines = file_content.splitlines(keepends=True)
    if not (1 <= lineno <= len(lines)):
        return None
    raw_line = lines[lineno - 1]
    line_ending = raw_line[len(raw_line.rstrip("\r\n")):]
    line_match = _PACKAGE_JSON_LINE_RE.match(raw_line.rstrip("\r\n"))
    if line_match is None:
        return None  # the line no longer looks like a plain "name": "spec" entry - don't guess
    prefix, suffix = line_match.groups()
    new_lines = list(lines)
    new_lines[lineno - 1] = f"{prefix}^{latest}{suffix}{line_ending}"
    after = "".join(new_lines)
    diff = _unified_diff(evidence.location.file_path, file_content, after)
    if diff is None:
        return None
    return Fix(
        finding_id=finding.finding_id,
        file_path=evidence.location.file_path,
        diff=diff,
        summary=f"Pinned {package_name} to a caret range on its current latest release (^{latest}) from the npm registry.",
        patched_content=after,
    )


# Deliberately narrow: only a plain, unaliased `import logging` at module
# level. An aliased import (`import logging as log`) would need the fix to
# call `log.exception(...)` instead, and `from logging import exception`
# doesn't exist as a free function - rather than special-case every import
# style, anything but the plain form just means "don't auto-fix this one",
# same as every other narrow gate in this module.
_LOGGING_IMPORT_RE = re.compile(r"^import logging\s*$", re.MULTILINE)


def _fix_swallowed_exception(finding: Finding, file_content: str) -> Fix | None:
    evidence = finding.evidence[0]
    body_line = evidence.location.end_line
    if body_line is None:
        return None  # not a single bare `pass` body - see reliability.py's own gating
    if not _LOGGING_IMPORT_RE.search(file_content):
        return None  # never adds an import - only fixes a file that already has one

    lines = file_content.splitlines(keepends=True)
    if not (1 <= body_line <= len(lines)):
        return None
    raw_line = lines[body_line - 1]
    stripped = raw_line.rstrip("\r\n")
    if stripped.strip() != "pass":
        return None  # file changed since the scan ran - don't blindly rewrite an unrelated line
    indent = stripped[: len(stripped) - len(stripped.lstrip())]
    line_ending = raw_line[len(stripped):]
    new_lines = list(lines)
    new_lines[body_line - 1] = f'{indent}logging.exception("Swallowed exception"){line_ending}'
    after = "".join(new_lines)
    diff = _unified_diff(evidence.location.file_path, file_content, after)
    if diff is None:
        return None
    return Fix(
        finding_id=finding.finding_id,
        file_path=evidence.location.file_path,
        diff=diff,
        summary="Replaced a bare 'pass' with logging.exception(...) so the fault is at least recorded, not silently discarded.",
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


def _suggest_swallowed_exception_fix(finding: Finding) -> Suggestion:
    return Suggestion(
        finding_id=finding.finding_id,
        guidance=(
            "Give the handler a real response to the fault instead of a bare 'pass': at minimum "
            "log it (logging.exception(...) inside the except block captures the traceback), and "
            "consider whether the caller needs to know the operation failed at all (re-raise, "
            "return an error value, or degrade to a documented fallback). This isn't auto-applied - "
            "it would need to add a 'logging' import the file may not already have, and whether "
            "swallowing was ever actually intentional here is a judgment call only you can make."
        ),
    )


_FIXERS = {
    "bare_except": _fix_bare_except,
    "unpinned_dependency": _fix_unpinned_dependency,
    "unpinned_dependency_package_json": _fix_unpinned_dependency_package_json,
    "swallowed_broad_exception": _fix_swallowed_exception,
}
_SUGGESTERS = {
    "sandbox_verified_shell_injection": _suggest_shell_injection_fix,
    "swallowed_broad_exception": _suggest_swallowed_exception_fix,
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
