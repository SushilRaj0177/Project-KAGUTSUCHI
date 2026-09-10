import pytest

from system.orchestration import UnsupportedSignature, param_count


def test_single_arg_function():
    assert param_count("def f(x):\n    pass\n", "f") == 1


def test_multi_arg_function():
    assert param_count("def f(a, b, c):\n    pass\n", "f") == 3


def test_rejects_bound_method():
    with pytest.raises(UnsupportedSignature, match="bound method"):
        param_count("class C:\n    def m(self, x):\n        pass\n", "m")


def test_rejects_classmethod():
    with pytest.raises(UnsupportedSignature, match="bound method"):
        param_count("class C:\n    @classmethod\n    def m(cls, x):\n        pass\n", "m")


def test_rejects_varargs():
    with pytest.raises(UnsupportedSignature, match=r"\*args"):
        param_count("def f(*args):\n    pass\n", "f")


def test_rejects_kwargs():
    with pytest.raises(UnsupportedSignature, match=r"\*\*kwargs"):
        param_count("def f(**kwargs):\n    pass\n", "f")


def test_rejects_required_keyword_only():
    with pytest.raises(UnsupportedSignature, match="keyword-only"):
        param_count("def f(*, required):\n    pass\n", "f")


def test_allows_optional_keyword_only():
    # only REQUIRED kwonly (no default) is unsupported - one with a
    # default can just be left at its default when called positionally.
    assert param_count("def f(a, *, optional=1):\n    pass\n", "f") == 1


def test_rejects_no_params():
    with pytest.raises(UnsupportedSignature, match="no parameters"):
        param_count("def f():\n    pass\n", "f")


def test_rejects_missing_symbol():
    with pytest.raises(UnsupportedSignature, match="not defined"):
        param_count("def f(x):\n    pass\n", "does_not_exist")


def test_async_function_supported():
    assert param_count("async def f(a, b):\n    pass\n", "f") == 2
