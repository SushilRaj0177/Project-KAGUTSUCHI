"""
M4b: the step that turns an M4a Observation (a static AST pattern match -
a hypothesis) into a wsqfai `Finding` (a claim that a sub-characteristic is
actually at risk) - by attempting the exploit for real in the sandbox
(wsqfai/security/sandbox.py) and minting a Finding only when it works.
This is ARCHITECTURE.md's #1 security design decision made real: "Security
findings must be proven, never asserted from a static match."

Deliberately narrow in what it can attempt, and honest about the rest.
Reconstructing a runnable call for an arbitrary function pulled from an
arbitrary repository is, in general, unsolved: real functions take
multiple arguments, depend on imports and names outside their own body,
and need object state a static scanner can't fabricate safely. This slice handles two concrete, mechanically reconstructible shapes -
both reduce to "a shell definitely sees attacker-influenced input", which
is what makes a single generic payload work regardless of the function's
own base command:

  - a direct shell-exec call (os.system, os.popen) -
    `wsqfai.security.ast_scan._SIGNATURES` entries tagged
    SensitiveOp.SHELL_EXEC
  - subprocess.run/Popen/call with an explicit `shell=True` keyword
    (`ast_scan._call_has_shell_true`, recorded as
    `Observation.metadata["shell_true"]`) - without that keyword,
    subprocess execs argv directly with no shell involved at all, so the
    same shell-metacharacter payload would do nothing, which is exactly
    why plain subprocess.* calls are excluded

Both shapes also require: the enclosing function takes exactly one
parameter, and the tainted data reaches the sink directly from that
parameter with no intermediate local variable
(`ast_scan._sole_direct_taint_param`, recorded as
`Observation.metadata["single_param_direct_taint"]`) - the same principle
the archived Kagutsuchi engine's netdiag fixture demonstrated, generalized
here to any function of either shape pulled from any real repository.

Everything else - SQL injection, deserialization, SSTI, subprocess.* with
no shell=True, multi-parameter calls, taint that flows through a local
variable - returns `Verdict.NOT_APPLICABLE`: a real, stated limitation of
this slice, not a silent false negative. Reintroducing the archived
hypothesis-generation LLM path (verification/hypothesis/generate.py,
groq_client.py) to widen this further is real further M4b work, not
attempted here.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic, sub_characteristic
from wsqfai.security.sandbox import ExecutionEvidence, run_in_subprocess_sandbox

_ANALYZER = "wsqfai.security.verify"

# Direct shell-exec sinks (os.system/os.popen) always generalize to a
# payload that works regardless of the function's own base command.
# subprocess.run/Popen/call only generalize the same way when the call
# site passes shell=True explicitly (checked separately, in
# can_attempt_verification, via metadata["shell_true"]) - without it, a
# generic shell-metacharacter payload can't be assumed to reach a shell.
_VERIFIABLE_OPS = {"shell_exec"}
_SHELL_TRUE_VERIFIABLE_OPS = {"subprocess"}
_SHELL_INJECTION_PAYLOAD = "127.0.0.1; touch /tmp/wsqfai_pwned"


class Verdict(str, Enum):
    VULNERABLE_CONFIRMED = "vulnerable_confirmed"
    NOT_REPRODUCED = "not_reproduced"
    NOT_APPLICABLE = "not_applicable"


class VerificationResult(BaseModel):
    verdict: Verdict
    execution_evidence: ExecutionEvidence | None = None
    detail: str


def can_attempt_verification(metadata: dict[str, str]) -> bool:
    """Whether this Observation's metadata (from wsqfai.security.ast_scan)
    matches one of the shapes this slice can mechanically reconstruct and
    run - see this module's docstring for exactly what those shapes are."""
    if not metadata.get("single_param_direct_taint"):
        return False
    sensitive_op = metadata.get("sensitive_op")
    if sensitive_op in _VERIFIABLE_OPS:
        return True
    return sensitive_op in _SHELL_TRUE_VERIFIABLE_OPS and metadata.get("shell_true") == "true"


