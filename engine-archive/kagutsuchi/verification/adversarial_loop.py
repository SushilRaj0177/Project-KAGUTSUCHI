"""Multi-model adversarial hardening loop.

Extends "the AI proposes, the sandbox disposes" from one model to several:
rotates through a handful of DISTINCT LLMs, each taking a turn as either an
attacker (write a fresh exploit against the CURRENT code) or a fixer (patch
whatever the last attacker just proved). No agent's opinion about its own
attack or fix is ever trusted - every verdict in here comes from the same
real sandboxed execution the rest of the pipeline uses
(system/orchestration + system/sandbox), never from a model's own claim.

This is deliberately additive: it only calls the existing, already-shipped
prompt builders and Groq client with a different `model` argument each
round. Nothing in generate.py, propose_fix.py, or groq_client.py is
modified to make this work.

Stops when `required_clean_streak` DIFFERENT models in a row fail to
exploit the current code (a much stronger signal than one model failing
once), or `max_rounds` / `time_budget_s` runs out - all three default to
small enough numbers to run inside a live demo.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Callable

from system.orchestration import build_script_from_source, new_run_id, run_attack
from verification.hypothesis.generate import _build_prompt as _attack_prompt
from verification.hypothesis.groq_client import GroqUnavailable, generate_hypothesis_json
from verification.hypothesis.propose_fix import FixValidationError
from verification.hypothesis.propose_fix import _build_prompt as _fix_prompt
from verification.hypothesis.propose_fix import _validate as _validate_fix_source
from verification.models import AttackHypothesis, SecurityFinding

# Four distinct Groq-hosted models standing in for four independent "agents" -
# no single model's blind spot is shared by all four, which is the entire
# point of rotating attackers/fixers rather than calling the same model
# on repeat. Override via the `models` argument if any of these ever get
# retired on Groq's side.
DEFAULT_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]

MARKER_PATH = "/tmp/kagutsuchi_pwned"


@dataclass
class RoundResult:
    round_no: int
    role: str  # "attack" or "fix"
    model: str
    outcome: str
    exploited: bool | None = None  # only meaningful for attack rounds
    source_after: str | None = None


@dataclass
class HardeningReport:
    rounds: list[RoundResult] = field(default_factory=list)
    final_source: str = ""
    hardened: bool = False
    stopped_reason: str = ""


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


def _attack_with_model(finding: SecurityFinding, model: str) -> AttackHypothesis:
    raw = generate_hypothesis_json(_attack_prompt(finding), model=model)
    return _hypothesis_from_raw(raw, finding, model)


def _fix_with_model(finding: SecurityFinding, hypothesis: AttackHypothesis, model: str) -> str:
    raw = generate_hypothesis_json(_fix_prompt(finding, hypothesis), model=model)
    fixed_source = raw["fixed_source"]
    if not isinstance(fixed_source, str):
        raise FixValidationError("fixed_source was not a string")
    _validate_fix_source(fixed_source, finding.symbol)
    return fixed_source


def _run_payload(source: str, symbol: str, hypothesis: AttackHypothesis) -> bool:
    """Runs for real in the sandbox. Returns True iff the marker file the
    payload is supposed to create actually got created - the one signal
    this whole project trusts."""
    run_id = new_run_id()
    script = build_script_from_source(source, symbol)
    evidence = run_attack(vulnerable_code=script, hypothesis=hypothesis, run_id=run_id)
    return MARKER_PATH in evidence.filesystem_diff.get("created", [])


def run_adversarial_hardening(
    finding: SecurityFinding,
    initial_source: str,
    *,
    models: list[str] | None = None,
    max_rounds: int = 8,
    required_clean_streak: int = 2,
    time_budget_s: float = 150.0,
    on_round: Callable[[RoundResult], None] | None = None,
) -> HardeningReport:
    """`initial_source` must be a self-contained module/function source
    (see system/orchestration/harness.py) whose `finding.symbol` function
    takes exactly one string argument - the same constraint every other
    real-code attack path in this project has."""
    models = models or DEFAULT_MODELS
    report = HardeningReport(final_source=initial_source)
    current_source = initial_source
    clean_streak = 0
    start = time.monotonic()
    model_i = 0

    def _emit(result: RoundResult) -> None:
        report.rounds.append(result)
        if on_round:
            on_round(result)

    for round_no in range(1, max_rounds + 1):
        if time.monotonic() - start > time_budget_s:
            report.stopped_reason = "time budget exceeded"
            break

        attacker_model = models[model_i % len(models)]
        model_i += 1
        attack_finding = finding.model_copy(update={"diff_hunk": current_source})

        try:
            hypothesis = _attack_with_model(attack_finding, attacker_model)
        except (GroqUnavailable, KeyError, TypeError) as exc:
            _emit(RoundResult(round_no, "attack", attacker_model, f"couldn't produce an attack ({exc}) - skipping this agent's turn"))
            continue

        try:
            exploited = _run_payload(current_source, finding.symbol, hypothesis)
        except Exception as exc:  # noqa: BLE001 - harness/sandbox failure, not a security verdict
            _emit(RoundResult(round_no, "attack", attacker_model, f"attack couldn't be executed ({exc}) - skipping this agent's turn"))
            continue

        if not exploited:
            clean_streak += 1
            _emit(RoundResult(round_no, "attack", attacker_model, "attack FAILED - code held", exploited=False, source_after=current_source))
            if clean_streak >= required_clean_streak:
                report.hardened = True
                report.stopped_reason = f"{clean_streak} independent models in a row failed to exploit it"
                break
            continue

        clean_streak = 0
        _emit(RoundResult(round_no, "attack", attacker_model, "attack SUCCEEDED - real exploit proven in the sandbox", exploited=True, source_after=current_source))

        fixer_model = models[model_i % len(models)]
        model_i += 1
        try:
            fixed_source = _fix_with_model(attack_finding, hypothesis, fixer_model)
        except (GroqUnavailable, FixValidationError, KeyError, TypeError) as exc:
            _emit(RoundResult(round_no, "fix", fixer_model, f"fix proposal failed ({exc}) - code stays as-is, will be re-attacked"))
            continue

        # Never adopt a fix because it parsed - prove it closes THIS exact
        # exploit for real before trusting it.
        try:
            still_works = _run_payload(fixed_source, finding.symbol, hypothesis)
        except Exception as exc:  # noqa: BLE001
            _emit(RoundResult(round_no, "fix", fixer_model, f"fix couldn't be verified ({exc}) - discarding it"))
            continue

        if still_works:
            _emit(RoundResult(round_no, "fix", fixer_model, "fix did NOT close the hole - discarding it, prior code stands for next round"))
            continue

        current_source = fixed_source
        report.final_source = current_source
        _emit(RoundResult(round_no, "fix", fixer_model, "fix verified against this exact exploit - adopted", source_after=current_source))
    else:
        report.stopped_reason = report.stopped_reason or "max rounds reached"

    report.final_source = current_source
    return report
