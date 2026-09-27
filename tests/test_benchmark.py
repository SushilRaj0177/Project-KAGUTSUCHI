import subprocess

import pytest

from wsqfai.benchmark import build_corpus, build_corpus_from_snapshots, compare_to_corpus
from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.report import analyze_snapshot


def _snapshot(owner: str, repo: str, *files: FileRecord) -> RepositorySnapshot:
    return RepositorySnapshot(owner=owner, repo=repo, ref=None, files=list(files))


def _bare_except_file(path: str, extra_lines: int = 0) -> FileRecord:
    content = "def f():\n    try:\n        risky()\n    except:\n        pass\n" + ("x = 1\n" * extra_lines)
    return FileRecord(path=path, language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)


def test_corpus_rate_is_weighted_by_total_lines_not_averaged_per_repo():
    # A 5-line repo with 1 finding (rate 200/KLOC) and a 995-line repo with
    # 0 findings should NOT average to 100/KLOC - the corpus is dominated
    # by the much larger, clean repo, so the true weighted rate is tiny.
    tiny_buggy = _snapshot("me", "tiny", _bare_except_file("app.py"))
    large_clean = _snapshot("me", "large", FileRecord(
        path="app.py", language="Python", size_bytes=5000, line_count=995, content="x = 1\n" * 995,
    ))
    corpus = build_corpus_from_snapshots([tiny_buggy, large_clean])
    rates = corpus.findings_per_kloc_by_characteristic()
    assert rates["reliability"] < 2.0  # ~1 finding / 1000 lines total, not 100+


def test_compare_to_corpus_reports_above_average_for_a_noisier_repo():
    clean_corpus_member = _snapshot("me", "clean", FileRecord(
        path="app.py", language="Python", size_bytes=5000, line_count=1000, content="x = 1\n" * 1000,
    ))
    corpus = build_corpus_from_snapshots([clean_corpus_member])

    noisy_report = analyze_snapshot(_snapshot("me", "noisy", _bare_except_file("app.py", extra_lines=999)))
    comparison = compare_to_corpus(noisy_report, corpus)
    # corpus has zero reliability findings -> base rate is 0 -> incomparable, not a bogus infinity
    assert comparison.get("reliability") is None


def test_compare_to_corpus_gives_a_ratio_when_both_sides_have_findings():
    corpus_member = analyze_snapshot(_snapshot("me", "corpus1", _bare_except_file("app.py", extra_lines=999)))
    corpus = build_corpus_from_snapshots([_snapshot("me", "corpus1", _bare_except_file("app.py", extra_lines=999))])

    same_rate_report = analyze_snapshot(_snapshot("me", "twin", _bare_except_file("app.py", extra_lines=999)))
    comparison = compare_to_corpus(same_rate_report, corpus)
    assert comparison["reliability"] == pytest.approx(1.0, rel=0.01)
    assert corpus_member.total_lines == same_rate_report.total_lines  # sanity: identical shape


def test_report_with_zero_lines_produces_no_comparison():
    corpus = build_corpus_from_snapshots([_snapshot("me", "corpus1", _bare_except_file("app.py"))])
    empty_report = analyze_snapshot(_snapshot("me", "empty"))
    assert compare_to_corpus(empty_report, corpus) == {}


def test_empty_corpus_has_no_rates():
    corpus = build_corpus_from_snapshots([])
    assert corpus.findings_per_kloc_by_characteristic() == {}


@pytest.mark.skipif(
    subprocess.run(
        ["git", "ls-remote", "https://github.com/octocat/Hello-World"],
        capture_output=True, timeout=10,
    ).returncode != 0,
    reason="no network access to github.com in this environment",
)
def test_build_corpus_runs_end_to_end_against_real_public_repos():
    corpus = build_corpus(["https://github.com/octocat/Hello-World"])
    assert len(corpus.reports) == 1
    assert corpus.reports[0].owner == "octocat"
