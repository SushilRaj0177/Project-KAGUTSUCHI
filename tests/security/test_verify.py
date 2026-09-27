from wsqfai.security.ast_scan import scan_source
from wsqfai.security.verify import Verdict, can_attempt_verification, promote_to_finding, verify_shell_exec_observation


def test_can_attempt_verification_true_for_single_param_shell_exec():
    src = """
def run_lookup(hostname):
    import os
    os.system("ping -c 1 " + hostname)
"""
    [observation] = scan_source(src, "sample.py")
    assert can_attempt_verification(observation.metadata) is True


def test_can_attempt_verification_false_for_sql_injection():
    src = """
def get_user(conn, username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
"""
    [observation] = scan_source(src, "sample.py")
    assert can_attempt_verification(observation.metadata) is False


def test_end_to_end_scan_then_verify_confirms_a_real_vulnerable_function():
    # Generalizes Kagutsuchi's original hardcoded netdiag fixture: this
    # exact function was never authored for this test suite, it's just a
    # command-injection shape ast_scan already knows to flag, and
    # verification actually runs it in the sandbox rather than trusting
    # the static match.
    src = """
def run_lookup(hostname):
    import os
    os.system("ping -c 1 " + hostname)
"""
    [observation] = scan_source(src, "sample.py")
    result = verify_shell_exec_observation(observation.metadata)
    assert result.verdict == Verdict.VULNERABLE_CONFIRMED
    assert result.execution_evidence is not None
    assert result.execution_evidence.marker_created is True


def test_end_to_end_scan_then_verify_correctly_clears_a_validated_function():
    # Same static shape (os.system with a concatenated hostname) ast_scan
    # flags identically - but this function validates its input first, so
    # the injection payload never reaches the shell. Verification should
    # tell the two apart even though the static match alone can't.
    src = """
import re

def run_lookup_safe(hostname):
    import os
    if not re.fullmatch(r"[a-zA-Z0-9.\\-]+", hostname):
        raise ValueError("invalid host")
    os.system("ping -c 1 " + hostname)
"""
    [observation] = scan_source(src, "sample.py")
    assert can_attempt_verification(observation.metadata) is True  # same static shape
    result = verify_shell_exec_observation(observation.metadata)
    assert result.verdict == Verdict.NOT_REPRODUCED
    assert result.execution_evidence.marker_created is False


def test_verify_works_when_the_import_is_at_module_level_not_inside_the_function():
    # The common real-world shape: `import os` at the top of the file, not
    # inside the vulnerable function itself. Regression test for a real
    # bug this module hit during development - build_candidate_script
    # originally used only the function's own source, so a candidate
    # built from a module-level-import function failed with a bare
    # NameError before the sink was ever reached, and that crash was
    # misread as NOT_REPRODUCED ("safe") instead of "couldn't even run".
    src = """
import os

def ping(host):
    os.system("ping -c 1 " + host)
"""
    [observation] = scan_source(src, "sample.py")
    assert observation.metadata["module_imports"] == "import os"
    result = verify_shell_exec_observation(observation.metadata)
    assert result.verdict == Verdict.VULNERABLE_CONFIRMED
    assert "NameError" not in (result.execution_evidence.stderr or "")


def test_can_attempt_verification_true_for_subprocess_run_shell_true():
    src = """
def run(cmd):
    import subprocess
    subprocess.run(cmd, shell=True)
"""
    [observation] = scan_source(src, "sample.py")
    assert can_attempt_verification(observation.metadata) is True


def test_can_attempt_verification_false_for_subprocess_without_shell_true():
    # Same sensitive_op, but no shell involved - a generic shell-metacharacter
    # payload wouldn't do anything here, so this must stay unverifiable.
    src = """
def run(cmd):
    import subprocess
    subprocess.run([cmd])
"""
    [observation] = scan_source(src, "sample.py")
    assert can_attempt_verification(observation.metadata) is False


def test_end_to_end_scan_then_verify_confirms_subprocess_run_shell_true():
    src = """
def run(cmd):
    import subprocess
    subprocess.run(cmd, shell=True)
"""
    [observation] = scan_source(src, "sample.py")
    result = verify_shell_exec_observation(observation.metadata)
    assert result.verdict == Verdict.VULNERABLE_CONFIRMED
    assert result.execution_evidence.marker_created is True


def test_verify_returns_not_applicable_for_unsupported_shapes():
    src = """
def get_user(conn, username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
"""
    [observation] = scan_source(src, "sample.py")
    result = verify_shell_exec_observation(observation.metadata)
    assert result.verdict == Verdict.NOT_APPLICABLE
    assert result.execution_evidence is None


def test_promote_to_finding_mints_a_finding_only_on_confirmed_verdict():
    src = """
def run_lookup(hostname):
    import os
    os.system("ping -c 1 " + hostname)
"""
    [observation] = scan_source(src, "sample.py")
    confirmed = verify_shell_exec_observation(observation.metadata)
    finding = promote_to_finding(observation.metadata, "sample.py", observation.location.start_line, confirmed)
    assert finding is not None
    assert finding.severity.value == "critical"
    assert finding.sub_characteristic_key == observation.metadata["likely_security_sub_characteristic"]
    assert finding.evidence[0].location.file_path == "sample.py"


def test_promote_to_finding_returns_none_for_not_reproduced():
    src = """
import re

def run_lookup_safe(hostname):
    import os
    if not re.fullmatch(r"[a-zA-Z0-9.\\-]+", hostname):
        raise ValueError("invalid host")
    os.system("ping -c 1 " + hostname)
"""
    [observation] = scan_source(src, "sample.py")
    result = verify_shell_exec_observation(observation.metadata)
    assert promote_to_finding(observation.metadata, "sample.py", observation.location.start_line, result) is None


def test_promote_to_finding_returns_none_for_not_applicable():
    src = """
def get_user(conn, username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
"""
    [observation] = scan_source(src, "sample.py")
    result = verify_shell_exec_observation(observation.metadata)
    assert promote_to_finding(observation.metadata, "sample.py", observation.location.start_line, result) is None


def test_finding_validates_against_the_real_domain_model():
    from wsqfai.domain.quality_model import QualityCharacteristic, sub_characteristic

    src = """
def run_lookup(hostname):
    import os
    os.system("ping -c 1 " + hostname)
"""
    [observation] = scan_source(src, "sample.py")
    result = verify_shell_exec_observation(observation.metadata)
    finding = promote_to_finding(observation.metadata, "sample.py", observation.location.start_line, result)
    assert finding.characteristic == QualityCharacteristic.SECURITY
    sc = sub_characteristic(finding.sub_characteristic_key)
    assert sc.characteristic == QualityCharacteristic.SECURITY
