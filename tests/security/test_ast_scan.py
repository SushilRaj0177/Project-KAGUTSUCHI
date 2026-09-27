from wsqfai.security.ast_scan import scan_source


def test_detects_os_system_command_injection():
    src = """
def run_lookup(hostname):
    import os
    os.system("ping -c 1 " + hostname)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["sensitive_op"] == "shell_exec"
    assert observations[0].metadata["symbol"] == "run_lookup"
    assert observations[0].location.file_path == "sample.py"


def test_detects_subprocess_call():
    src = """
def run(cmd):
    import subprocess
    subprocess.run(cmd, shell=True)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["sensitive_op"] == "subprocess"


def test_detects_eval_and_pickle():
    src = """
def load(payload):
    import pickle
    eval(payload)
    pickle.loads(payload)
"""
    observations = scan_source(src, "sample.py")
    ops = {o.metadata["sensitive_op"] for o in observations}
    assert len(observations) == 2
    assert ops == {"deserialization"}


def test_detects_sql_injection_via_fstring():
    src = """
def get_user(conn, username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["sensitive_op"] == "sql_query"
    assert observations[0].metadata["likely_security_sub_characteristic"] == "integrity"


def test_no_false_positive_on_parameterized_query():
    src = """
def get_user_safe(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
"""
    assert scan_source(src, "sample.py") == []


def test_no_false_positive_on_clean_function():
    src = """
def add(a, b):
    return a + b
"""
    assert scan_source(src, "sample.py") == []


def test_detects_marshal_loads():
    src = """
def load(payload):
    import marshal
    marshal.loads(payload)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["sensitive_op"] == "deserialization"


def test_detects_os_execv_family():
    src = """
def run(argv):
    import os
    os.execv(argv[0], argv)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["sensitive_op"] == "subprocess"


def test_detects_django_raw_query():
    src = """
def get_user(model, username):
    return model.objects.raw(f"SELECT * FROM users WHERE name = '{username}'")
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["detected_by"] == "ast.sql_injection.django_raw"


def test_no_false_positive_on_django_raw_with_literal_query():
    src = """
def get_users(model):
    return model.objects.raw("SELECT * FROM users")
"""
    assert scan_source(src, "sample.py") == []


def test_detects_django_extra_where():
    src = """
def get_user(model, username):
    return model.objects.extra(where=[f"name = '{username}'"])
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["detected_by"] == "ast.sql_injection.django_extra"


def test_detects_yaml_load_without_safe_loader():
    src = """
def load(data):
    import yaml
    return yaml.load(data)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["detected_by"] == "ast.deserialization.yaml_load_unsafe"


def test_no_false_positive_on_yaml_load_with_safe_loader():
    src = """
def load(data):
    import yaml
    return yaml.load(data, Loader=yaml.SafeLoader)
"""
    assert scan_source(src, "sample.py") == []


def test_no_false_positive_on_yaml_safe_load():
    src = """
def load(data):
    import yaml
    return yaml.safe_load(data)
"""
    assert scan_source(src, "sample.py") == []


def test_detects_flask_render_template_string_ssti():
    src = """
def render(user_input):
    from flask import render_template_string
    return render_template_string(f"Hello {user_input}")
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["detected_by"] == "ast.ssti.render_template_string"


def test_detects_jinja2_template_render_chain_ssti():
    src = """
def render(user_input):
    from jinja2 import Template
    return Template(f"Hello {user_input}").render()
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["detected_by"] == "ast.ssti.jinja2_template"


def test_no_false_positive_on_jinja2_template_with_literal_string():
    src = """
def render(name):
    from jinja2 import Template
    return Template("Hello {{ name }}").render(name=name)
"""
    assert scan_source(src, "sample.py") == []


def test_no_false_positive_on_dangerous_call_with_only_hardcoded_arguments():
    src = """
def uninstall(pkg_name=None):
    import subprocess
    subprocess.run(["pip", "uninstall", "-y", "some-fixed-tool"], check=True)
"""
    assert scan_source(src, "sample.py") == []


def test_flags_dangerous_call_when_parameter_flows_in_via_local_variable():
    src = """
def load(data):
    import pickle
    raw = data
    return pickle.loads(raw)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["sensitive_op"] == "deserialization"


def test_function_source_is_captured_in_metadata():
    src = """
def outer(x):
    import os
    os.system("echo " + str(x))
    return x
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    snippet = observations[0].metadata["function_source"]
    assert "def outer(x):" in snippet
    assert "return x" in snippet


def test_syntax_error_source_is_skipped_not_crashed():
    assert scan_source("def f(:\n  bad\n", "broken.py") == []


def test_every_observation_has_a_real_source_location_with_line_number():
    src = """
def run(cmd):
    import os
    os.system(cmd)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].location.start_line == 4
