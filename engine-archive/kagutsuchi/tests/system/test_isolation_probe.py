from system.sandbox.isolation_probe import CheckResult, ProbeReport, run_isolation_probe


def test_all_ok_true_when_every_required_check_passes():
    report = ProbeReport(checks=[
        CheckResult("a", True, "", required=True),
        CheckResult("b", True, "", required=True),
        CheckResult("informational", False, "", required=False),
    ])
    assert report.all_ok is True


def test_all_ok_false_when_any_required_check_fails():
    report = ProbeReport(checks=[
        CheckResult("a", True, "", required=True),
        CheckResult("b", False, "", required=True),
    ])
    assert report.all_ok is False


def test_all_ok_false_when_there_are_no_checks_at_all():
    # An empty report must never look "OK" by default -- that would
    # silently claim isolation is possible on evidence of nothing.
    assert ProbeReport(checks=[]).all_ok is False


def test_as_dict_shape():
    report = ProbeReport(checks=[CheckResult("a", True, "detail", required=True)])
    d = report.as_dict()
    assert d["all_ok"] is True
    assert d["checks"] == [{"name": "a", "ok": True, "detail": "detail", "required": True}]
    assert "verdict" in d


def test_run_isolation_probe_returns_a_report_with_the_expected_checks():
    # Runs for real (this is the same probe the live endpoint calls) --
    # not asserting pass/fail (that's host-dependent, the whole point of
    # the probe), just that it runs to completion and reports on every
    # primitive it claims to check, without crashing.
    report = run_isolation_probe()
    names = {c.name for c in report.checks}
    assert any("user_namespace" in n for n in names)
    assert any("network_namespace" in n for n in names)
    assert any("mount_namespace" in n for n in names)
    assert any("pid_namespace" in n for n in names)
    assert any("chroot" in n for n in names)
    assert any("cgroup_delegation" in n for n in names)
    assert isinstance(report.all_ok, bool)
