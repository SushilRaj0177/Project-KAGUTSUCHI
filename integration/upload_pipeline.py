"""
The upload-and-verify pipeline for arbitrary user-submitted code — what
server/main.py calls. Distinct from integration/pipeline.py's
run_full_verification(), which is built for our own trusted fixture
modules (imported Python objects). This one takes plain source TEXT and
never imports/execs it outside the Docker sandbox.

Two real constraints, stated plainly rather than papered over:
1. The target function must take exactly one string argument (the
   attacker-controlled input) - see system/orchestration/harness.py's
   own docstring for why.
2. There is no safe hardcoded fallback if the LLM attack-generation call
   fails, unlike our three known fixtures (which each have a fallback
   hypothesis with a real, correct payload). For arbitrary code, a
   "fallback" would just be a wrong guess wearing a confident label -
   so this raises AttackGenerationUnavailable instead of ever guessing.
"""
from __future__ import annotations

import ast
import uuid
from dataclasses import dataclass

from contracts import AttackHypothesis, ExecutionEvidence, SecurityFinding
from integration.adapters import to_system, to_verification
from system.orchestration import build_script_from_source, new_run_id, replay_attack, run_attack
from verification.hypothesis.groq_client import generate_hypothesis_json
from verification.models import AttackHypothesis as VAttackHypothesis
from verification.models import ExecutionEvidence as VExecutionEvidence
from verification.models import SecurityFinding as VSecurityFinding
from verification.models import VerificationResult
from verification.regression.verify import verify as verify_regression


class AttackGenerationUnavailable(RuntimeError):
    """Raised when the LLM attack-generation call fails and there's no
    safe fallback to fall back to (unlike our known fixtures)."""


class FixProposalUnavailable(RuntimeError):
    """Raised when verification.hypothesis.propose_fix isn't available
    yet, or the LLM's proposed fix fails basic sanity checks (invalid
    Python, wrong function name)."""


@dataclass
class UploadVerificationBundle:
    finding: VSecurityFinding
    hypothesis: VAttackHypothesis
    before: VExecutionEvidence
    fixed_source: str | None
    after: VExecutionEvidence | None
    result: VerificationResult | None
    fix_error: str | None


_PROMPT_TEMPLATE = """You are a security analyst producing exactly ONE concrete, \
deterministic attack hypothesis for the vulnerable code below. Do not fuzz \
or list options - pick the single most direct exploit of the flagged \
sensitive operation.

sensitive_op: {sensitive_op}
symbol: {symbol}
file_path: {file_path}
diff_hunk:
{diff_hunk}

rationale: {rationale}

Your payload MUST, if the exploit succeeds, cause a file at the exact \
path /tmp/kagutsuchi_pwned to be created — this is the single observable \
signal used to score every finding, so route whatever mechanism fits this \
sensitive_op (shell metacharacter chaining, ATTACH DATABASE, a __reduce__ \
that calls eval(...), etc.) toward creating that exact file. If the code \
truly cannot be made to create a file this way, pick the closest \
equivalent side effect and say so plainly in attack_vector.

Respond with a single JSON object with exactly these keys:
security_property, attack_vector, payload, expected_if_vulnerable, \
expected_if_safe. All values must be plain strings. `payload` must be a \
single concrete input, not a description.
"""


def _generate_hypothesis_or_raise(finding: VSecurityFinding) -> VAttackHypothesis:
    prompt = _PROMPT_TEMPLATE.format(
        sensitive_op=finding.sensitive_op.value,
        symbol=finding.symbol,
        file_path=finding.file_path,
        diff_hunk=finding.diff_hunk,
        rationale=finding.rationale,
    )
    try:
        raw = generate_hypothesis_json(prompt)
        return VAttackHypothesis(
            hypothesis_id=str(uuid.uuid4()),
            finding_id=finding.finding_id,
            security_property=raw["security_property"],
            attack_vector=raw["attack_vector"],
            payload=raw["payload"],
            expected_if_vulnerable=raw["expected_if_vulnerable"],
            expected_if_safe=raw["expected_if_safe"],
            generated_by="groq:openai/gpt-oss-120b",
        )
    except Exception as exc:
        raise AttackGenerationUnavailable(
            "Could not generate an attack for this code right now "
            "(LLM unavailable or returned an unusable response). Try again shortly."
        ) from exc


def _validate_fix(fixed_source: str, function_name: str) -> None:
    try:
        tree = ast.parse(fixed_source)
    except SyntaxError as exc:
        raise FixProposalUnavailable(f"Proposed fix is not valid Python: {exc}") from exc
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if function_name not in names:
        raise FixProposalUnavailable(
            f"Proposed fix no longer defines a function named {function_name!r}."
        )


def verify_upload(*, source: str, finding: SecurityFinding) -> UploadVerificationBundle:
    """Detect -> hypothesize -> attack the ORIGINAL uploaded code. If
    that proves it vulnerable, attempt a fix proposal + replay; otherwise
    stop at the before-evidence (nothing to fix if it wasn't exploitable)."""
    v_finding = to_verification(finding, VSecurityFinding)
    v_hypothesis = _generate_hypothesis_or_raise(v_finding)
    s_hypothesis = to_system(v_hypothesis, AttackHypothesis)

    run_id = new_run_id()
    vulnerable_script = build_script_from_source(source, finding.symbol)
    before: ExecutionEvidence = run_attack(
        vulnerable_code=vulnerable_script, hypothesis=s_hypothesis, run_id=run_id
    )
    v_before = to_verification(before, VExecutionEvidence)

    marker_hit = "/tmp/kagutsuchi_pwned" in v_before.filesystem_diff.get("created", [])
    if not marker_hit:
        # Hypothesis didn't pan out against the real code - nothing to
        # propose a fix for. Let the caller report this as-is (this IS a
        # real, honest outcome: FALSE_POSITIVE-shaped, just without a
        # paired "after" run since there's nothing proven to fix).
        return UploadVerificationBundle(
            finding=v_finding,
            hypothesis=v_hypothesis,
            before=v_before,
            fixed_source=None,
            after=None,
            result=None,
            fix_error=None,
        )

    try:
        from verification.hypothesis.propose_fix import propose_fix  # noqa: PLC0415
    except ImportError as exc:
        return UploadVerificationBundle(
            finding=v_finding,
            hypothesis=v_hypothesis,
            before=v_before,
            fixed_source=None,
            after=None,
            result=None,
            fix_error=f"Fix proposal not available yet: {exc}",
        )

    try:
        fixed_source = propose_fix(v_finding, v_hypothesis)
        _validate_fix(fixed_source, finding.symbol)
    except Exception as exc:  # noqa: BLE001 - surface any failure as fix_error, don't crash the request
        return UploadVerificationBundle(
            finding=v_finding,
            hypothesis=v_hypothesis,
            before=v_before,
            fixed_source=None,
            after=None,
            result=None,
            fix_error=str(exc),
        )

    fixed_script = build_script_from_source(fixed_source, finding.symbol)
    after: ExecutionEvidence = replay_attack(
        fixed_code=fixed_script, hypothesis=s_hypothesis, run_id=run_id
    )
    v_after = to_verification(after, VExecutionEvidence)

    result = verify_regression(
        v_hypothesis,
        v_before,
        v_after,
        before_payload=v_hypothesis.payload,
        after_payload=v_hypothesis.payload,
    )
    return UploadVerificationBundle(
        finding=v_finding,
        hypothesis=v_hypothesis,
        before=v_before,
        fixed_source=fixed_source,
        after=v_after,
        result=result,
        fix_error=None,
    )
