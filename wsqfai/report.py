"""
The first end-to-end composition of everything built so far: ingest a
repository, run every measurement and security module against it, and
produce one combined report. Every module up to this point
(`wsqfai/measurement/*`, `wsqfai/security/*`) has been proven correct in
isolation via its own tests; this module is what proves the pieces
actually compose into something a person can run against a real
repository and read the output of - the difference between "a set of
passing test suites" and "a working tool".

Deliberately still limited in the same ways its parts are limited (see
each module's own docstring): Maintainability/Reliability/ML-pattern
Findings are real but only cover the sub-characteristics built so far
(M2a/M2b/M3a); most security hypotheses remain unverified static AST
matches, since M4b's sandbox verification only covers one mechanically
reconstructible shape so far (see wsqfai/security/verify.py) - the ones it
can attempt are actually run in the sandbox here, and only a real,
sandbox-confirmed exploit is promoted into `findings` as a Security
Finding. Everything else stays a labeled hypothesis, not silently upgraded.
"""
from __future__ import annotations

import html as _html

from pydantic import BaseModel

from wsqfai.domain.evidence import Finding, Observation
from wsqfai.ingestion.repository import RepositorySnapshot, ingest
from wsqfai.measurement.compatibility import compute_compatibility_findings
from wsqfai.measurement.maintainability import compute_maintainability_findings
from wsqfai.measurement.ml_patterns import compute_ml_pattern_findings, is_ml_repository
from wsqfai.measurement.performance import compute_performance_findings
from wsqfai.measurement.portability import compute_portability_findings
from wsqfai.measurement.reliability import compute_reliability_findings
from wsqfai.measurement.usability import compute_usability_findings
from wsqfai.remediation import Fix, Suggestion, propose_fix, propose_suggestion
from wsqfai.security.scanner import scan_repository_for_security_hypotheses
from wsqfai.security.secrets import compute_hardcoded_secret_findings
from wsqfai.security.verify import can_attempt_verification, promote_to_finding, verify_shell_exec_observation

_SEVERITY_ORDER = ("critical", "high", "medium", "low")


