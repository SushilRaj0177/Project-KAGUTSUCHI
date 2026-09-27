from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.measurement.reliability import compute_reliability_findings


def _snapshot(path: str, content: str) -> RepositorySnapshot:
    f = FileRecord(path=path, language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])


def test_bare_except_is_flagged_high_severity():
    content = "def f():\n    try:\n        risky()\n    except:\n        pass\n"
    findings = compute_reliability_findings(_snapshot("app.py", content))
    bare = [f for f in findings if f.evidence[0].analyzer.rule_id == "bare_except"]
    assert len(bare) == 1
    assert bare[0].severity.value == "high"
    assert bare[0].sub_characteristic_key == "fault_tolerance"
    assert bare[0].evidence[0].location.start_line == 4


def test_swallowed_broad_exception_is_flagged_medium_severity():
    content = "def f():\n    try:\n        risky()\n    except Exception:\n        pass\n"
    findings = compute_reliability_findings(_snapshot("app.py", content))
    swallowed = [f for f in findings if f.evidence[0].analyzer.rule_id == "swallowed_broad_exception"]
    assert len(swallowed) == 1
    assert swallowed[0].severity.value == "medium"


def test_broad_exception_that_logs_is_not_flagged():
    content = (
        "import logging\n\n"
        "def f():\n"
        "    try:\n"
        "        risky()\n"
        "    except Exception:\n"
        "        logging.exception('failed')\n"
    )
    assert compute_reliability_findings(_snapshot("app.py", content)) == []


def test_broad_exception_that_reraises_is_not_flagged():
    content = "def f():\n    try:\n        risky()\n    except Exception:\n        raise\n"
    assert compute_reliability_findings(_snapshot("app.py", content)) == []


def test_specific_exception_type_with_pass_is_not_flagged():
    # Narrow, specific exception types being deliberately no-op'd is a
    # common, often-intentional pattern (e.g. suppressing a known-benign
    # FileNotFoundError) - only broad Exception/BaseException is flagged.
    content = "def f():\n    try:\n        risky()\n    except FileNotFoundError:\n        pass\n"
    assert compute_reliability_findings(_snapshot("app.py", content)) == []


def test_file_with_syntax_error_is_skipped_not_crashed():
    content = "def f(:\n    this is not valid python\n"
    assert compute_reliability_findings(_snapshot("broken.py", content)) == []


def test_non_python_files_are_ignored():
    f = FileRecord(path="app.js", language="JavaScript", size_bytes=20, line_count=1, content="try {} catch (e) {}")
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])
    assert compute_reliability_findings(snapshot) == []


def test_file_with_both_patterns_produces_two_findings():
    content = (
        "def f():\n"
        "    try:\n"
        "        a()\n"
        "    except:\n"
        "        pass\n\n"
        "def g():\n"
        "    try:\n"
        "        b()\n"
        "    except Exception:\n"
        "        pass\n"
    )
    findings = compute_reliability_findings(_snapshot("app.py", content))
    assert len(findings) == 2


def test_every_finding_cites_reliability_and_a_real_sub_characteristic():
    from wsqfai.domain.quality_model import QualityCharacteristic, sub_characteristic

    content = "def f():\n    try:\n        a()\n    except:\n        pass\n"
    findings = compute_reliability_findings(_snapshot("app.py", content))
    assert findings
    for finding in findings:
        assert finding.characteristic == QualityCharacteristic.RELIABILITY
        sc = sub_characteristic(finding.sub_characteristic_key)
        assert sc.characteristic == QualityCharacteristic.RELIABILITY
