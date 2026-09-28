from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.security.secrets import compute_hardcoded_secret_findings


def _snapshot(path: str, content: str) -> RepositorySnapshot:
    f = FileRecord(path=path, language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])


def test_hardcoded_password_is_flagged():
    content = "password = 'correct-horse-battery-staple'\n"
    findings = compute_hardcoded_secret_findings(_snapshot("app.py", content))
    assert len(findings) == 1
    assert findings[0].sub_characteristic_key == "confidentiality"
    assert findings[0].characteristic.value == "security"
    assert findings[0].severity.value == "high"
    assert findings[0].evidence[0].location.start_line == 1
    assert findings[0].evidence[0].analyzer.rule_id == "hardcoded_credential"


def test_hardcoded_api_key_is_flagged():
    content = "API_KEY = 'sk_live_51H8xyzABCDEFGHIJ'\n"
    findings = compute_hardcoded_secret_findings(_snapshot("app.py", content))
    assert len(findings) == 1


def test_finding_never_leaks_the_actual_secret_value():
    content = "password = 'correct-horse-battery-staple'\n"
    findings = compute_hardcoded_secret_findings(_snapshot("app.py", content))
    assert "correct-horse-battery-staple" not in findings[0].description
    assert "correct-horse-battery-staple" not in findings[0].evidence[0].snippet
    assert "correct-horse-battery-staple" not in findings[0].title


def test_value_read_from_environment_is_not_flagged():
    content = "import os\npassword = os.environ.get('DB_PASSWORD')\n"
    assert compute_hardcoded_secret_findings(_snapshot("app.py", content)) == []


def test_unrelated_variable_name_is_not_flagged():
    content = "key = 'some_dict_key_name'\n"
    assert compute_hardcoded_secret_findings(_snapshot("app.py", content)) == []


def test_short_value_is_not_flagged():
    content = "password = 'abc'\n"
    assert compute_hardcoded_secret_findings(_snapshot("app.py", content)) == []


def test_placeholder_values_are_not_flagged():
    for placeholder in ["changeme", "your_api_key_here", "<insert-secret>", "TODO_FIX_ME_XX"]:
        content = f"secret_key = '{placeholder}'\n"
        assert compute_hardcoded_secret_findings(_snapshot("app.py", content)) == [], placeholder


def test_test_files_are_excluded():
    content = "password = 'correct-horse-battery-staple'\n"
    assert compute_hardcoded_secret_findings(_snapshot("tests/test_app.py", content)) == []


def test_annotated_assignment_is_also_flagged():
    content = "secret_token: str = 'correct-horse-battery-staple'\n"
    findings = compute_hardcoded_secret_findings(_snapshot("app.py", content))
    assert len(findings) == 1


def test_multiple_hardcoded_secrets_in_one_file_get_separate_findings():
    content = (
        "password = 'correct-horse-battery-staple'\n"
        "api_key = 'sk_live_51H8xyzABCDEFGHIJ'\n"
    )
    findings = compute_hardcoded_secret_findings(_snapshot("app.py", content))
    assert len(findings) == 2
    assert {f.evidence[0].location.start_line for f in findings} == {1, 2}


def test_malformed_python_is_skipped_not_crashed():
    assert compute_hardcoded_secret_findings(_snapshot("app.py", "def f(:\n")) == []


def test_non_python_files_are_ignored():
    f = FileRecord(path="notes.md", language="Markdown", size_bytes=10, line_count=1, content="password = 'correct-horse-battery-staple'")
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])
    assert compute_hardcoded_secret_findings(snapshot) == []
