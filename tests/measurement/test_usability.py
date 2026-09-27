from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.measurement.usability import compute_usability_findings


def _file(path: str, content: str | None = "x") -> FileRecord:
    return FileRecord(path=path, language="Python" if path.endswith(".py") else None, size_bytes=10, line_count=1, content=content)


def _snapshot(*files: FileRecord) -> RepositorySnapshot:
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=list(files))


def test_repo_with_no_readme_is_flagged():
    findings = compute_usability_findings(_snapshot(_file("app.py")))
    assert len(findings) == 1
    assert findings[0].sub_characteristic_key == "appropriateness_recognizability"
    assert findings[0].characteristic.value == "usability"
    assert findings[0].evidence[0].analyzer.rule_id == "missing_readme"


def test_repo_with_readme_md_is_not_flagged():
    assert compute_usability_findings(_snapshot(_file("README.md"), _file("app.py"))) == []


def test_repo_with_bare_readme_no_extension_is_not_flagged():
    assert compute_usability_findings(_snapshot(_file("README"), _file("app.py"))) == []


def test_readme_case_insensitive():
    assert compute_usability_findings(_snapshot(_file("readme.MD"), _file("app.py"))) == []


def test_readme_rst_and_txt_are_recognized():
    assert compute_usability_findings(_snapshot(_file("README.rst"))) == []
    assert compute_usability_findings(_snapshot(_file("README.txt"))) == []


def test_readme_not_at_root_does_not_count():
    # A README nested in a subdirectory doesn't serve the same purpose as
    # one at the repository root - a user browsing the repo landing page
    # never sees it.
    findings = compute_usability_findings(_snapshot(_file("docs/README.md"), _file("app.py")))
    assert len(findings) == 1


def test_empty_repository_is_flagged():
    assert len(compute_usability_findings(_snapshot())) == 1
