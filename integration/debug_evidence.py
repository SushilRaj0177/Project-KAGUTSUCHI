"""
One-off diagnostic: run the netdiag fixture through the real sandbox and
print the FULL before/after evidence (not just the final verdict), so a
surprising verdict can actually be inspected instead of guessed at.

Run with:
    python -m integration.debug_evidence
"""
from __future__ import annotations

import inspect
import json

from contracts import SecurityFinding, SensitiveOp, Severity
from integration.demo import _wrap_module_as_script
from system.orchestration import new_run_id, replay_attack, run_attack
from verification.fixtures import netdiag
from verification.hypothesis.fallback import with_finding_id


def main() -> None:
    finding = SecurityFinding(
        file_path="verification/fixtures/netdiag.py",
        symbol="vulnerable",
        diff_hunk=inspect.getsource(netdiag.vulnerable),
        sensitive_op=SensitiveOp.SHELL_EXEC,
        rationale="debug run",
        detected_by="ast.shell_exec.os_system",
        severity_hint=Severity.HIGH,
    )
    hypothesis = with_finding_id(finding.finding_id)
    run_id = new_run_id()

    print(f"Payload: {hypothesis.payload!r}\n")

    before = run_attack(
        vulnerable_code=_wrap_module_as_script("vulnerable"),
        hypothesis=hypothesis,
        run_id=run_id,
    )
    print("=== BEFORE (vulnerable) ===")
    print(json.dumps(before.model_dump(), indent=2))

    after = replay_attack(
        fixed_code=_wrap_module_as_script("fixed"),
        hypothesis=hypothesis,
        run_id=run_id,
    )
    print("\n=== AFTER (fixed) ===")
    print(json.dumps(after.model_dump(), indent=2))


if __name__ == "__main__":
    main()
