"""
Third demo, further proving generalization: insecure deserialization
(pickle.loads) -> the SAME system/sandbox, SAME
integration/pipeline.run_full_verification, SAME verification/regression
logic as demo.py and demo_sql.py — zero special-casing.

Requires a reachable Docker daemon, same as the other two demos.

Run with:
    PYTHONPATH=. python3 -m integration.demo_deserialize
"""
from __future__ import annotations

import inspect

from contracts import SecurityFinding, SensitiveOp, Severity
from integration.pipeline import run_full_verification
from system.orchestration import build_runnable_script
from verification.fixtures import insecure_deserialization
from verification.hypothesis.deserialization_fallback import (
    DESERIALIZATION_FALLBACK_HYPOTHESIS,
)


def _build_finding() -> SecurityFinding:
    return SecurityFinding(
        file_path="verification/fixtures/insecure_deserialization.py",
        symbol="vulnerable",
        diff_hunk=inspect.getsource(insecure_deserialization.vulnerable),
        sensitive_op=SensitiveOp.DESERIALIZATION,
        rationale=(
            "pickle.loads() on attacker-controlled bytes — a crafted "
            "__reduce__ method can call any callable with any arguments "
            "during unpickling, not just produce unexpected data."
        ),
        detected_by="ast.pickle.loads",
        severity_hint=Severity.HIGH,
    )


def main() -> None:
    result = run_full_verification(
        vulnerable_code=build_runnable_script(insecure_deserialization, "vulnerable"),
        fixed_code=build_runnable_script(insecure_deserialization, "fixed"),
        finding=_build_finding(),
        fallback=DESERIALIZATION_FALLBACK_HYPOTHESIS,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
