from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.measurement.portability import compute_portability_findings


def _file(path: str, content: str) -> RepositorySnapshot:
    f = FileRecord(path=path, language="TOML" if path.endswith(".toml") else None, size_bytes=len(content), line_count=content.count("\n"), content=content)
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])


def test_requirements_txt_with_unpinned_dependency_is_flagged():
    content = "requests\nflask==2.3.0\n"
    findings = compute_portability_findings(_file("requirements.txt", content))
    assert len(findings) == 1
    assert findings[0].sub_characteristic_key == "installability"
    assert "requests" in findings[0].evidence[0].snippet
    assert "flask" not in findings[0].evidence[0].snippet


def test_requirements_txt_with_multiple_unpinned_dependencies_gets_one_finding_each():
    content = "requests\nflask==2.3.0\nnumpy\n"
    findings = compute_portability_findings(_file("requirements.txt", content))
    assert len(findings) == 2
    by_line = {f.evidence[0].location.start_line: f.evidence[0].snippet for f in findings}
    assert by_line == {1: "requests", 3: "numpy"}


def test_fully_pinned_requirements_txt_has_no_finding():
    content = "requests==2.31.0\nflask~=2.3\n"
    assert compute_portability_findings(_file("requirements.txt", content)) == []


def test_requirements_txt_skips_comments_blank_lines_and_options():
    content = "# a comment\n\n-r base.txt\nrequests==2.31.0\n"
    assert compute_portability_findings(_file("requirements.txt", content)) == []


def test_pyproject_toml_with_unpinned_dependency_is_flagged():
    content = (
        "[project]\n"
        'name = "proj"\n'
        'dependencies = ["requests", "flask==2.3.0"]\n'
    )
    findings = compute_portability_findings(_file("pyproject.toml", content))
    assert len(findings) == 1
    assert "requests" in findings[0].evidence[0].snippet


def test_pyproject_toml_fully_pinned_has_no_finding():
    content = (
        "[project]\n"
        'name = "proj"\n'
        'dependencies = ["requests==2.31.0", "flask~=2.3"]\n'
    )
    assert compute_portability_findings(_file("pyproject.toml", content)) == []


def test_pyproject_toml_dependency_with_environment_marker_is_checked_correctly():
    content = (
        "[project]\n"
        'name = "proj"\n'
        'dependencies = ["requests==2.31.0 ; python_version >= \\"3.11\\""]\n'
    )
    assert compute_portability_findings(_file("pyproject.toml", content)) == []


def test_malformed_pyproject_toml_is_skipped_not_crashed():
    assert compute_portability_findings(_file("pyproject.toml", "not valid [[[ toml")) == []


def test_unrelated_files_are_ignored():
    assert compute_portability_findings(_file("README.md", "requests\n")) == []


def test_every_finding_cites_portability_and_a_real_sub_characteristic():
    from wsqfai.domain.quality_model import QualityCharacteristic, sub_characteristic

    findings = compute_portability_findings(_file("requirements.txt", "requests\n"))
    assert findings
    for finding in findings:
        assert finding.characteristic == QualityCharacteristic.PORTABILITY
        sc = sub_characteristic(finding.sub_characteristic_key)
        assert sc.characteristic == QualityCharacteristic.PORTABILITY
