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
and need object state a static scanner can't fabricate safely. This first
slice handles exactly one concrete, mechanically reconstructible shape:

  - the sensitive operation is a direct shell-exec call (os.system,
    os.popen) - `wsqfai.security.ast_scan._SIGNATURES` entries tagged
    SensitiveOp.SHELL_EXEC
  - the enclosing function takes exactly one parameter, and the tainted
    data reaches the sink directly from that parameter with no
    intermediate local variable (`ast_scan._sole_direct_taint_param`,
    recorded as `Observation.metadata["single_param_direct_taint"]`)

For that shape, verification is mechanical and safe to attempt: any shell
string built by concatenating attacker input is vulnerable to command
chaining (`; <second command>`), independent of what the function's own
base command actually is - the same principle the archived Kagutsuchi
engine's netdiag fixture demonstrated, generalized here from one hardcoded
fixture to any function of this shape pulled from any real repository.

Everything else - SQL injection, deserialization, SSTI, multi-parameter
shell-exec, taint that flows through a local variable - returns
`Verdict.NOT_APPLICABLE`: a real, stated limitation of this slice, not a
silent false negative. Reintroducing the archived hypothesis-generation
LLM path (verification/hypothesis/generate.py, groq_client.py) to widen
this is real further M4b work, not attempted here.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from wsqfai.domain.evidence import AnalyzerMetadata, Confidence, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic, sub_characteristic
from wsqfai.security.sandbox import ExecutionEvidence, run_in_subprocess_sandbox

_ANALYZER = "wsqfai.security.verify"

# Only direct shell-exec sinks generalize to a payload that works
# regardless of the function's own base command - see this module's
# docstring. subprocess.run/Popen/call are NOT included: without knowing
# whether the call site passes shell=True (a keyword argument, not part of
# the call name ast_scan matches on), a generic shell-metacharacter payload
# can't be assumed to reach a shell at all.
_VERIFIABLE_OPS = {"shell_exec"}
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
    matches the one shape this slice can mechanically reconstruct and run
    - see this module's docstring for exactly what that shape is."""
    return metadata.get("sensitive_op") in _VERIFIABLE_OPS and bool(metadata.get("single_param_direct_taint"))


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
                "This observation isn't a direct single-parameter shell-exec call with "
                "no intermediate local variable - the only shape this verification slice "
                "can safely and mechanically reconstruct a runnable call for. See "
                "wsqfai/security/verify.py's module docstring."
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
