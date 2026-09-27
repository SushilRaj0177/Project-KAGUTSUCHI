"""Given a SecurityFinding, produce one deterministic AttackHypothesis.

Tries Groq once; on any failure (down, rate-limited, malformed output)
degrades to a hardcoded fallback rather than raising - see
verification/hypothesis/fallback.py (netdiag) and sql_fallback.py (SQL
injection). The fallback is per-fixture, not hardcoded to one vulnerability
class - see COORDINATION.md's "Next milestone: prove this generalizes
beyond one fixture" for why this had to change from a single hardcoded
import once a second fixture existed.
"""

from __future__ import annotations

import uuid

from pydantic import ValidationError

from verification.hypothesis.fallback import NETDIAG_FALLBACK_HYPOTHESIS
from verification.hypothesis.groq_client import GroqUnavailable, generate_hypothesis_json
from verification.models import AttackHypothesis, SecurityFinding, SensitiveOp

# regression/verify.py's _marker_created() only ever checks for this one
# specific path (see COORDINATION.md's "the marker path is hardcoded,
# prompt doesn't know about it" entry). The three hand-built fixtures
# were each deliberately engineered to funnel their exploit into creating
# this file; for arbitrary uploaded code, the model has to be told about
# that convention explicitly, or a real exploit that leaks data via a
# return value/stdout/mutated argument would succeed with nothing for the
# sandbox to observe.
_MARKER_PATH = "/tmp/kagutsuchi_pwned"

# Per-sensitive_op guidance on HOW to reach the marker, mirroring the
# mechanism each hand-built fixture already uses (see
# verification/fixtures/*.py and README.md's "why all three use the same
# observable proof"). Unlisted/unknown sensitive_op values fall back to a
# generic instruction below.
_MECHANISM_HINTS: dict[SensitiveOp, str] = {
    SensitiveOp.SHELL_EXEC: (
        f"Chain a shell metacharacter (`;`, `&&`, `|`, backticks, `$()`, or "
        f"a newline) onto the vulnerable input so an injected `touch "
        f"{_MARKER_PATH}` runs alongside the intended command."
    ),
    SensitiveOp.SUBPROCESS: (
        f"If the call can be made to invoke a shell (`shell=True`) or "
        f"accept attacker-influenced argv, inject or append a command that "
        f"runs `touch {_MARKER_PATH}`."
    ),
    SensitiveOp.SQL_QUERY: (
        f"Close the intended string/query early and chain `ATTACH DATABASE "
        f"'{_MARKER_PATH}' AS pwn; CREATE TABLE pwn.t(x);` (or an "
        f"equivalent DDL/DML that creates a file at that exact path) onto "
        f"it, then comment out or balance whatever trails after your "
        f"injection point."
    ),
    SensitiveOp.DESERIALIZATION: (
        f"Craft a payload (e.g. a pickle stream whose `__reduce__` calls "
        f"`eval` or `exec`) that, once deserialized, runs a command "
        f"equivalent to `touch {_MARKER_PATH}`. Prefer reducing to a "
        f"builtin like `eval`/`exec` rather than a platform-specific "
        f"function reference (e.g. `os.system` directly can pickle under a "
        f"platform-specific module and fail to unpickle elsewhere)."
    ),
    SensitiveOp.FILESYSTEM: (
        f"If the flagged operation's path/filename is attacker-influenced "
        f"(e.g. path traversal), redirect it to write/create "
        f"`{_MARKER_PATH}` instead of, or in addition to, its intended target."
    ),
    SensitiveOp.AUTH_CHANGE: (
        f"If the flagged operation lets an attacker bypass an auth/permission "
        f"check, use the resulting access to perform a further operation "
        f"that creates `{_MARKER_PATH}` as concrete proof of the bypass, "
        f"not just an assertion that access was granted."
    ),
    SensitiveOp.NETWORK_EGRESS: (
        f"If the flagged operation can be redirected to fetch and execute "
        f"attacker-controlled content, use that to run a command "
        f"equivalent to `touch {_MARKER_PATH}`."
    ),
}

_GENERIC_MECHANISM_HINT = (
    f"Adapt whatever mechanism the flagged operation allows so that, if "
    f"the exploit succeeds, it results in the file {_MARKER_PATH} being "
    f"created on disk."
)

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

IMPORTANT - observable proof requirement: the sandbox that runs your \
payload does NOT inspect return values, stdout, or error messages to \
decide whether the exploit worked. The ONLY signal it checks is whether \
the file {marker_path} gets created on disk. Your `payload` MUST be \
engineered so that, if the exploit succeeds, that exact file is created - \
otherwise a real, working exploit will be scored as if it failed. \
{mechanism_hint}

Also include a key "confidence": your own honest estimate, as a float \
between 0 and 1, of the probability that this EXACT payload will \
actually succeed against this exact code (not a generic vulnerability- \
class confidence - specific to this payload and this function). Be \
calibrated, not falsely certain: if you are genuinely unsure whether this \
sink is reachable the way you think, say so with a lower number.

