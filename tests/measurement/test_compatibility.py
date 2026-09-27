from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.measurement.compatibility import compute_compatibility_findings


def _snapshot(path: str, content: str) -> RepositorySnapshot:
    f = FileRecord(path=path, language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])


def test_hardcoded_port_literal_is_flagged():
    content = "from flask import Flask\napp = Flask(__name__)\napp.run(port=5000)\n"
    findings = compute_compatibility_findings(_snapshot("app.py", content))
    assert len(findings) == 1
    assert findings[0].sub_characteristic_key == "co_existence"
    assert findings[0].characteristic.value == "compatibility"
    assert findings[0].evidence[0].location.start_line == 3
    assert findings[0].evidence[0].analyzer.rule_id == "hardcoded_port"


def test_port_read_from_environment_is_not_flagged():
    content = (
        "import os\n"
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "app.run(port=int(os.environ.get('PORT', 5000)))\n"
    )
    assert compute_compatibility_findings(_snapshot("app.py", content)) == []


def test_port_passed_as_a_variable_is_not_flagged():
    content = "def start(port):\n    app.run(port=port)\n"
    assert compute_compatibility_findings(_snapshot("app.py", content)) == []


def test_unrelated_keyword_arguments_are_not_flagged():
    content = "foo(timeout=5000)\n"
    assert compute_compatibility_findings(_snapshot("app.py", content)) == []


def test_test_files_are_excluded():
    content = "app.run(port=5000)\n"
    findings = compute_compatibility_findings(_snapshot("tests/test_app.py", content))
    assert findings == []


def test_conftest_is_excluded():
    content = "app.run(port=5000)\n"
    findings = compute_compatibility_findings(_snapshot("conftest.py", content))
    assert findings == []


def test_multiple_hardcoded_ports_in_one_file_get_one_finding():
    content = "app.run(port=5000)\nuvicorn.run(app, port=8000)\n"
    findings = compute_compatibility_findings(_snapshot("app.py", content))
    assert len(findings) == 1
    assert "2 call(s)" in findings[0].description
    assert findings[0].evidence[0].location.start_line == 1


def test_malformed_python_is_skipped_not_crashed():
    assert compute_compatibility_findings(_snapshot("app.py", "def f(:\n")) == []


def test_non_python_files_are_ignored():
    f = FileRecord(path="notes.md", language="Markdown", size_bytes=10, line_count=1, content="port=5000")
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])
    assert compute_compatibility_findings(snapshot) == []
