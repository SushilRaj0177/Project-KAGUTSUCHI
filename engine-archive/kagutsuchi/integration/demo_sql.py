"""
Second demo, proving the pipeline generalizes: the SQL-injection fixture
-> the SAME system/sandbox, SAME integration/pipeline.run_full_verification,
SAME verification/regression logic as demo.py's command-injection run —
zero special-casing anywhere in this file beyond picking the fixture and
its matching fallback hypothesis.

Requires a reachable Docker daemon, same as demo.py.

Run with:
    PYTHONPATH=. python3 -m integration.demo_sql
"""
from __future__ import annotations

import inspect

from contracts import SecurityFinding, SensitiveOp, Severity
from integration.pipeline import run_full_verification
from system.orchestration import build_runnable_script
from verification.fixtures import sql_injection
from verification.hypothesis.sql_fallback import SQL_INJECTION_FALLBACK_HYPOTHESIS


def _build_finding() -> SecurityFinding:
    return SecurityFinding(
        file_path="verification/fixtures/sql_injection.py",
        symbol="vulnerable",
        diff_hunk=inspect.getsource(sql_injection.vulnerable),
        sensitive_op=SensitiveOp.SQL_QUERY,
        rationale=(
            "executescript() is called with a string-interpolated name — "
            "classic SQL injection sink, allows chaining arbitrary "
            "additional SQL statements."
        ),
        detected_by="ast.sql_injection.string_built_query",
        severity_hint=Severity.HIGH,
    )


def main() -> None:
    result = run_full_verification(
        vulnerable_code=build_runnable_script(sql_injection, "vulnerable"),
        fixed_code=build_runnable_script(sql_injection, "fixed"),
        finding=_build_finding(),
        fallback=SQL_INJECTION_FALLBACK_HYPOTHESIS,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
