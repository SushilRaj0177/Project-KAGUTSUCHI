"""
The real end-to-end demo: netdiag fixture -> real system/sandbox (Docker)
-> real verification/ hypothesis generation and regression verdict.

Requires a reachable Docker daemon - this repo's dev sessions don't have
one, so this needs to be run wherever the demo actually happens, ahead of
time, to confirm the full loop works before presenting it live.

Run with:
    PYTHONPATH=. python3 -m integration.demo

Falls back to the hardcoded hypothesis automatically if GROQ_API_KEY
isn't set or Groq is unreachable/rate-limited (see
verification/hypothesis/generate.py) - either way this should produce a
VERIFIED_FIXED verdict.
"""
from __future__ import annotations

import inspect

from contracts import SecurityFinding, SensitiveOp, Severity
from integration.pipeline import run_full_verification
from verification.fixtures import netdiag


def _wrap_module_as_script(func_name: str) -> str:
    """Embed the WHOLE netdiag module (not just one function) so
    module-level dependencies - the _HOSTNAME_RE regex, the os/re/subprocess
    imports - are present regardless of which function actually runs."""
    module_source = inspect.getsource(netdiag)
    return f"{module_source}\nimport sys\n{func_name}(sys.argv[1])\n"


def _build_finding() -> SecurityFinding:
    return SecurityFinding(
        file_path="verification/fixtures/netdiag.py",
        symbol="vulnerable",
        diff_hunk=inspect.getsource(netdiag.vulnerable),
        sensitive_op=SensitiveOp.SHELL_EXEC,
        rationale=(
            "os.system runs a string-interpolated host through the shell — "
            "classic command injection sink."
        ),
        detected_by="ast.shell_exec.os_system",
        severity_hint=Severity.HIGH,
    )


def main() -> None:
    result = run_full_verification(
        vulnerable_code=_wrap_module_as_script("vulnerable"),
        fixed_code=_wrap_module_as_script("fixed"),
        finding=_build_finding(),
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
