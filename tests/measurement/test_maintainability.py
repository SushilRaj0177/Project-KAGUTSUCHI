import subprocess

import pytest

from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot, ingest
from wsqfai.measurement.maintainability import compute_maintainability_findings


def _snapshot(*files: FileRecord) -> RepositorySnapshot:
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=list(files))


def _findings_for(snapshot: RepositorySnapshot, sub_key: str):
    return [f for f in compute_maintainability_findings(snapshot) if f.sub_characteristic_key == sub_key]


def test_large_python_file_produces_a_modularity_finding():
    snapshot = _snapshot(
        FileRecord(path="src/god.py", language="Python", size_bytes=40_000, line_count=1200),
        FileRecord(path="src/small.py", language="Python", size_bytes=200, line_count=10),
    )
    modularity = _findings_for(snapshot, "modularity")
    assert len(modularity) == 1
    assert modularity[0].evidence[0].location.file_path == "src/god.py"
    assert modularity[0].severity.value == "medium"


def test_very_large_file_is_a_higher_severity_modularity_finding():
    snapshot = _snapshot(FileRecord(path="src/mega.py", language="Python", size_bytes=100_000, line_count=2500))
    modularity = _findings_for(snapshot, "modularity")
    assert len(modularity) == 1
    assert modularity[0].severity.value == "high"


def test_small_files_produce_no_modularity_finding():
    snapshot = _snapshot(
        FileRecord(path="src/a.py", language="Python", size_bytes=200, line_count=20),
        FileRecord(path="src/b.py", language="Python", size_bytes=300, line_count=30),
    )
    assert _findings_for(snapshot, "modularity") == []


def test_large_non_code_file_is_ignored_for_modularity():
    # A big lockfile or changelog is not evidence of poor modularity.
    snapshot = _snapshot(FileRecord(path="package-lock.json", language="JSON", size_bytes=500_000, line_count=15_000))
    assert _findings_for(snapshot, "modularity") == []


def test_minified_style_file_produces_an_analysability_finding():
    # 50000 bytes over 2 lines => 25000 chars/line average, well past the
    # minified threshold.
    snapshot = _snapshot(FileRecord(path="dist/bundle.js", language="JavaScript", size_bytes=50_000, line_count=2))
    analysability = _findings_for(snapshot, "analysability")
    assert len(analysability) == 1
    assert analysability[0].severity.value == "medium"


def test_normally_formatted_file_produces_no_analysability_finding():
    snapshot = _snapshot(FileRecord(path="src/app.py", language="Python", size_bytes=4_000, line_count=150))
    assert _findings_for(snapshot, "analysability") == []


def test_repo_with_healthy_test_ratio_has_no_testability_finding():
    snapshot = _snapshot(
        *[FileRecord(path=f"src/mod{i}.py", language="Python", size_bytes=500, line_count=25) for i in range(9)],
        FileRecord(path="tests/test_mod0.py", language="Python", size_bytes=500, line_count=25),
    )
    assert _findings_for(snapshot, "testability") == []


def test_repo_with_no_tests_flags_critical_testability():
    snapshot = _snapshot(
        *[FileRecord(path=f"src/mod{i}.py", language="Python", size_bytes=500, line_count=25) for i in range(5)],
    )
    findings = _findings_for(snapshot, "testability")
    assert len(findings) == 1
    assert findings[0].severity.value == "critical"


def test_repo_with_sparse_tests_flags_high_severity_testability():
    snapshot = _snapshot(
        *[FileRecord(path=f"src/mod{i}.py", language="Python", size_bytes=500, line_count=25) for i in range(20)],
        FileRecord(path="tests/test_mod0.py", language="Python", size_bytes=500, line_count=25),
    )
    findings = _findings_for(snapshot, "testability")
    assert len(findings) == 1
    assert findings[0].severity.value == "high"


def test_repo_with_no_code_files_produces_no_testability_finding():
    snapshot = _snapshot(FileRecord(path="README.md", language="Markdown", size_bytes=100, line_count=5))
    assert _findings_for(snapshot, "testability") == []


def test_every_finding_cites_maintainability_and_a_real_sub_characteristic():
    from wsqfai.domain.quality_model import QualityCharacteristic, sub_characteristic

    snapshot = _snapshot(
        FileRecord(path="src/god.py", language="Python", size_bytes=100_000, line_count=2500),
        FileRecord(path="dist/bundle.js", language="JavaScript", size_bytes=50_000, line_count=2),
    )
    findings = compute_maintainability_findings(snapshot)
    assert findings
    for finding in findings:
        assert finding.characteristic == QualityCharacteristic.MAINTAINABILITY
        sc = sub_characteristic(finding.sub_characteristic_key)
        assert sc.characteristic == QualityCharacteristic.MAINTAINABILITY


@pytest.mark.skipif(
    subprocess.run(
        ["git", "ls-remote", "https://github.com/octocat/Hello-World"],
        capture_output=True, timeout=10,
    ).returncode != 0,
    reason="no network access to github.com in this environment",
)
def test_measurement_runs_end_to_end_against_a_real_cloned_repo():
    # Real network clone -> real snapshot -> real measurement, no mocking.
    snapshot = ingest("https://github.com/octocat/Hello-World")
    findings = compute_maintainability_findings(snapshot)
    assert isinstance(findings, list)
