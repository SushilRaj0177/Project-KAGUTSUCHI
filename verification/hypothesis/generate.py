"""Given a SecurityFinding, produce one deterministic AttackHypothesis.

Tries Groq once; on any failure (down, rate-limited, malformed output)
degrades to the hardcoded P0 fallback rather than raising - see
verification/hypothesis/fallback.py.
"""

from __future__ import annotations

import uuid

from pydantic import ValidationError

from verification.hypothesis.fallback import with_finding_id
from verification.hypothesis.groq_client import GroqUnavailable, generate_hypothesis_json
from verification.models import AttackHypothesis, SecurityFinding

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

Respond with a single JSON object with exactly these keys:
security_property, attack_vector, payload, expected_if_vulnerable, \
expected_if_safe. All values must be plain strings. `payload` must be a \
single concrete input, not a description.
"""


def _build_prompt(finding: SecurityFinding) -> str:
    return _PROMPT_TEMPLATE.format(
        sensitive_op=finding.sensitive_op.value,
        symbol=finding.symbol,
        file_path=finding.file_path,
        diff_hunk=finding.diff_hunk,
        rationale=finding.rationale,
    )


def generate(finding: SecurityFinding, model_id: str = "groq:openai/gpt-oss-120b") -> AttackHypothesis:
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
        return with_finding_id(finding.finding_id)
