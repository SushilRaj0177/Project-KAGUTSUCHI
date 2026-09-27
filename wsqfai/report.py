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
