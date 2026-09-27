#!/usr/bin/env python3
"""
KAGUTSUCHI adversarial hardening demo: 4 distinct LLMs take turns attacking
and fixing the same code until several of them in a row can't break it.

Usage:
    PYTHONPATH=. python scripts/adversarial_hardening.py

Needs GROQ_API_KEY set. Every attack/fix claim is proven (or disproven) by
actually running it in the sandbox - nothing here is an LLM's opinion of
its own work.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from contracts import SecurityFinding
from system.analysis.ast_scan import scan_source
from verification.adversarial_loop import DEFAULT_MODELS, RoundResult, run_adversarial_hardening

_FIXTURES_DIR = Path(__file__).parent.parent / "verification" / "fixtures"


def _print_round(r: RoundResult) -> None:
    label = "ATTACK" if r.role == "attack" else " FIX  "
    print(f"\n  round {r.round_no:>2}  [{label}]  {r.model}")
    print(f"           {r.outcome}")


def main() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY is not set - this demo needs it (all 4 agents call Groq).")
        sys.exit(1)

    files = sorted(p for p in _FIXTURES_DIR.glob("*.py") if p.name != "__init__.py")
    print("=" * 72)
    print("ADVERSARIAL HARDENING — 4 models fight over the same code")
    print("=" * 72)
    print("\nWhich file should the agents fight over?\n")
    for i, f in enumerate(files):
        print(f"  [{i}] {f.name}")
    choice = input(f"\nYour choice [0-{len(files) - 1}]: ").strip()
    if not (choice.isdigit() and 0 <= int(choice) < len(files)):
        print("Didn't recognize that choice.")
        return
    path = files[int(choice)]
    source = path.read_text()

    findings = scan_source(source, str(path))
    if not findings:
        print(f"\nThe deterministic scanner found nothing in {path.name} to fight over.")
        return

    print(f"\nFound {len(findings)} finding(s) in {path.name}:")
    for i, f in enumerate(findings):
        print(f"  [{i}] {f.sensitive_op.value} in {f.symbol}()")
    fchoice = input(f"\nHarden which one? [0-{len(findings) - 1}]: ").strip()
    if not (fchoice.isdigit() and 0 <= int(fchoice) < len(findings)):
        print("Didn't recognize that choice.")
        return
    finding: SecurityFinding = findings[int(fchoice)]

    print(f"\nAgents in rotation: {', '.join(DEFAULT_MODELS)}")
    print("\nEach round: one model attacks the current code for real in the sandbox.")
    print("If it breaks, a different model fixes it, and the fix is proven against")
    print("that exact exploit before being adopted. Stops once 2 different models")
    print("in a row can't break what's left standing.\n")

    report = run_adversarial_hardening(finding, source, on_round=_print_round)

    print("\n" + "=" * 72)
    if report.hardened:
        print(f"RESULT: hardened — {report.stopped_reason}")
    else:
        print(f"RESULT: stopped without full confirmation — {report.stopped_reason}")
    print("=" * 72)
    print(f"\nFinal surviving code for {finding.symbol}():\n")
    print(report.final_source)


if __name__ == "__main__":
    main()
