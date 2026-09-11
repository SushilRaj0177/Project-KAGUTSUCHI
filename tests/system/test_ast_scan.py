from contracts import Severity, SensitiveOp
from system.analysis import LearnedSignature, scan_diff, scan_source


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


def test_scan_diff_only_reports_changed_function():
    old_src = """
def safe_existing(x):
    return x + 1


def to_be_changed(hostname):
    return "unchanged"
"""
    new_src = """
def safe_existing(x):
    return x + 1


def to_be_changed(hostname):
    import os
    os.system("ping -c 1 " + hostname)
"""
    findings = scan_diff(old_src, new_src, "sample.py")
    assert len(findings) == 1
    assert findings[0].symbol == "to_be_changed"


def test_scan_diff_ignores_preexisting_vulnerability():
    # os.system call already existed before the change and didn't move —
    # scan_diff should not re-flag it since it's not part of this diff.
    old_src = """
def already_vulnerable(hostname):
    import os
    os.system("ping -c 1 " + hostname)


def touched(x):
    return x
"""
    new_src = """
def already_vulnerable(hostname):
    import os
    os.system("ping -c 1 " + hostname)


def touched(x):
    return x + 1
"""
    findings = scan_diff(old_src, new_src, "sample.py")
    assert findings == []


def test_diff_hunk_captures_full_function_body():
    src = """
def outer(x):
    import os
    os.system("echo " + str(x))
    return x
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert "def outer(x):" in findings[0].diff_hunk
    assert "return x" in findings[0].diff_hunk


def test_detects_marshal_loads():
    src = """
def load(payload):
    import marshal
    marshal.loads(payload)
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.DESERIALIZATION


def test_detects_os_execv_family():
    src = """
def run(argv):
    import os
    os.execv(argv[0], argv)
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.SUBPROCESS


def test_detects_django_raw_query():
    src = """
def get_user(model, username):
    return model.objects.raw(f"SELECT * FROM users WHERE name = '{username}'")
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.SQL_QUERY
    assert findings[0].detected_by == "ast.sql_injection.django_raw"


def test_no_false_positive_on_django_raw_with_literal_query():
    src = """
def get_users(model):
    return model.objects.raw("SELECT * FROM users")
"""
    findings = scan_source(src, "sample.py")
    assert findings == []


def test_detects_django_extra_where():
    src = """
def get_user(model, username):
    return model.objects.extra(where=[f"name = '{username}'"])
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].detected_by == "ast.sql_injection.django_extra"


def test_detects_yaml_load_without_safe_loader():
    src = """
def load(data):
    import yaml
    return yaml.load(data)
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.DESERIALIZATION
    assert findings[0].detected_by == "ast.deserialization.yaml_load_unsafe"


def test_no_false_positive_on_yaml_load_with_safe_loader():
    src = """
def load(data):
    import yaml
    return yaml.load(data, Loader=yaml.SafeLoader)
"""
    findings = scan_source(src, "sample.py")
    assert findings == []


def test_no_false_positive_on_yaml_safe_load():
    src = """
def load(data):
    import yaml
    return yaml.safe_load(data)
"""
    findings = scan_source(src, "sample.py")
    assert findings == []


def test_detects_flask_render_template_string_ssti():
    src = """
def render(user_input):
    from flask import render_template_string
    return render_template_string(f"Hello {user_input}")
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].detected_by == "ast.ssti.render_template_string"


def test_detects_jinja2_template_render_chain_ssti():
    src = """
def render(user_input):
    from jinja2 import Template
    return Template(f"Hello {user_input}").render()
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].detected_by == "ast.ssti.jinja2_template"


def test_no_false_positive_on_jinja2_template_with_literal_string():
    src = """
def render(name):
    from jinja2 import Template
    return Template("Hello {{ name }}").render(name=name)
"""
    findings = scan_source(src, "sample.py")
    assert findings == []


def test_no_false_positive_on_dangerous_call_with_only_hardcoded_arguments():
    # subprocess.run is a real sink in general, but every argument here is
    # a literal - there's no attacker-influenced data that could ever reach
    # it, unlike the unrelated `pkg_name` parameter this function happens
    # to take. This is the "uninstall.py" shape: a dangerous-looking call
    # that isn't a bug because nothing external ever flows into it.
    src = """
def uninstall(pkg_name=None):
    import subprocess
    subprocess.run(["pip", "uninstall", "-y", "some-fixed-tool"], check=True)
"""
    findings = scan_source(src, "sample.py")
    assert findings == []


def test_flags_dangerous_call_when_parameter_flows_in_via_local_variable():
    # One hop of local assignment between the parameter and the sink -
    # matches insecure_deserialization.py's `raw = base64.b64decode(data);
    # pickle.loads(raw)` shape - should still be flagged.
    src = """
def load(data):
    import pickle
    raw = data
    return pickle.loads(raw)
"""
    findings = scan_source(src, "sample.py")
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.DESERIALIZATION


def test_extra_signatures_are_matched_like_a_builtin_detector():
    # An approved detector proposal (see webapp's detector-proposals
    # review flow) is checked for exactly like a hand-written _SIGNATURES
    # entry - same taint gate, same finding shape.
    src = """
def fetch(url):
    import requests
    return requests.get(url)
"""
    learned = {
        "requests.get": LearnedSignature(
            op=SensitiveOp.NETWORK_EGRESS,
            rationale="requests.get with an attacker-influenced URL is server-side request forgery.",
            detector="learned.ssrf",
            severity=Severity.HIGH,
        )
    }
    findings = scan_source(src, "sample.py", extra_signatures=learned)
    assert len(findings) == 1
    assert findings[0].sensitive_op == SensitiveOp.NETWORK_EGRESS
    assert findings[0].detected_by == "learned.ssrf"
    assert findings[0].severity_hint == Severity.HIGH


def test_extra_signatures_still_require_taint():
    src = """
def fetch():
    import requests
    return requests.get("https://example.com/health")
"""
    learned = {
        "requests.get": LearnedSignature(
            op=SensitiveOp.NETWORK_EGRESS,
            rationale="...",
            detector="learned.ssrf",
            severity=Severity.HIGH,
        )
    }
    findings = scan_source(src, "sample.py", extra_signatures=learned)
    assert findings == []


def test_builtin_signature_wins_over_a_same_named_extra_signature():
    src = """
def run(cmd):
    import os
    os.system(cmd)
"""
    learned = {
        "os.system": LearnedSignature(
            op=SensitiveOp.OTHER, rationale="bogus override", detector="learned.bogus", severity=Severity.LOW
        )
    }
    findings = scan_source(src, "sample.py", extra_signatures=learned)
    assert len(findings) == 1
    assert findings[0].detected_by == "ast.shell_exec.os_system"
    assert findings[0].sensitive_op == SensitiveOp.SHELL_EXEC