Respond with a single JSON object with exactly these keys:
security_property, attack_vector, payload, expected_if_vulnerable, \
expected_if_safe, confidence. All string values must be plain strings; \
`confidence` must be a plain number. {payload_shape_hint} \
`expected_if_vulnerable` must state that \
{marker_path} is created; `expected_if_safe` must state that it is never \
created.
"""

# {symbol}() takes exactly one argument in every hand-built fixture, so
# `payload` has always just been that one argument's value as a plain
# string. Real-world functions frequently take more than one (this
# harness limitation broke live on PyGoat's log_code()/api_code() -
# see COORDINATION.md) - for those, `payload` is instead a
# JSON-ENCODED ARRAY of that many values, still delivered as a plain
# string field (AttackHypothesis.payload is always a str), which
# system/orchestration/harness.py's build_script_from_source() then
# json.loads()s and unpacks positionally into the call. Only the
# instruction text changes based on arg_count; the JSON schema Groq is
# asked for is identical either way.
_SINGLE_ARG_PAYLOAD_HINT = "`payload` must be a single concrete input, not a description."


def _multi_arg_payload_hint(arg_count: int) -> str:
    return (
        f"This function takes {arg_count} positional arguments, in order. `payload` must be a "
        f"JSON-encoded array (as a string) of exactly {arg_count} concrete argument values, in "
        f"that same order - not a description, and not the array itself, but a STRING containing "
        f"valid JSON like \"[\\\"value1\\\", \\\"value2\\\"]\"."
    )


def _build_prompt(finding: SecurityFinding, arg_count: int = 1) -> str:
    mechanism_hint = _MECHANISM_HINTS.get(finding.sensitive_op, _GENERIC_MECHANISM_HINT)
    payload_shape_hint = (
        _SINGLE_ARG_PAYLOAD_HINT if arg_count == 1 else _multi_arg_payload_hint(arg_count)
    )
    return _PROMPT_TEMPLATE.format(
        sensitive_op=finding.sensitive_op.value,
        symbol=finding.symbol,
        file_path=finding.file_path,
        diff_hunk=finding.diff_hunk,
        rationale=finding.rationale,
        marker_path=_MARKER_PATH,
        mechanism_hint=mechanism_hint,
        payload_shape_hint=payload_shape_hint,
    )


def _hypothesis_from_raw(raw: dict, finding: SecurityFinding, model_id: str) -> AttackHypothesis:
    return AttackHypothesis(
        hypothesis_id=str(uuid.uuid4()),
        finding_id=finding.finding_id,
        security_property=raw["security_property"],
        attack_vector=raw["attack_vector"],
        payload=raw["payload"],
        expected_if_vulnerable=raw["expected_if_vulnerable"],
        expected_if_safe=raw["expected_if_safe"],
        generated_by=model_id,
    )


def generate(
    finding: SecurityFinding,
    model_id: str = "groq:openai/gpt-oss-120b",
    fallback: AttackHypothesis | None = NETDIAG_FALLBACK_HYPOTHESIS,
    *,
    arg_count: int = 1,
) -> AttackHypothesis:
    """`fallback` defaults to the netdiag hypothesis for backward
    compatibility with existing call sites (e.g. integration/pipeline.py's
    single-arg `generate_hypothesis(v_finding)` call). Pass the matching
    per-fixture fallback explicitly for any other fixture, e.g.
    `generate(finding, fallback=SQL_INJECTION_FALLBACK_HYPOTHESIS)` - see
    verification/hypothesis/sql_fallback.py.

    Pass `fallback=None` for arbitrary/unknown code where no fallback is
    safe (a "fallback" for code nobody's ever seen is just a wrong guess
    wearing a confident label) - the original failure (`GroqUnavailable`,
    `KeyError`, etc.) propagates uncaught instead of being swallowed, so
    the caller can surface "couldn't generate an attack right now" rather
    than silently running an unrelated payload.

    `arg_count` defaults to 1, reproducing the exact prompt this has
    always sent. Pass the real value from
    system/orchestration/signature.param_count() for a function taking
    more than one argument - see that module's docstring.
    """
    try:
        raw = generate_hypothesis_json(_build_prompt(finding, arg_count))
        return _hypothesis_from_raw(raw, finding, model_id)
    except (GroqUnavailable, KeyError, TypeError, ValidationError):
        # Covers: API down/rate-limited, malformed JSON (raised as
        # GroqUnavailable by groq_client), valid JSON missing expected
        # keys (KeyError), a non-dict JSON value (TypeError on indexing),
        # and valid-but-wrong-shaped values, e.g. `payload` coming back as
        # a list/object instead of a string (pydantic ValidationError).
        if fallback is None:
            raise
        return fallback.model_copy(update={"finding_id": finding.finding_id})


def generate_with_confidence(
    finding: SecurityFinding,
    model_id: str = "groq:openai/gpt-oss-120b",
    fallback: AttackHypothesis | None = NETDIAG_FALLBACK_HYPOTHESIS,
    *,
    arg_count: int = 1,
) -> tuple[AttackHypothesis, float | None]:
    """Same as generate(), but also returns the model's own stated
    confidence (0-1) that this exact payload will succeed against this
    exact code - see verification/calibration.py, which compares this
    against what the sandbox actually observes (research direction D from
    the original brief: is the model's confidence trustworthy, not just
    its answer?).

    The AttackHypothesis contract itself is untouched (confidence is not
    a contracts/ field - it's verification/-internal calibration data),
    so this doesn't require a contract change to add.

    Returns `(hypothesis, None)` on the fallback path - a hardcoded
    fallback has no live confidence estimate to report, and reporting a
    fake one would corrupt the calibration data it's meant to produce.

    See generate()'s docstring for `arg_count`.
    """
    try:
        raw = generate_hypothesis_json(_build_prompt(finding, arg_count))
        hypothesis = _hypothesis_from_raw(raw, finding, model_id)
        confidence = raw.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            confidence = 0.5  # model omitted/malformed it; don't fabricate false precision
        confidence = max(0.0, min(1.0, float(confidence)))
        return hypothesis, confidence
    except (GroqUnavailable, KeyError, TypeError, ValidationError):
        if fallback is None:
            raise
        return fallback.model_copy(update={"finding_id": finding.finding_id}), None
