import subprocess

import pytest

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic
from wsqfai.remediation import _fix_unpinned_dependency, propose_fix, propose_suggestion, pypi_latest_version


def _finding(rule_id: str, file_path: str, start_line: int | None, snippet: str) -> Finding:
    return Finding(
        title="t",
        description="d",
        characteristic=QualityCharacteristic.RELIABILITY,
        sub_characteristic_key="fault_tolerance",
        severity=Severity.HIGH,
        evidence=[Evidence(
            location=SourceLocation(file_path=file_path, start_line=start_line),
            snippet=snippet,
            analyzer=AnalyzerMetadata(analyzer="x", rule_id=rule_id, confidence=Confidence.HIGH),
        )],
    )


def test_fixes_a_bare_except_preserving_indentation():
    finding = _finding("bare_except", "app.py", 4, "1 bare except clause(s), first at line 4")
    content = "def f():\n    try:\n        risky()\n    except:\n        pass\n"
    fix = propose_fix(finding, {"app.py": content})
    assert fix is not None
    assert "except Exception:" in fix.diff
    assert "-    except:" in fix.diff
    assert "+    except Exception:" in fix.diff


def test_bare_except_fix_preserves_trailing_comment():
    finding = _finding("bare_except", "app.py", 1, "x")
    content = "except:  # noqa\n"
    fix = propose_fix(finding, {"app.py": content})
    assert fix is not None
    assert "except Exception:  # noqa" in fix.diff


def test_returns_none_when_file_content_is_unavailable():
    finding = _finding("bare_except", "app.py", 4, "x")
    assert propose_fix(finding, {}) is None


def test_returns_none_for_unrecognized_rule_id():
    finding = _finding("god_file_line_count", "app.py", 4, "x")
    assert propose_fix(finding, {"app.py": "x = 1\n"}) is None


def test_returns_none_when_line_number_is_out_of_range():
    finding = _finding("bare_except", "app.py", 999, "x")
    assert propose_fix(finding, {"app.py": "x = 1\n"}) is None


def test_returns_none_when_the_line_no_longer_matches_a_bare_except():
    # File changed since the scan ran - the line at that number isn't a
    # bare except anymore. Must not blindly rewrite an unrelated line.
    finding = _finding("bare_except", "app.py", 1, "x")
    assert propose_fix(finding, {"app.py": "x = 1\n"}) is None


def test_unpinned_dependency_fix_pins_to_the_looked_up_version():
    finding = _finding("unpinned_dependency", "requirements.txt", 2, "requests")
    content = "flask==2.3.0\nrequests\nnumpy==1.26.0\n"
    fix = _fix_unpinned_dependency(finding, content, version_lookup=lambda name: "2.31.0")
    assert fix is not None
    assert "-requests" in fix.diff
    assert "+requests==2.31.0" in fix.diff
    assert "flask==2.3.0" in fix.diff  # untouched lines preserved
    assert fix.patched_content == "flask==2.3.0\nrequests==2.31.0\nnumpy==1.26.0\n"


def test_unpinned_dependency_fix_returns_none_when_lookup_fails():
    finding = _finding("unpinned_dependency", "requirements.txt", 1, "requests")
    fix = _fix_unpinned_dependency(finding, "requests\n", version_lookup=lambda name: None)
    assert fix is None


def test_unpinned_dependency_fix_refuses_names_with_extras_or_markers():
    # "requests[socks]" isn't a bare package name this fixer can safely
    # rewrite as "requests[socks]==X.Y.Z" without checking PyPI's actual
    # extras syntax rules - refuse rather than guess.
    finding = _finding("unpinned_dependency", "requirements.txt", 1, "requests[socks]")
    fix = _fix_unpinned_dependency(finding, "requests[socks]\n", version_lookup=lambda name: "2.31.0")
    assert fix is None


def test_shell_injection_finding_gets_a_suggestion_not_an_auto_fix():
    finding = _finding("sandbox_verified_shell_injection", "app.py", 4, "x")
    assert propose_fix(finding, {"app.py": "x = 1\n"}) is None
    suggestion = propose_suggestion(finding)
    assert suggestion is not None
    assert "subprocess.run" in suggestion.guidance


def test_propose_suggestion_returns_none_for_a_fixable_rule():
    finding = _finding("bare_except", "app.py", 1, "x")
    assert propose_suggestion(finding) is None


def test_swallowed_exception_finding_gets_a_suggestion_not_an_auto_fix():
    finding = _finding("swallowed_broad_exception", "app.py", 4, "x")
    assert propose_fix(finding, {"app.py": "x = 1\n"}) is None
    suggestion = propose_suggestion(finding)
    assert suggestion is not None
    assert "logging.exception" in suggestion.guidance


@pytest.mark.skipif(
    subprocess.run(
        ["python3", "-c", "import urllib.request; urllib.request.urlopen('https://pypi.org', timeout=5)"],
        capture_output=True,
    ).returncode != 0,
    reason="no network access to pypi.org in this environment",
)
def test_pypi_latest_version_looks_up_a_real_package():
    version = pypi_latest_version("requests")
    assert version is not None
    assert version[0].isdigit()


def test_pypi_latest_version_returns_none_for_a_nonexistent_package():
    assert pypi_latest_version("this-package-definitely-does-not-exist-wsqfai-test") is None
