import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from wsqfai.ingestion.repository import (
    CloneFailed,
    InvalidRepoUrl,
    _classify,
    _parse_github_url,
    _snapshot_from_dir,
    ingest,
)


def test_parse_github_url_extracts_owner_and_repo():
    assert _parse_github_url("https://github.com/octocat/Hello-World") == ("octocat", "Hello-World")
    assert _parse_github_url("https://github.com/octocat/Hello-World.git") == ("octocat", "Hello-World")
    assert _parse_github_url("https://github.com/octocat/Hello-World/") == ("octocat", "Hello-World")


def test_parse_github_url_rejects_non_github_urls():
    with pytest.raises(InvalidRepoUrl):
        _parse_github_url("https://gitlab.com/octocat/Hello-World")


def test_classify_maps_extensions_to_languages():
    assert _classify(Path("app.py")) == "Python"
    assert _classify(Path("component.tsx")) == "TypeScript"
    assert _classify(Path("README")) is None


def test_ingest_rejects_invalid_ref():
    with pytest.raises(InvalidRepoUrl):
        ingest("https://github.com/octocat/Hello-World", ref="--upload-pack=evil")


def test_snapshot_from_dir_skips_ignored_directories_and_classifies_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import os\n\ndef f():\n    return 1\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("var x = 1;\n")
    (tmp_path / "README.md").write_text("# hello\n")

    snapshot = _snapshot_from_dir(tmp_path, owner="me", repo="proj", ref=None)
    paths = {f.path for f in snapshot.files}

    assert "src/main.py" in paths
    assert "README.md" in paths
    assert not any(p.startswith("node_modules/") for p in paths)

    summary = snapshot.language_summary()
    assert summary["Python"]["files"] == 1
    assert summary["Python"]["lines"] == 4

    main_py = next(f for f in snapshot.files if f.path == "src/main.py")
    assert main_py.content == "import os\n\ndef f():\n    return 1\n"


def test_unclassified_files_do_not_retain_content(tmp_path):
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    snapshot = _snapshot_from_dir(tmp_path, owner="me", repo="proj", ref=None)
    png = next(f for f in snapshot.files if f.path == "image.png")
    assert png.language is None
    assert png.content is None


def test_snapshot_marks_truncated_when_file_cap_exceeded(tmp_path, monkeypatch):
    import wsqfai.ingestion.repository as repo_mod

    monkeypatch.setattr(repo_mod, "_MAX_FILES", 2)
    for i in range(5):
        (tmp_path / f"f{i}.py").write_text("x = 1\n")

    snapshot = _snapshot_from_dir(tmp_path, owner="me", repo="proj", ref=None)
    assert snapshot.truncated is True
    assert len(snapshot.files) == 2


@pytest.mark.skipif(
    subprocess.run(
        ["git", "ls-remote", "https://github.com/octocat/Hello-World"],
        capture_output=True, timeout=10,
    ).returncode != 0,
    reason="no network access to github.com in this environment",
)
def test_ingest_real_public_repo_end_to_end():
    # Real network call, real clone, real classification - the actual
    # M1 promise: no mocked filesystem, no fixture repo.
    snapshot = ingest("https://github.com/octocat/Hello-World")
    assert snapshot.owner == "octocat"
    assert snapshot.repo == "Hello-World"
    assert any(f.path == "README" for f in snapshot.files)