class RepositoryReport(BaseModel):
    owner: str
    repo: str
    ref: str | None
    total_files: int
    total_lines: int
    truncated: bool
    language_summary: dict[str, dict[str, int]]
    is_ml_repository: bool
    findings: list[Finding]
    security_hypotheses: list[Observation]
    fixes: list[Fix]
    suggestions: list[Suggestion]

    def combined_patch(self) -> str:
        """Every proposed Fix's diff, concatenated into one patch file a
        user can `git apply` directly against a clone of the repository -
        the actual "clean it up" deliverable, not just a list of findings."""
        return "".join(fix.diff for fix in self.fixes)

    def finding_count_by_severity(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.findings:
            counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
        return counts

    def finding_count_by_characteristic(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.findings:
            counts[f.characteristic.value] = counts.get(f.characteristic.value, 0) + 1
        return counts


def analyze_snapshot(snapshot: RepositorySnapshot) -> RepositoryReport:
    """Run every measurement/security module built so far against an
    already-ingested RepositorySnapshot. Split from analyze_repository()
    below so tests (and any future caller that already has a snapshot -
    e.g. a benchmark corpus in M5) never need a real network clone."""
    findings: list[Finding] = []
    findings.extend(compute_maintainability_findings(snapshot))
    findings.extend(compute_reliability_findings(snapshot))
    findings.extend(compute_portability_findings(snapshot))
    findings.extend(compute_performance_findings(snapshot))
    findings.extend(compute_compatibility_findings(snapshot))
    findings.extend(compute_usability_findings(snapshot))
    findings.extend(compute_ml_pattern_findings(snapshot))
    findings.extend(compute_hardcoded_secret_findings(snapshot))

    security_hypotheses = scan_repository_for_security_hypotheses(snapshot)
    for observation in security_hypotheses:
        if not can_attempt_verification(observation.metadata):
            continue
        result = verify_shell_exec_observation(observation.metadata)
        start_line = observation.location.start_line if observation.location else None
        file_path = observation.location.file_path if observation.location else "?"
        finding = promote_to_finding(observation.metadata, file_path, start_line, result)
        if finding is not None:
            findings.append(finding)

    file_contents = {f.path: f.content for f in snapshot.files if f.content is not None}
    fixes: list[Fix] = []
    suggestions: list[Suggestion] = []
    for finding in findings:
        fix = propose_fix(finding, file_contents)
        if fix is not None:
            fixes.append(fix)
            continue
        suggestion = propose_suggestion(finding)
        if suggestion is not None:
            suggestions.append(suggestion)

    return RepositoryReport(
        owner=snapshot.owner,
        repo=snapshot.repo,
        ref=snapshot.ref,
        total_files=len(snapshot.files),
        total_lines=snapshot.total_lines,
        truncated=snapshot.truncated,
        language_summary=snapshot.language_summary(),
        is_ml_repository=is_ml_repository(snapshot),
        findings=findings,
        security_hypotheses=security_hypotheses,
        fixes=fixes,
        suggestions=suggestions,
    )


def analyze_repository(repo_url: str, ref: str | None = None) -> RepositoryReport:
    """Clone `repo_url` (real network clone, see wsqfai.ingestion.repository.ingest)
    and analyze it. The only function in this module that touches the
    network - everything else operates on an already-ingested snapshot."""
    return analyze_snapshot(ingest(repo_url, ref=ref))


def render_text(report: RepositoryReport) -> str:
    """A human-readable summary, suitable for printing straight to a
    terminal - the CLI's default output mode (see wsqfai/__main__.py)."""
    ref_suffix = f"@{report.ref}" if report.ref else ""
    lines = [
        f"WSQF-AI report for {report.owner}/{report.repo}{ref_suffix}",
        f"{report.total_files} files, {report.total_lines} lines"
        + (" (file cap reached — results are partial)" if report.truncated else ""),
    ]
    if report.language_summary:
        top = list(report.language_summary.items())[:5]
        lines.append("Top languages: " + ", ".join(f"{lang} ({d['files']} files, {d['lines']} lines)" for lang, d in top))
    lines.append(f"ML-containing repository: {'yes' if report.is_ml_repository else 'no'}")
    lines.append("")

    lines.append(f"Findings: {len(report.findings)}")
    by_severity = report.finding_count_by_severity()
    for severity in _SEVERITY_ORDER:
        if severity in by_severity:
            lines.append(f"  {severity}: {by_severity[severity]}")
    for f in sorted(report.findings, key=lambda x: _SEVERITY_ORDER.index(x.severity.value)):
        location = f.evidence[0].location.file_path if f.evidence else "?"
        lines.append(f"  [{f.severity.value.upper()}] {f.characteristic.value}/{f.sub_characteristic_key}: {f.title} ({location})")
    lines.append("")

    lines.append(f"Security hypotheses (raw static AST matches — a confirmed one is also promoted to a Finding above; see M4b in ROADMAP.md): {len(report.security_hypotheses)}")
    for o in report.security_hypotheses:
        severity_hint = o.metadata.get("severity_hint", "?").upper()
        op = o.metadata.get("sensitive_op", "?")
        loc = f"{o.location.file_path}:{o.location.start_line}" if o.location else "?"
        lines.append(f"  [{severity_hint}] {op}: {o.description} ({loc})")
    lines.append("")

    lines.append(f"Fixes proposed (real diffs — see --patch to get them as an applyable file): {len(report.fixes)}")
    for fix in report.fixes:
        lines.append(f"  {fix.file_path}: {fix.summary}")
    if report.suggestions:
        lines.append(f"Suggestions (not auto-applied — needs human judgment): {len(report.suggestions)}")
        for suggestion in report.suggestions:
            lines.append(f"  {suggestion.guidance}")

    return "\n".join(lines)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>WSQF-AI report: {owner}/{repo}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 880px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
  h1 {{ font-size: 1.4rem; }}
  .subtitle {{ color: #666; margin-top: -0.5rem; }}
  .stats {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin: 1.5rem 0; }}
  .stat {{ border: 1px solid #ddd; border-radius: 8px; padding: 0.75rem 1rem; min-width: 8rem; }}
  .stat .n {{ font-size: 1.5rem; font-weight: 700; display: block; }}
  .stat .l {{ font-size: 0.8rem; color: #666; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0 2rem; }}
  th, td {{ text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #eee; font-size: 0.9rem; }}
  th {{ color: #666; font-weight: 600; }}
  .sev-critical, .sev-high {{ color: #b91c1c; font-weight: 600; }}
  .sev-medium {{ color: #b45309; font-weight: 600; }}
  .sev-low {{ color: #4b5563; }}
  .empty {{ color: #666; font-style: italic; }}
  pre.diff {{ background: #0d1117; color: #c9d1d9; padding: 0.75rem 1rem; border-radius: 8px; overflow-x: auto; font-size: 0.82rem; line-height: 1.4; }}
  pre.diff .add {{ color: #7ee787; }}
  pre.diff .del {{ color: #ffa198; }}
  .fix-summary {{ font-size: 0.85rem; color: #666; margin: 0.5rem 0 0.25rem; }}
  footer {{ margin-top: 2rem; border-top: 1px solid #ddd; padding-top: 1rem; font-size: 0.8rem; color: #666; }}
</style>
</head>
<body>
<h1>WSQF-AI report for {owner}/{repo}{ref_suffix}</h1>
<p class="subtitle">Evidence-based dependability auditing against ISO/IEC 25010/25059 (SQuaRE) — every row below cites a real file, not an LLM's opinion.</p>

<div class="stats">
  <div class="stat"><span class="n">{total_files}</span><span class="l">files scanned</span></div>
  <div class="stat"><span class="n">{total_lines}</span><span class="l">lines</span></div>
  <div class="stat"><span class="n">{finding_count}</span><span class="l">findings</span></div>
  <div class="stat"><span class="n">{hypothesis_count}</span><span class="l">security hypotheses</span></div>
  <div class="stat"><span class="n">{fix_count}</span><span class="l">fixes proposed</span></div>
  <div class="stat"><span class="n">{ml_repo}</span><span class="l">ML-containing</span></div>
</div>

<h2>Findings</h2>
{findings_table}

<h2>Proposed fixes <span style="font-weight:400;font-size:0.7em;color:#666">(real diffs, generated from the repository's own files — get them as one patch with --patch)</span></h2>
{fixes_block}

<h2>Security hypotheses <span style="font-weight:400;font-size:0.7em;color:#666">(raw static matches — a sandbox-confirmed one is also promoted to a Finding above)</span></h2>
{hypotheses_table}

<footer>
Generated by WSQF-AI — an AI-systems extension of Waseda's Software Quality Framework
methodology (Prof. Hironori Washizaki, WSQF/WSQB, ICSE 2019). See ARCHITECTURE.md in the
project repository for the full research grounding.
</footer>
</body>
</html>
"""


def _escape(s: str) -> str:
    return _html.escape(s, quote=True)


def _findings_table_html(report: RepositoryReport) -> str:
    if not report.findings:
        return '<p class="empty">No findings.</p>'
    rows = []
    for f in sorted(report.findings, key=lambda x: _SEVERITY_ORDER.index(x.severity.value)):
        location = f.evidence[0].location.file_path if f.evidence else "?"
        rows.append(
            f"<tr><td class='sev-{f.severity.value}'>{_escape(f.severity.value.upper())}</td>"
            f"<td>{_escape(f.characteristic.value)}/{_escape(f.sub_characteristic_key)}</td>"
            f"<td>{_escape(f.title)}</td><td><code>{_escape(location)}</code></td></tr>"
        )
    return (
        "<table><thead><tr><th>Severity</th><th>Sub-characteristic</th><th>Finding</th><th>Location</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _hypotheses_table_html(report: RepositoryReport) -> str:
    if not report.security_hypotheses:
        return '<p class="empty">No security hypotheses.</p>'
    rows = []
    for o in report.security_hypotheses:
        severity_hint = o.metadata.get("severity_hint", "?")
        op = o.metadata.get("sensitive_op", "?")
        loc = f"{o.location.file_path}:{o.location.start_line}" if o.location else "?"
        rows.append(
            f"<tr><td class='sev-{severity_hint}'>{_escape(severity_hint.upper())}</td>"
            f"<td>{_escape(op)}</td><td>{_escape(o.description)}</td><td><code>{_escape(loc)}</code></td></tr>"
        )
    return (
        "<table><thead><tr><th>Severity</th><th>Op</th><th>Rationale</th><th>Location</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _diff_html(diff_text: str) -> str:
    lines = []
    for line in diff_text.splitlines():
        escaped = _escape(line)
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(f'<span class="add">{escaped}</span>')
        elif line.startswith("-") and not line.startswith("---"):
            lines.append(f'<span class="del">{escaped}</span>')
        else:
            lines.append(escaped)
    return "\n".join(lines)


def _fixes_block_html(report: RepositoryReport) -> str:
    if not report.fixes and not report.suggestions:
        return '<p class="empty">No fixes proposed.</p>'
    blocks = []
    for fix in report.fixes:
        blocks.append(
            f"<p class='fix-summary'><code>{_escape(fix.file_path)}</code> — {_escape(fix.summary)}</p>"
            f"<pre class='diff'>{_diff_html(fix.diff)}</pre>"
        )
    for suggestion in report.suggestions:
        blocks.append(f"<p class='fix-summary'>Suggestion (not auto-applied): {_escape(suggestion.guidance)}</p>")
    return "".join(blocks)


def render_html(report: RepositoryReport) -> str:
    """A self-contained static HTML page (no external assets) - suitable
    for saving to a file and opening directly, or for `--format html`'s
    CLI output. Every value that could contain repository-controlled text
    (a title, a file path, a rationale string) is HTML-escaped before
    interpolation, since this report is meant to be run against arbitrary
    public repositories the tool doesn't control."""
    return _HTML_TEMPLATE.format(
        owner=_escape(report.owner),
        repo=_escape(report.repo),
        ref_suffix=f"@{_escape(report.ref)}" if report.ref else "",
        total_files=report.total_files,
        total_lines=report.total_lines,
        finding_count=len(report.findings),
        hypothesis_count=len(report.security_hypotheses),
        fix_count=len(report.fixes),
        ml_repo="yes" if report.is_ml_repository else "no",
        findings_table=_findings_table_html(report),
        fixes_block=_fixes_block_html(report),
        hypotheses_table=_hypotheses_table_html(report),
    )