def build_candidate_script(function_source: str, symbol: str, module_imports: str = "") -> str:
    """A self-contained script: the source file's own top-level imports
    (a function frequently relies on a name like `os` imported at module
    scope rather than inside itself - the common real-world shape), then
    the observed function's own source, then a call to it with argv[1] as
    its single argument. Only valid to call when `can_attempt_verification`
    is true - the function must take exactly one parameter for this call
    shape to be correct."""
    imports_block = f"{module_imports}\n\n" if module_imports else ""
    return f"{imports_block}{function_source}\n\nif __name__ == '__main__':\n    import sys\n    {symbol}(sys.argv[1])\n"


def verify_shell_exec_observation(metadata: dict[str, str], *, timeout_s: int = 10) -> VerificationResult:
    """Attempt to actually exploit the sensitive call described by
    `metadata` (an M4a Observation's `.metadata`) in the sandbox, and
    report what really happened. Never raises on candidate misbehavior -
    a candidate that crashes, times out, or does nothing is exactly the
    kind of outcome this is designed to observe safely."""
    if not can_attempt_verification(metadata):
        return VerificationResult(
            verdict=Verdict.NOT_APPLICABLE,
            detail=(
                "This observation isn't a single-parameter direct shell-exec call, or a "
                "subprocess.run/Popen/call with an explicit shell=True, with no intermediate "
                "local variable between the parameter and the sink - the only shapes this "
                "verification slice can safely and mechanically reconstruct a runnable call "
                "for. See wsqfai/security/verify.py's module docstring."
            ),
        )
    function_source = metadata.get("function_source", "")
    symbol = metadata.get("symbol", "")
    module_imports = metadata.get("module_imports", "")
    candidate = build_candidate_script(function_source, symbol, module_imports)
    evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload=_SHELL_INJECTION_PAYLOAD, timeout_s=timeout_s)

    if evidence.marker_created:
        return VerificationResult(
            verdict=Verdict.VULNERABLE_CONFIRMED,
            execution_evidence=evidence,
            detail=(
                f"Calling {symbol}() with a shell-metacharacter payload actually executed an "
                "injected second command in the sandbox (marker file created) - proven, not "
                "asserted from the static match alone."
            ),
        )
    return VerificationResult(
        verdict=Verdict.NOT_REPRODUCED,
        execution_evidence=evidence,
        detail=(
            f"Calling {symbol}() with the injection payload did NOT execute the injected command "
            "in the sandbox - the static match may be a false positive (e.g. the function validates "
            "or escapes its input before reaching the shell)."
        ),
    )


def promote_to_finding(
    observation_metadata: dict[str, str],
    file_path: str,
    start_line: int | None,
    verification: VerificationResult,
) -> Finding | None:
    """Build a real Finding from a VULNERABLE_CONFIRMED verification - and
    only that verdict. NOT_REPRODUCED and NOT_APPLICABLE never produce a
    Finding: this function is the one place in the whole pipeline where a
    security claim is allowed to come into existence, and it requires
    actual sandbox proof to do so."""
    if verification.verdict != Verdict.VULNERABLE_CONFIRMED or verification.execution_evidence is None:
        return None
    sub_key = observation_metadata.get("likely_security_sub_characteristic", "integrity")
    symbol = observation_metadata.get("symbol", "?")
    evidence = verification.execution_evidence
    return Finding(
        title=f"Proven command injection in {symbol}()",
        description=(
            f"{verification.detail} Sandbox stdout: {evidence.stdout.strip()!r}, "
            f"exit code {evidence.exit_code}, {evidence.duration_ms}ms. "
            f"Isolation: {'; '.join(evidence.policy_violations)}."
        ),
        characteristic=sub_characteristic(sub_key).characteristic if sub_key else QualityCharacteristic.SECURITY,
        sub_characteristic_key=sub_key,
        severity=Severity.CRITICAL,
        evidence=[Evidence(
            location=SourceLocation(file_path=file_path, start_line=start_line),
            snippet=f"sandbox-verified: marker file created; exit {evidence.exit_code}",
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id="sandbox_verified_shell_injection", confidence=Confidence.HIGH),
        )],
    )
