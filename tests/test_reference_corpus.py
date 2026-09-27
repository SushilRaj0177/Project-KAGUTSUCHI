import subprocess

import pytest

from wsqfai.benchmark import build_corpus_from_snapshots
from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.reference_corpus import (
    REFERENCE_CORPUS,
    REFERENCE_CORPUS_URLS,
    build_reference_corpus,
    load_cached_corpus_report,
    save_corpus_report,
)


def _snapshot(owner: str, repo: str) -> RepositorySnapshot:
    content = "def f():\n    try:\n        risky()\n    except:\n        pass\n"
    f = FileRecord(path="app.py", language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)
    return RepositorySnapshot(owner=owner, repo=repo, ref=None, files=[f])


def test_reference_corpus_is_curated_not_empty_and_urls_line_up():
    assert len(REFERENCE_CORPUS) >= 4
    assert REFERENCE_CORPUS_URLS == [url for url, _ in REFERENCE_CORPUS]
    for url, justification in REFERENCE_CORPUS:
        assert url.startswith("https://github.com/")
        assert justification  # every entry is auditable, not a bare URL


def test_reference_corpus_urls_are_unique():
    assert len(REFERENCE_CORPUS_URLS) == len(set(REFERENCE_CORPUS_URLS))


def test_load_cached_corpus_report_returns_none_when_file_missing(tmp_path):
    assert load_cached_corpus_report(tmp_path / "does_not_exist.json") is None


def test_load_cached_corpus_report_returns_none_for_corrupt_file(tmp_path):
    cache_path = tmp_path / "corpus.json"
    cache_path.write_text("not valid json {{{")
    assert load_cached_corpus_report(cache_path) is None


def test_save_then_load_round_trips_a_corpus_report(tmp_path):
    corpus = build_corpus_from_snapshots([_snapshot("me", "one"), _snapshot("me", "two")])
    cache_path = tmp_path / "nested" / "corpus.json"

    save_corpus_report(corpus, cache_path)
    loaded = load_cached_corpus_report(cache_path)

    assert loaded is not None
    assert len(loaded.reports) == 2
    assert loaded.findings_per_kloc_by_characteristic() == corpus.findings_per_kloc_by_characteristic()


def test_build_reference_corpus_uses_cache_without_touching_the_network(tmp_path, monkeypatch):
    cache_path = tmp_path / "corpus.json"
    prebuilt = build_corpus_from_snapshots([_snapshot("me", "cached")])
    save_corpus_report(prebuilt, cache_path)

    def _fail_if_called(urls):
        raise AssertionError("build_reference_corpus should not hit the network when a valid cache exists")

    monkeypatch.setattr("wsqfai.reference_corpus.build_corpus", _fail_if_called)

    result = build_reference_corpus(cache_path=cache_path)
    assert len(result.reports) == 1
    assert result.reports[0].repo == "cached"


def test_build_reference_corpus_force_refresh_bypasses_the_cache(tmp_path, monkeypatch):
    cache_path = tmp_path / "corpus.json"
    stale = build_corpus_from_snapshots([_snapshot("me", "stale")])
    save_corpus_report(stale, cache_path)

    fresh = build_corpus_from_snapshots([_snapshot("me", "fresh")])
    monkeypatch.setattr("wsqfai.reference_corpus.build_corpus", lambda urls: fresh)

    result = build_reference_corpus(cache_path=cache_path, force_refresh=True)
    assert result.reports[0].repo == "fresh"
    # the cache file itself was overwritten with the fresh result
    assert load_cached_corpus_report(cache_path).reports[0].repo == "fresh"


@pytest.mark.skipif(
    subprocess.run(
        ["git", "ls-remote", "https://github.com/pallets/flask"],
        capture_output=True, timeout=10,
    ).returncode != 0,
    reason="no network access to github.com in this environment",
)
def test_build_reference_corpus_runs_end_to_end_against_the_real_curated_repos(tmp_path):
    cache_path = tmp_path / "corpus.json"
    corpus = build_reference_corpus(cache_path=cache_path)
    assert len(corpus.reports) == len(REFERENCE_CORPUS_URLS)
    assert cache_path.exists()
    # a second call reads the cache, so it must return the same shape without a second clone
    cached_again = build_reference_corpus(cache_path=cache_path)
    assert len(cached_again.reports) == len(corpus.reports)
