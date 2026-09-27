from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.security.scanner import scan_repository_for_security_hypotheses


def _py(path: str, content: str) -> FileRecord:
    return FileRecord(path=path, language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)


def test_scans_every_python_file_with_retained_content():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("safe.py", "def add(a, b):\n    return a + b\n"),
        _py("risky.py", "def run(cmd):\n    import os\n    os.system(cmd)\n"),
    ])
    observations = scan_repository_for_security_hypotheses(snapshot)
    assert len(observations) == 1
    assert observations[0].location.file_path == "risky.py"


def test_ignores_files_without_retained_content_or_wrong_language():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        FileRecord(path="binary.pyc", language="Python", size_bytes=100, line_count=0, content=None),
        FileRecord(path="app.js", language="JavaScript", size_bytes=30, line_count=1, content="os.system(cmd)"),
    ])
    assert scan_repository_for_security_hypotheses(snapshot) == []


def test_empty_repository_produces_no_observations():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[])
    assert scan_repository_for_security_hypotheses(snapshot) == []
