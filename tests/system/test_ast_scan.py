from contracts import SensitiveOp
from system.analysis import scan_source


def test_detects_os_system_command_injection():
    src = """
def run_lookup(hostname):
    import os
    os.system("ping -c 1 " + hostname)
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.SHELL_EXEC
    assert findings[0].symbol == "run_lookup"


def test_detects_subprocess_call():
    src = """
def run(cmd):
    import subprocess
    subprocess.run(cmd, shell=True)
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.SUBPROCESS


def test_detects_eval_and_pickle():
    src = """
def load(payload):
    import pickle
    eval(payload)
    pickle.loads(payload)
"""
    findings = scan_source(src, "sample.py")
    ops = {f.sensitive_op for f in findings}
    assert len(findings) == 2
    assert ops == {SensitiveOp.DESERIALIZATION}


def test_detects_sql_injection_via_fstring():
    src = """
def get_user(conn, username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.SQL_QUERY


def test_no_false_positive_on_parameterized_query():
    src = """
def get_user_safe(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
"""
    findings = scan_source(src, "sample.py")
    assert findings == []


def test_no_false_positive_on_clean_function():
    src = """
def add(a, b):
    return a + b
"""
    findings = scan_source(src, "sample.py")
    assert findings == []


def test_diff_hunk_captures_full_function_body():
    src = """
def outer():
    x = 1
    import os
    os.system("echo " + str(x))
    return x
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert "def outer():" in findings[0].diff_hunk
    assert "return x" in findings[0].diff_hunk
