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
and need object state a static scanner can't fabricate safely. This slice
handles three concrete, mechanically reconstructible shapes, grouped by
what a single generic payload can prove regardless of the function's own
logic:

  - a direct shell-exec call (os.system, os.popen), or subprocess.run/
    Popen/call with an explicit `shell=True` keyword
    (`ast_scan._call_has_shell_true`, recorded as
    `Observation.metadata["shell_true"]`) - a shell-metacharacter payload
    (`; touch <marker>`) proves command injection regardless of the
    function's own base command. Without `shell=True`, subprocess execs
    argv directly with no shell involved at all, so the same payload
    would do nothing - why plain subprocess.* calls are excluded.
  - a direct `eval`/`exec` call - a Python-source payload
    (`__import__('pathlib').Path(<marker>).touch()`) proves arbitrary
    code execution regardless of what the function otherwise does with
    the string, since eval/exec run it as code no matter what.

All three shapes also require: the tainted data reaches the sink directly
from exactly one of the enclosing function's own parameters, with no
intermediate local variable (`ast_scan._direct_taint_param_for_call`,
recorded as `Observation.metadata["single_param_direct_taint"]`) - the
same principle the archived Kagutsuchi engine's netdiag fixture
demonstrated, generalized here to any function of any of these shapes
pulled from any real repository.

**Widened to multi-parameter functions:** the enclosing function no
longer has to take *only* that one parameter - it can take others too, as
long as exactly one of them is the one the dangerous call actually uses
(`ast_scan._callable_positional_params`/`_other_params_metadata`, recorded
as `Observation.metadata["other_params"]`, a JSON list of
`[name, default_source_or_null]` pairs). The candidate call fills every
other parameter in by keyword - its own declared default when it has one
(so a call shaped like the function's real, intended usage), a generic
placeholder string when it doesn't. This is a best-effort reconstruction,
not a claim that the placeholder is semantically valid: if a placeholder
value makes the function raise or take a different branch before ever
reaching the sink, that's a `NOT_REPRODUCED` verdict (an honest false
negative from an imperfect call, not a false claim the function is safe)
- exactly the same "never assert, only prove" discipline this whole module
already applies to a validated-input function that legitimately blocks
the payload. Still excluded, the same as before: positional-only
parameters, `*args`/`**kwargs` (no static way to know what belongs there),
and more than one parameter directly reaching the same call (ambiguous -
which one would the payload go in?).

