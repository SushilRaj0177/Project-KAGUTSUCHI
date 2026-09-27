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
(M2a/M2b/M3a); security hypotheses are unverified static AST matches, not
sandbox-proven Findings, until M4b exists.
"""
from __future__ import annotations

import html as _html

from pydantic import BaseModel

from wsqfai.domain.evidence import Finding, Observation
from wsqfai.ingestion.repository import RepositorySnapshot, ingest
from wsqfai.measurement.maintainability import compute_maintainability_findings
from wsqfai.measurement.ml_patterns import compute_ml_pattern_findings, is_ml_repository
from wsqfai.measurement.reliability import compute_reliability_findings
from wsqfai.security.scanner import scan_repository_for_security_hypotheses

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
    findings.extend(compute_ml_pattern_findings(snapshot))
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
        security_hypotheses=scan_repository_for_security_hypotheses(snapshot),
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

    lines.append(f"Security hypotheses (unverified static AST match, not sandbox-proven — see M4b in ROADMAP.md): {len(report.security_hypotheses)}")
    for o in report.security_hypotheses:
        severity_hint = o.metadata.get("severity_hint", "?").upper()
        op = o.metadata.get("sensitive_op", "?")
        loc = f"{o.location.file_path}:{o.location.start_line}" if o.location else "?"
        lines.append(f"  [{severity_hint}] {op}: {o.description} ({loc})")

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
  <div class="stat"><span class="n">{ml_repo}</span><span class="l">ML-containing</span></div>
</div>

<h2>Findings</h2>
{findings_table}

<h2>Security hypotheses <span style="font-weight:400;font-size:0.7em;color:#666">(unverified static AST match, not sandbox-proven)</span></h2>
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
        ml_repo="yes" if report.is_ml_repository else "no",
        findings_table=_findings_table_html(report),
        hypotheses_table=_hypotheses_table_html(report),
    )
