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

Respond with a single JSON object with exactly these keys:
security_property, attack_vector, payload, expected_if_vulnerable, \
expected_if_safe. All values must be plain strings. `payload` must be a \
single concrete input, not a description. `expected_if_vulnerable` must \
state that {marker_path} is created; `expected_if_safe` must state that \
it is never created.
"""


def _build_prompt(finding: SecurityFinding) -> str:
    mechanism_hint = _MECHANISM_HINTS.get(finding.sensitive_op, _GENERIC_MECHANISM_HINT)
    return _PROMPT_TEMPLATE.format(
        sensitive_op=finding.sensitive_op.value,
        symbol=finding.symbol,
        file_path=finding.file_path,
        diff_hunk=finding.diff_hunk,
        rationale=finding.rationale,
        marker_path=_MARKER_PATH,
        mechanism_hint=mechanism_hint,
    )


def generate(
    finding: SecurityFinding,
    model_id: str = "groq:openai/gpt-oss-120b",
    fallback: AttackHypothesis | None = NETDIAG_FALLBACK_HYPOTHESIS,
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
    """
    try:
        raw = generate_hypothesis_json(_build_prompt(finding))
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
    except (GroqUnavailable, KeyError, TypeError, ValidationError):
        # Covers: API down/rate-limited, malformed JSON (raised as
        # GroqUnavailable by groq_client), valid JSON missing expected
        # keys (KeyError), a non-dict JSON value (TypeError on indexing),
        # and valid-but-wrong-shaped values, e.g. `payload` coming back as
        # a list/object instead of a string (pydantic ValidationError).
        if fallback is None:
            raise
        return fallback.model_copy(update={"finding_id": finding.finding_id})
