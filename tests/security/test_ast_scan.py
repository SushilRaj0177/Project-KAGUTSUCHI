import json

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
    assert observations[0].metadata["shell_true"] == "true"


def test_subprocess_call_without_shell_true_is_not_tagged_shell_true():
    # subprocess.run with argv (no shell=True) execs directly - a generic
    # shell-metacharacter payload wouldn't reach a shell at all here, so
    # this must NOT carry shell_true even though it's still flagged as a
    # sensitive subprocess call.
    src = """
def run(cmd):
    import subprocess
    subprocess.run([cmd])
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["sensitive_op"] == "subprocess"
    assert "shell_true" not in observations[0].metadata


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


def test_single_param_direct_taint_is_recorded_for_simple_functions():
    src = """
def run_lookup(hostname):
    import os
    os.system("ping -c 1 " + hostname)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["single_param_direct_taint"] == "hostname"


def test_single_param_direct_taint_absent_when_taint_flows_through_a_local_variable():
    src = """
def load(data):
    import pickle
    raw = data
    return pickle.loads(raw)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert "single_param_direct_taint" not in observations[0].metadata


def test_single_param_direct_taint_absent_when_taint_reaches_call_via_derived_receiver():
    # Two parameters, but that alone isn't why this is unverifiable: `cursor`
    # is itself derived from `conn` (not a parameter), and it's `cursor` -
    # not `conn` - that the call directly references (as the receiver of
    # .execute), so the taint reaches this call only through that
    # intermediate local. See the multi-parameter tests below for a case
    # with two real parameters that *is* now recorded.
    src = """
def get_user(conn, username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert "single_param_direct_taint" not in observations[0].metadata


def test_direct_taint_param_recorded_for_multi_parameter_function_when_only_one_reaches_the_sink():
    # `verbose` is a real second parameter, but it's never referenced by
    # the os.system call at all - only `hostname` is. This is the widened
    # case: a function can take other parameters now, as long as exactly
    # one of them is the one the dangerous call actually uses.
    src = """
def run_lookup(hostname, verbose):
    import os
    if verbose:
        print("looking up", hostname)
    os.system("ping -c 1 " + hostname)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["single_param_direct_taint"] == "hostname"
    other_params = json.loads(observations[0].metadata["other_params"])
    assert other_params == [["verbose", None]]


def test_other_params_metadata_carries_a_real_default_verbatim():
    # `timeout` has its own default and, unlike `verbose` above, is never
    # referenced by the sink at all - only `hostname` is.
    src = """
def run_lookup(hostname, timeout=5):
    import os
    os.system("ping -c 1 " + hostname)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].metadata["single_param_direct_taint"] == "hostname"
    other_params = json.loads(observations[0].metadata["other_params"])
    assert other_params == [["timeout", "5"]]


def test_direct_taint_param_absent_when_two_real_parameters_both_reach_the_call():
    # Genuinely ambiguous: both `host` and `count` are parameters, and both
    # are referenced directly in the same call - a verifier has no honest
    # way to know which one to inject the payload into, so this stays
    # unrecorded (NOT_APPLICABLE downstream in verify.py), not guessed.
    src = """
def ping(host, count):
    import os
    os.system(f"ping -c {count} {host}")
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert "single_param_direct_taint" not in observations[0].metadata
    assert "other_params" not in observations[0].metadata


def test_direct_taint_param_absent_for_positional_only_parameters():
    # Positional-only params can't be passed by keyword, which is how
    # verify.py's candidate call fills in every parameter - so this stays
    # unsupported even though only one parameter reaches the sink.
    src = """
def run_lookup(hostname, /):
    import os
    os.system("ping -c 1 " + hostname)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert "single_param_direct_taint" not in observations[0].metadata


def test_module_level_imports_are_captured_in_metadata():
    src = """
import os
from pathlib import Path

def run(cmd):
    os.system(cmd)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    imports = observations[0].metadata["module_imports"]
    assert "import os" in imports
    assert "from pathlib import Path" in imports


def test_module_imports_key_absent_when_file_has_no_top_level_imports():
    src = """
def run(cmd):
    import os
    os.system(cmd)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert "module_imports" not in observations[0].metadata


def test_every_observation_has_a_real_source_location_with_line_number():
    src = """
def run(cmd):
    import os
    os.system(cmd)
"""
    observations = scan_source(src, "sample.py")
    assert len(observations) == 1
    assert observations[0].location.start_line == 4
