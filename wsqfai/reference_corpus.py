"""
M5b: a real, curated reference corpus for WSQF/WSQB-style benchmarking
(wsqfai/benchmark.py), instead of leaving the corpus as "whatever list of
repositories the caller happens to supply" - M5's own stated limitation
(see benchmark.py's module docstring).

Curation criteria, applied to every entry below:
  - Real, actively-maintained, widely-used open-source Python projects -
    not synthetic fixtures, so the baseline reflects how findings actually
    distribute across code people really run in production.
  - Permissively licensed (BSD/Apache/MIT) - the point of a reference
    corpus is comparing against it, which requires being able to actually
    clone and read it.
  - Deliberately small in count (4) and modest in size individually -
    WSQF/WSQB's own study benchmarked 21 commercial products, but building
    and refreshing this corpus means real `git clone` network calls every
    time it's rebuilt (see `build_reference_corpus`'s caching below); a
    small, well-chosen set that's actually exercised beats a large one
    that's aspirational and never actually run end-to-end.
  - Deliberately diverse in what kind of software each one is, so the
    baseline isn't secretly "the average web framework": a web framework,
    an HTTP client library, a CLI toolkit, and a WSGI server.

This diversity, not the count, is what matters for the comparison in
`wsqfai/benchmark.py.compare_to_corpus` to mean anything - comparing an
arbitrary repository's findings-per-KLOC only against, say, four other web
frameworks would silently bias the baseline toward whatever's typical of
web frameworks specifically.
"""
from __future__ import annotations

from pathlib import Path

from wsqfai.benchmark import CorpusReport, build_corpus

# (repo URL, one-line justification for inclusion - kept alongside the URL
# so the corpus's composition stays auditable, not just a bare list).
REFERENCE_CORPUS: list[tuple[str, str]] = [
    ("https://github.com/pallets/flask", "web framework - BSD-3, widely deployed in production"),
    ("https://github.com/psf/requests", "HTTP client library - Apache-2.0, one of the most-depended-on PyPI packages"),
    ("https://github.com/pallets/click", "CLI toolkit - BSD-3, a different application shape from a web framework"),
    ("https://github.com/benoitc/gunicorn", "WSGI application server - MIT, infrastructure rather than an application"),
]

REFERENCE_CORPUS_URLS: list[str] = [url for url, _ in REFERENCE_CORPUS]


def load_cached_corpus_report(cache_path: Path) -> CorpusReport | None:
    """A previously-saved CorpusReport from `cache_path`, or None if the
    file doesn't exist or doesn't parse as one - never raises, since a
    corrupt or missing cache should just mean "rebuild it", not crash
    whatever's asking for a benchmark comparison."""
    if not cache_path.exists():
        return None
    try:
        return CorpusReport.model_validate_json(cache_path.read_text())
    except (ValueError, OSError):
        return None


def save_corpus_report(report: CorpusReport, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(report.model_dump_json())


def build_reference_corpus(*, cache_path: Path | None = None, force_refresh: bool = False) -> CorpusReport:
    """The curated reference corpus, analyzed and ready to benchmark
    against. Re-cloning and re-analyzing 4 real repositories on every call
    would be slow and needlessly network-dependent for a corpus that only
    changes when REFERENCE_CORPUS itself does - so when `cache_path` is
    given and already holds a valid cached report, this returns it without
    touching the network at all. Pass `force_refresh=True` to rebuild and
    overwrite the cache regardless (e.g. after REFERENCE_CORPUS changes)."""
    if cache_path is not None and not force_refresh:
        cached = load_cached_corpus_report(cache_path)
        if cached is not None:
            return cached

    report = build_corpus(REFERENCE_CORPUS_URLS)
    if cache_path is not None:
        save_corpus_report(report, cache_path)
    return report
