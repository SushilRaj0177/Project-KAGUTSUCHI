from __future__ import annotations

from wsqfai.security.sandbox import run_in_subprocess_sandbox


def test_runs_candidate_script_and_captures_stdout():
    evidence = run_in_subprocess_sandbox(candidate_code="print('hi')", payload="x")
    assert evidence.exit_code == 0
    assert evidence.stdout.strip() == "hi"


def test_payload_is_passed_as_argv1():
    candidate = "import sys\nprint(sys.argv[1])\n"
    evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload="hello-payload")
    assert evidence.stdout.strip() == "hello-payload"


def test_uncaught_exception_is_reported_as_nonzero_exit_not_a_crash():
    evidence = run_in_subprocess_sandbox(candidate_code="raise ValueError('boom')", payload="x")
    assert evidence.exit_code != 0
    assert "boom" in evidence.stderr


def test_marker_file_creation_is_detected():
    candidate = "from pathlib import Path\nPath('/tmp/wsqfai_pwned').write_text('proof')\n"
    evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload="x")
    assert evidence.marker_created is True


def test_marker_file_is_cleared_between_runs():
    candidate_writes = "from pathlib import Path\nPath('/tmp/wsqfai_pwned').write_text('proof')\n"
    first = run_in_subprocess_sandbox(candidate_code=candidate_writes, payload="x")
    assert first.marker_created is True
    second = run_in_subprocess_sandbox(candidate_code="print('clean')", payload="x")
    assert second.marker_created is False


def test_infinite_loop_is_killed_by_timeout():
    evidence = run_in_subprocess_sandbox(candidate_code="while True:\n    pass\n", payload="x", timeout_s=2)
    assert "timed out" in evidence.stderr


def test_secrets_in_the_calling_process_environment_are_not_inherited():
    import os

    os.environ["WSQFAI_TEST_SECRET"] = "super-secret-value"
    try:
        candidate = "import os\nprint(os.environ.get('WSQFAI_TEST_SECRET', 'NOT_PRESENT'))\n"
        evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload="x")
        assert evidence.stdout.strip() == "NOT_PRESENT"
    finally:
        del os.environ["WSQFAI_TEST_SECRET"]


def test_policy_violations_always_discloses_isolation_level():
    evidence = run_in_subprocess_sandbox(candidate_code="print('hi')", payload="x")
    assert evidence.policy_violations  # never silently claims full isolation
