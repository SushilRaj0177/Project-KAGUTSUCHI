import ast

from system.orchestration import build_script_from_source


def test_single_arg_output_unchanged():
    # arg_count defaults to 1 and must reproduce the exact call this
    # harness has always emitted - every existing caller that doesn't
    # pass arg_count depends on this not changing.
    src = "def f(x):\n    pass\n"
    script = build_script_from_source(src, "f")
    assert script == "def f(x):\n    pass\n\nimport sys\nf(sys.argv[1])\n"


def test_multi_arg_unpacks_json_array():
    src = "def f(a, b):\n    pass\n"
    script = build_script_from_source(src, "f", arg_count=2)
    ast.parse(script)
    assert "json.loads(sys.argv[1])" in script
    assert "f(*__kagutsuchi_args__)" in script


def test_multi_arg_script_actually_runs():
    import json
    import subprocess
    import sys

    src = "def f(a, b):\n    print(a + b)\n"
    script = build_script_from_source(src, "f", arg_count=2)
    result = subprocess.run(
        [sys.executable, "-c", script, json.dumps(["hello-", "world"])],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "hello-world"
