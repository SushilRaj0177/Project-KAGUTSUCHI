import ast

from system.orchestration import build_runnable_script
from verification.fixtures import netdiag


def test_builds_syntactically_valid_script_for_each_function():
    for func_name in ("vulnerable", "fixed"):
        script = build_runnable_script(netdiag, func_name)
        ast.parse(script)  # raises SyntaxError if malformed
        assert f"{func_name}(sys.argv[1])" in script


def test_embeds_module_level_dependencies():
    script = build_runnable_script(netdiag, "fixed")
    # fixed() depends on the module-level _HOSTNAME_RE regex and the re/
    # subprocess imports - both must be present since only the function
    # source alone wouldn't carry them.
    assert "_HOSTNAME_RE" in script
    assert "import re" in script
    assert "import subprocess" in script
