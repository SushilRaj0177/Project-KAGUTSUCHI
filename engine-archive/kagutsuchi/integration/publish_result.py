"""
Run a real demo fixture end-to-end and publish the REAL result to the
Kagutsuchi web dashboard (webapp/). No sample/fake data is ever sent here
- this only ever posts what the actual pipeline actually produced.

Requires a reachable Docker daemon (same as demo.py/demo_sql.py) and two
environment variables:
  DASHBOARD_URL     e.g. https://kagutsuchi.vercel.app
  DASHBOARD_API_KEY must match the deployed webapp's INGEST_API_KEY

Run with:
    PYTHONPATH=. python -m integration.publish_result demo
    PYTHONPATH=. python -m integration.publish_result demo_sql
"""
from __future__ import annotations

import inspect
import os
import sys
import uuid

import requests

from contracts import SecurityFinding, SensitiveOp, Severity
from integration.pipeline import FullRunBundle, run_full_verification_detailed
from system.orchestration import build_runnable_script
from verification.fixtures import netdiag, sql_injection
from verification.hypothesis.fallback import NETDIAG_FALLBACK_HYPOTHESIS
from verification.hypothesis.sql_fallback import SQL_INJECTION_FALLBACK_HYPOTHESIS


def _netdiag_bundle() -> FullRunBundle:
    finding = SecurityFinding(
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
    return run_full_verification_detailed(
        vulnerable_code=build_runnable_script(netdiag, "vulnerable"),
        fixed_code=build_runnable_script(netdiag, "fixed"),
        finding=finding,
        fallback=NETDIAG_FALLBACK_HYPOTHESIS,
    )


def _sql_injection_bundle() -> FullRunBundle:
    finding = SecurityFinding(
        file_path="verification/fixtures/sql_injection.py",
        symbol="vulnerable",
        diff_hunk=inspect.getsource(sql_injection.vulnerable),
        sensitive_op=SensitiveOp.SQL_QUERY,
        rationale=(
            "executescript() is called with a string-interpolated name — "
            "classic SQL injection sink."
        ),
        detected_by="ast.sql_injection.string_built_query",
        severity_hint=Severity.HIGH,
    )
    return run_full_verification_detailed(
        vulnerable_code=build_runnable_script(sql_injection, "vulnerable"),
        fixed_code=build_runnable_script(sql_injection, "fixed"),
        finding=finding,
        fallback=SQL_INJECTION_FALLBACK_HYPOTHESIS,
    )


_FIXTURES = {
    "demo": ("netdiag", _netdiag_bundle),
    "demo_sql": ("sql_injection", _sql_injection_bundle),
}


def publish(bundle: FullRunBundle, fixture_name: str) -> None:
    dashboard_url = os.environ.get("DASHBOARD_URL")
    api_key = os.environ.get("DASHBOARD_API_KEY")
    if not dashboard_url or not api_key:
        raise SystemExit(
            "Set DASHBOARD_URL and DASHBOARD_API_KEY to publish a result "
            "(see integration/publish_result.py's module docstring)."
        )

    payload = {
        "id": str(uuid.uuid4()),
        "fixture_name": fixture_name,
        "sensitive_op": bundle.finding.sensitive_op.value,
        "finding": bundle.finding.model_dump(mode="json"),
        "hypothesis": bundle.hypothesis.model_dump(mode="json"),
        "before_evidence": bundle.before.model_dump(mode="json"),
        "after_evidence": bundle.after.model_dump(mode="json"),
        "verdict": bundle.result.verdict.value,
        "confidence": bundle.result.confidence,
        "replay_identical": bundle.result.replay_identical,
        "summary": bundle.result.summary,
    }

    response = requests.post(
        f"{dashboard_url.rstrip('/')}/api/runs",
        json=payload,
        headers={"x-api-key": api_key},
        timeout=15,
    )
    response.raise_for_status()
    print(f"Published run {payload['id']} — verdict: {bundle.result.verdict.value}")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in _FIXTURES:
        raise SystemExit(f"Usage: python -m integration.publish_result {{{'|'.join(_FIXTURES)}}}")

    fixture_name, build_bundle = _FIXTURES[sys.argv[1]]
    bundle = build_bundle()
    print(bundle.result.model_dump_json(indent=2))
    publish(bundle, fixture_name)


if __name__ == "__main__":
    main()
