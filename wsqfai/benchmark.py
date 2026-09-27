"""
M5 (first slice): benchmark a repository's findings against a reference
corpus instead of reporting them as a lonely, context-free number. This
is WSQF/WSQB's own core idea (Washizaki et al., ICSE 2019: don't invent a
0-100 score, measure real products against the standard's characteristics
and benchmark them against each other - 21 commercial products in that
study) applied to what wsqfai/report.py already produces.

Deliberately a first slice, not the full M5: a real reference corpus (a
curated, versioned set of repositories WSQF/WSQB-style benchmarking would
compare against) doesn't exist yet - the corpus here is whatever list of
repositories the caller supplies. What's real is the comparison
methodology itself: findings normalized per thousand lines of code
(findings-per-KLOC), not a raw count, since a 200,000-line repository with
20 findings is doing far better than a 2,000-line repository with 20
findings, and a raw count alone can't tell the two apart.
"""
from __future__ import annotations

from pydantic import BaseModel

from wsqfai.ingestion.repository import RepositorySnapshot
from wsqfai.report import RepositoryReport, analyze_repository, analyze_snapshot


class CorpusReport(BaseModel):
    reports: list[RepositoryReport]

    def findings_per_kloc_by_characteristic(self) -> dict[str, float]:
        """Findings-per-1000-lines-of-code for each characteristic across
        the whole corpus, weighted by each repo's own line count (summing
        counts and lines separately, not averaging per-repo rates) so one
        huge repository isn't drowned out by many tiny ones, and one tiny
        repository's noisy rate doesn't dominate the corpus baseline."""
        totals: dict[str, int] = {}
        total_lines = 0
        for report in self.reports:
            total_lines += report.total_lines
            for finding in report.findings:
                totals[finding.characteristic.value] = totals.get(finding.characteristic.value, 0) + 1
        if total_lines == 0:
            return {}
        return {characteristic: (count / total_lines) * 1000 for characteristic, count in totals.items()}


def build_corpus(repo_urls: list[str]) -> CorpusReport:
    """Clone and analyze every URL in `repo_urls` (real network clones -
    see wsqfai.ingestion.repository.ingest) and return the combined
    CorpusReport."""
    return CorpusReport(reports=[analyze_repository(url) for url in repo_urls])


def build_corpus_from_snapshots(snapshots: list[RepositorySnapshot]) -> CorpusReport:
    """Same as build_corpus, but from already-ingested snapshots - no
    network access. What every test in this module uses, and what a
    future M5 build would use once a real, cached reference corpus exists
    (re-cloning the same reference repositories on every comparison would
    be wasteful and network-dependent for no reason)."""
    return CorpusReport(reports=[analyze_snapshot(snapshot) for snapshot in snapshots])


def compare_to_corpus(report: RepositoryReport, corpus: CorpusReport) -> dict[str, float | None]:
    """For each Security characteristic present in either `report` or
    `corpus`, this repo's findings-per-KLOC divided by the corpus's own
    rate for that characteristic: 1.0 means exactly average, 2.0 means
    twice as many findings per line as the corpus, 0.0 means none at all
    where the corpus has some. `None` means no comparison is possible -
    either `report` has zero recorded lines, or the corpus itself has zero
    findings for that characteristic (dividing by that zero rate would be
    meaningless, not just an ordinary small number)."""
    if report.total_lines == 0:
        return {}
    corpus_rates = corpus.findings_per_kloc_by_characteristic()

    own_counts: dict[str, int] = {}
    for finding in report.findings:
        own_counts[finding.characteristic.value] = own_counts.get(finding.characteristic.value, 0) + 1
    own_rates = {characteristic: (count / report.total_lines) * 1000 for characteristic, count in own_counts.items()}

    result: dict[str, float | None] = {}
    for characteristic in set(own_rates) | set(corpus_rates):
        base_rate = corpus_rates.get(characteristic)
        if not base_rate:
            result[characteristic] = None
        else:
            result[characteristic] = own_rates.get(characteristic, 0.0) / base_rate
    return result
