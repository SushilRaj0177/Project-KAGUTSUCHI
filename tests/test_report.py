import subprocess

import pytest

from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.report import analyze_repository, analyze_snapshot, render_html, render_text


def _py(path: str, content: str) -> FileRecord:
    return FileRecord(path=path, language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)


def test_analyze_snapshot_composes_every_module():
    god_file_content = "\n".join(f"x{i} = {i}" for i in range(1200))
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("src/god.py", god_file_content),
        _py("train.py", "import sklearn\nmodel = sklearn.linear_model.LogisticRegression()\n"),
        _py("app.py", "def run(cmd):\n    import os\n    os.system(cmd)\n"),
        _py("reliability.py", "def f():\n    try:\n        risky()\n    except:\n        pass\n"),
    ])
    report = analyze_snapshot(snapshot)

    assert report.owner == "me"
    assert report.total_files == 4
    assert report.is_ml_repository is True

    characteristics = {f.characteristic.value for f in report.findings}
    assert "maintainability" in characteristics  # god-file + missing versioning (modifiability)
    assert "reliability" in characteristics  # bare except
    assert "security" in characteristics  # app.py's os.system(cmd) sandbox-verified

    assert len(report.security_hypotheses) == 1
    assert report.security_hypotheses[0].metadata["sensitive_op"] == "shell_exec"


def test_sandbox_verified_shell_injection_is_promoted_to_a_critical_finding():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("app.py", "def run(cmd):\n    import os\n    os.system(cmd)\n"),
    ])
    report = analyze_snapshot(snapshot)
    security_findings = [f for f in report.findings if f.characteristic.value == "security"]
    assert len(security_findings) == 1
    assert security_findings[0].severity.value == "critical"
    assert security_findings[0].evidence[0].location.file_path == "app.py"


def test_bare_except_finding_gets_a_real_applyable_fix():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("app.py", "def f():\n    try:\n        risky()\n    except:\n        pass\n"),
    ])
    report = analyze_snapshot(snapshot)
    assert len(report.fixes) == 1
    assert "except Exception:" in report.fixes[0].diff
    assert report.combined_patch() == report.fixes[0].diff


def test_sandbox_confirmed_security_finding_gets_a_suggestion_not_a_fix():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("app.py", "def run(cmd):\n    import os\n    os.system(cmd)\n"),
    ])
    report = analyze_snapshot(snapshot)
    assert report.fixes == []
    assert len(report.suggestions) == 1
    assert "subprocess.run" in report.suggestions[0].guidance


def test_unverifiable_security_hypothesis_stays_a_hypothesis_not_a_finding():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("app.py", "def get_user(conn, username):\n    cursor = conn.cursor()\n    cursor.execute(f\"SELECT * FROM users WHERE name = '{username}'\")\n"),
    ])
    report = analyze_snapshot(snapshot)
    assert len(report.security_hypotheses) == 1
    assert not any(f.characteristic.value == "security" for f in report.findings)


def test_finding_counts_by_severity_and_characteristic():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("app.py", "def f():\n    try:\n        risky()\n    except:\n        pass\n"),
    ])
    report = analyze_snapshot(snapshot)
    by_severity = report.finding_count_by_severity()
    assert by_severity.get("high") == 1
    by_characteristic = report.finding_count_by_characteristic()
    assert by_characteristic.get("reliability") == 1


def test_report_on_empty_repository_has_no_findings_or_hypotheses():
    snapshot = RepositorySnapshot(owner="me", repo="empty", ref=None, files=[])
    report = analyze_snapshot(snapshot)
    assert report.findings == []
    assert report.security_hypotheses == []
    assert report.is_ml_repository is False


def test_render_text_includes_key_sections():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("app.py", "def run(cmd):\n    import os\n    os.system(cmd)\n"),
    ])
    text = render_text(analyze_snapshot(snapshot))
    assert "WSQF-AI report for me/proj" in text
    assert "Security hypotheses" in text
    assert "app.py" in text


def test_report_is_json_serializable():
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[
        _py("app.py", "def run(cmd):\n    import os\n    os.system(cmd)\n"),
    ])
    report = analyze_snapshot(snapshot)
    payload = report.model_dump_json()
    assert '"owner":"me"' in payload or '"owner": "me"' in payload


def test_render_html_is_well_formed_and_escapes_repository_controlled_text():
    malicious_title_content = "def f():\n    try:\n        risky()\n    except:\n        pass\n"
    snapshot = RepositorySnapshot(owner="me", repo="<script>alert(1)</script>", ref=None, files=[
        _py("app.py", malicious_title_content),
    ])
    page = render_html(analyze_snapshot(snapshot))
    assert page.startswith("<!doctype html>")
    assert "</html>" in page
    assert "<script>alert(1)</script>" not in page  # must be escaped, not injected raw
    assert "&lt;script&gt;" in page
    assert "app.py" in page


def test_render_html_on_empty_repository_shows_no_findings_message():
    snapshot = RepositorySnapshot(owner="me", repo="empty", ref=None, files=[])
    page = render_html(analyze_snapshot(snapshot))
    assert "No findings." in page
    assert "No security hypotheses." in page


@pytest.mark.skipif(
    subprocess.run(
        ["git", "ls-remote", "https://github.com/octocat/Hello-World"],
        capture_output=True, timeout=10,
    ).returncode != 0,
    reason="no network access to github.com in this environment",
)
def test_analyze_repository_runs_end_to_end_against_a_real_public_repo():
    report = analyze_repository("https://github.com/octocat/Hello-World")
    assert report.owner == "octocat"
    assert isinstance(render_text(report), str)