Everything else - SQL injection, pickle/marshal/yaml deserialization,
SSTI, subprocess.* with no shell=True, a call with more than one parameter
directly reaching the sink, positional-only/*args/**kwargs signatures, or
taint that flows through a local variable - returns
`Verdict.NOT_APPLICABLE`: a real, stated limitation of this slice, not a
silent false negative.
pickle.loads/marshal.loads in particular are a plausible future addition
(a malicious pickle payload can also prove code execution) but need an
actual serialized payload constructed, not a plain argv string, which is
real further work, not attempted here. Reintroducing the archived
hypothesis-generation LLM path (verification/hypothesis/generate.py,
groq_client.py) to widen coverage further is real further M4b work too.
"""
from __future__ import annotations

import json
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

# eval/exec run their argument as Python source no matter what the
# enclosing function otherwise does with it - a plain Python expression
# that touches the marker file proves code execution the same way the
# shell-metacharacter payload proves command injection above. Detector ids
# come from wsqfai.security.ast_scan._SIGNATURES, keyed by the exact
# builtin called - "deserialization" alone isn't specific enough, since it
# also covers pickle.loads/marshal.loads/yaml.load, which take a data blob
# rather than directly executing a source string and so aren't verifiable
# this same way.
_CODE_EXEC_DETECTORS = {"ast.eval", "ast.exec"}
_CODE_EXECUTION_PAYLOAD = "__import__('pathlib').Path('/tmp/wsqfai_pwned').touch()"


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
    if metadata.get("detected_by") in _CODE_EXEC_DETECTORS:
        return True
    sensitive_op = metadata.get("sensitive_op")
    if sensitive_op in _VERIFIABLE_OPS:
        return True
    return sensitive_op in _SHELL_TRUE_VERIFIABLE_OPS and metadata.get("shell_true") == "true"


def _payload_for(metadata: dict[str, str]) -> str:
    if metadata.get("detected_by") in _CODE_EXEC_DETECTORS:
        return _CODE_EXECUTION_PAYLOAD
    return _SHELL_INJECTION_PAYLOAD


_PLACEHOLDER_ARG = "'wsqfai_placeholder'"


def _other_param_kwargs(other_params_json: str | None) -> str:
    """`, name=value, ...` for every parameter besides the directly tainted
    one, so the candidate call matches the real function's arity instead of
    failing with `TypeError: missing N required positional arguments`
    before the sink is ever reached. `other_params_json` is
    `Observation.metadata["other_params"]` (see ast_scan.py's
    `_other_params_metadata`) - a JSON list of `[name, default_source]`
    pairs; `default_source` is the parameter's own declared default,
    reproduced verbatim, or None when it has none. Malformed/missing input
    yields no extra arguments rather than raising - the caller already
    gated on `can_attempt_verification`, so this is defensive, not a path
    expected to matter in practice."""
    if not other_params_json:
        return ""
    try:
        pairs = json.loads(other_params_json)
    except (json.JSONDecodeError, TypeError, ValueError):
        return ""
    return "".join(f", {name}={default if default else _PLACEHOLDER_ARG}" for name, default in pairs)


def build_candidate_script(
    function_source: str,
    symbol: str,
    taint_param: str,
    module_imports: str = "",
    other_params_json: str | None = None,
) -> str:
    """A self-contained script: the source file's own top-level imports
    (a function frequently relies on a name like `os` imported at module
    scope rather than inside itself - the common real-world shape), then
    the observed function's own source, then a call to it with the payload
    passed as `taint_param` and every other parameter filled in by keyword
    (see `_other_param_kwargs`) - by keyword throughout, so parameter order
    never matters and a taint parameter that isn't the function's first
    argument still gets the payload, not whatever positionally happens to
    land there. Only valid to call when `can_attempt_verification` is
    true."""
    imports_block = f"{module_imports}\n\n" if module_imports else ""
    other_args = _other_param_kwargs(other_params_json)
    call = f"{symbol}({taint_param}=sys.argv[1]{other_args})"
    return f"{imports_block}{function_source}\n\nif __name__ == '__main__':\n    import sys\n    {call}\n"


def verify_security_observation(metadata: dict[str, str], *, timeout_s: int = 10) -> VerificationResult:
    """Attempt to actually exploit the sensitive call described by
    `metadata` (an M4a Observation's `.metadata`) in the sandbox, and
    report what really happened. Never raises on candidate misbehavior -
    a candidate that crashes, times out, or does nothing is exactly the
    kind of outcome this is designed to observe safely."""
    if not can_attempt_verification(metadata):
        return VerificationResult(
            verdict=Verdict.NOT_APPLICABLE,
            detail=(
                "This observation isn't one of the shapes this verification slice can safely "
                "and mechanically reconstruct a runnable call for - a single-parameter direct "
                "shell-exec call, a subprocess.run/Popen/call with an explicit shell=True, or a "
                "direct eval/exec call, in each case with no intermediate local variable "
                "between the parameter and the sink. See wsqfai/security/verify.py's module "
                "docstring."
            ),
        )
    function_source = metadata.get("function_source", "")
    symbol = metadata.get("symbol", "")
    taint_param = metadata.get("single_param_direct_taint", "")
    module_imports = metadata.get("module_imports", "")
    other_params_json = metadata.get("other_params")
    is_code_exec = metadata.get("detected_by") in _CODE_EXEC_DETECTORS
    payload_kind = "Python-source" if is_code_exec else "shell-metacharacter"
    candidate = build_candidate_script(function_source, symbol, taint_param, module_imports, other_params_json)
    evidence = run_in_subprocess_sandbox(candidate_code=candidate, payload=_payload_for(metadata), timeout_s=timeout_s)

    if evidence.marker_created:
        return VerificationResult(
            verdict=Verdict.VULNERABLE_CONFIRMED,
            execution_evidence=evidence,
            detail=(
                f"Calling {symbol}() with a {payload_kind} payload actually executed injected "
                "code in the sandbox (marker file created) - proven, not asserted from the "
                "static match alone."
            ),
        )
    return VerificationResult(
        verdict=Verdict.NOT_REPRODUCED,
        execution_evidence=evidence,
        detail=(
            f"Calling {symbol}() with the {payload_kind} payload did NOT execute the injected "
            "code in the sandbox - the static match may be a false positive (e.g. the function "
            "validates or escapes its input before reaching the sink)."
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
    is_code_exec = observation_metadata.get("detected_by") in _CODE_EXEC_DETECTORS
    vuln_label = "code execution" if is_code_exec else "command injection"
    rule_id = "sandbox_verified_code_execution" if is_code_exec else "sandbox_verified_shell_injection"
    return Finding(
        title=f"Proven {vuln_label} in {symbol}()",
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
            analyzer=AnalyzerMetadata(analyzer=_ANALYZER, rule_id=rule_id, confidence=Confidence.HIGH),
        )],
    )
