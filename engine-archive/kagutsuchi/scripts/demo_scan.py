#!/usr/bin/env python3
"""
KAGUTSUCHI interactive demo console.

Run it once, then pick options from the menu — nothing to memorize, no
flags, no re-running commands.

Usage:
    PYTHONPATH=. python scripts/demo_scan.py

Needs GROQ_API_KEY set for the AI scan / live attack options - the menu
still runs without it, those options just explain that plainly instead
of crashing.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from contracts import SecurityFinding
from system.analysis.ast_scan import scan_source
from system.analysis.llm_scan import scan_source_with_llm

_FIXTURES_DIR = Path(__file__).parent.parent / "verification" / "fixtures"

# Session state, carried between menu choices in this one run.
_state: dict = {"file": None, "source": None, "findings": []}

# Plain-English names, matching the ones shown on the live website -
# nobody outside this codebase knows what "sql_query" or "filesystem"
# means as a category label.
_FRIENDLY_NAMES = {
    "shell_exec": "Command Injection",
    "subprocess": "Command Injection",
    "sql_query": "SQL Injection",
    "deserialization": "Insecure Deserialization",
    "filesystem": "Path Traversal",
    "auth_change": "Authentication Bypass",
    "network_egress": "Unsafe Network Access",
    "other": "Security Vulnerability",
}


def _friendly(op: str) -> str:
    return _FRIENDLY_NAMES.get(op, op.replace("_", " ").title())


def _has_groq_key() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def _pause() -> None:
    input("\nPress Enter to go back to the menu... ")


def _banner(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def _list_fixtures() -> list[Path]:
    return sorted(p for p in _FIXTURES_DIR.glob("*.py") if p.name != "__init__.py")


def _print_finding(i: int, f: SecurityFinding) -> None:
    print(f"\n  [{i}] {_friendly(f.sensitive_op.value)}  —  severity: {f.severity_hint.value}  —  in {f.symbol}()")
    print(f"      {f.rationale}")


# ---- Menu actions ----------------------------------------------------


def action_scan() -> None:
    files = _list_fixtures()
    print("\nWhich file do you want to scan for vulnerabilities?\n")
    for i, f in enumerate(files):
        print(f"  [{i}] {f.name}")
    print("  [c] enter a custom file path")
    choice = input(f"\nYour choice [0-{len(files) - 1} or c]: ").strip().lower()
    if choice == "c":
        path = Path(input("Path to the file: ").strip())
    elif choice.isdigit() and 0 <= int(choice) < len(files):
        path = files[int(choice)]
    else:
        print("Didn't recognize that choice — nothing scanned.")
        return

    if not path.exists():
        print(f"Couldn't find that file: {path}")
        return

    source = path.read_text()
    _banner(f"SCANNING {path.name}")

    print("\nStep 1 — deterministic scan (instant, matches known dangerous code patterns):")
    try:
        ast_findings = scan_source(source, str(path))
    except SyntaxError as exc:
        print(f"  That file isn't valid Python: {exc}")
        return
    if not ast_findings:
        print("  Nothing matched a known pattern.")
    else:
        print(f"  Found {len(ast_findings)}.")

    print("\nStep 2 — AI scan (reads the code for meaning, catches what the fixed list can't):")
    if not _has_groq_key():
        print("  Skipped — no GROQ_API_KEY is set in this terminal, so the AI half can't run.")
        llm_findings, proposal = [], None
    else:
        llm_result = scan_source_with_llm(source, str(path))
        llm_findings, proposal = llm_result.findings, llm_result.proposal
        if not llm_findings:
            print("  Nothing new found beyond the deterministic scan.")
        else:
            print(f"  Found {len(llm_findings)}.")
        if proposal:
            print(
                f"\n  Bonus: the AI thinks this looks like a whole new vulnerability class "
                f"we haven't hard-coded a rule for yet — {proposal.class_name!r}."
            )
            print(f"  {proposal.rationale}")
            print("  (This gets queued for a human to review, never trusted automatically.)")

    all_findings = ast_findings + llm_findings
    _banner(f"RESULT: {len(all_findings)} vulnerability(ies) found")
    for i, f in enumerate(all_findings):
        _print_finding(i, f)

    _state["file"] = path
    _state["source"] = source
    _state["findings"] = all_findings

    if not all_findings:
        return

    choice = input(
        f"\nWant to attack one of these right now and see if it's real? "
        f"Enter a number [0-{len(all_findings) - 1}], or just press Enter to skip: "
    ).strip()
    if choice.isdigit() and 0 <= int(choice) < len(all_findings):
        _run_attack(int(choice))


def action_attack() -> None:
    if not _state["findings"]:
        print("\nNothing to attack yet — scan a file first (option 1).")
        return

    print(f"\nHere's what we found in {_state['file'].name} last time:")
    for i, f in enumerate(_state["findings"]):
        _print_finding(i, f)

    choice = input(f"\nAttack which one? [0-{len(_state['findings']) - 1}]: ").strip()
    if not (choice.isdigit() and 0 <= int(choice) < len(_state["findings"])):
        print("Didn't recognize that choice.")
        return
    _run_attack(int(choice))


def _run_attack(index: int) -> None:
    target = _state["findings"][index]

    if not _has_groq_key():
        print(
            "\nCan't run a live attack — no GROQ_API_KEY is set in this terminal.\n"
            "Set it first, e.g.:  $env:GROQ_API_KEY = \"your-key-here\"\n"
            "then come back to this menu and try again."
        )
        return

    _banner(f"ATTACKING: {_friendly(target.sensitive_op.value)} in {target.symbol}()")
    print("Asking the AI to write a real exploit for this exact code, then running it for real...")

    from integration.upload_pipeline import AttackGenerationUnavailable, verify_upload

    try:
        bundle = verify_upload(source=_state["source"], finding=target)
    except AttackGenerationUnavailable as exc:
        cause = exc.__cause__
        if cause is not None and "GROQ_API_KEY is not set" in str(cause):
            print("\nGROQ_API_KEY isn't set (or isn't valid). Set it and try again.")
        else:
            print(
                f"\nThe AI couldn't produce a usable attack this time "
                f"({(cause if cause else exc)!r}). This happens occasionally — try again, "
                f"or pick a different finding."
            )
        return

    print(f"\nAttack payload the AI wrote for us : {bundle.hypothesis.payload}")
    if bundle.confidence is not None:
        print(f"How confident the AI was it would work : {bundle.confidence:.0%}")

    is_docker = bundle.before.container_id != "subprocess-fallback"
    if is_docker:
        print(f"Where it ran                        : a real, isolated Docker container (id {bundle.before.container_id[:12]})")
    else:
        print("Where it ran                        : an isolated subprocess (Docker wasn't reachable on this machine)")

    marker_hit = "/tmp/kagutsuchi_pwned" in bundle.before.filesystem_diff.get("created", [])
    print(f"Did the attack actually work?       : {'YES — the exploit succeeded' if marker_hit else 'No — this finding was a false positive'}")

    if bundle.result:
        verdict_plain = {
            "VERIFIED_FIXED": "The exploit worked before the fix, and failed after — the fix is verified.",
            "STILL_VULNERABLE": "The exploit still works even after the proposed fix — not safe yet.",
        }.get(bundle.result.verdict, bundle.result.summary)
        print(f"\nVERDICT: {bundle.result.verdict.value}")
        print(verdict_plain)
        if bundle.fixed_source:
            print(f"\nHere's the fix the AI wrote, which just survived a real re-attack:\n{bundle.fixed_source}")
    elif bundle.fix_error:
        print(f"\nThe attack worked, but the automatic fix step didn't complete: {bundle.fix_error}")
    else:
        print("\nThis particular finding turned out to be a false positive — nothing to fix.")


def action_calibration() -> None:
    _banner("IS THE AI'S CONFIDENCE TRUSTWORTHY?")
    from verification.calibration import CalibrationEntry, calibration_summary

    print(
        "\nEvery attack comes with the AI's own guess at how likely it is to work. "
        "We check that guess against what actually happened, so we can tell if the "
        "model is honestly calibrated or just confidently guessing.\n"
        "\nHere's that scoring logic running on 5 example outcomes:\n"
    )
    example = [
        CalibrationEntry("h1", 0.95, True),
        CalibrationEntry("h2", 0.80, True),
        CalibrationEntry("h3", 0.60, False),
        CalibrationEntry("h4", 0.40, False),
        CalibrationEntry("h5", 0.90, True),
    ]
    summary = calibration_summary(example)
    print(f"Brier score (0 = perfectly calibrated, 1 = worst possible): {summary['brier_score']:.3f}\n")
    print(json.dumps(summary["buckets"], indent=2))
    print(
        "\nOn the live website, the /calibration page shows this same score computed "
        "from real attacks people have actually run on the site — try option 2 here "
        "to generate one for real."
    )


def action_new_classes() -> None:
    _banner("HOW WE FIND VULNERABILITIES WE HAVEN'T HARD-CODED YET")
    print(
        "\nOur fast scanner only recognizes a fixed list of dangerous patterns. "
        "So every scan (option 1) also asks the AI: 'does this look like a "
        "vulnerability type we don't have a rule for yet?'\n"
        "\nTry scanning path_traversal.py or tar_extraction.py — those two aren't "
        "in the fast scanner's list yet, so you'll see the AI propose one live.\n"
        "\nWe never auto-trust that proposal. It gets queued for a human to review "
        "on the website's /detector-proposals page. Once approved, this turns it "
        "into real, permanent detector code:\n"
        "\n  python scripts/promote_detector.py --class-name <name> "
        "--call-signature <dotted.call> --rationale \"...\" --severity high\n"
    )


def action_adversarial() -> None:
    _banner("4 AI MODELS FIGHT OVER THE SAME CODE")
    if not _has_groq_key():
        print("\nCan't run this — no GROQ_API_KEY is set in this terminal.")
        return
    if not _state["findings"]:
        print("\nScan a file first (option 1), then come back here.")
        return

    print("Here's what we found last time:")
    for i, f in enumerate(_state["findings"]):
        _print_finding(i, f)
    choice = input(f"\nHarden which one? [0-{len(_state['findings']) - 1}]: ").strip()
    if not (choice.isdigit() and 0 <= int(choice) < len(_state["findings"])):
        print("Didn't recognize that choice.")
        return
    finding = _state["findings"][int(choice)]

    from verification.adversarial_loop import DEFAULT_MODELS, RoundResult, run_adversarial_hardening

    def _print_round(r: "RoundResult") -> None:
        label = "ATTACK" if r.role == "attack" else " FIX  "
        print(f"\n  round {r.round_no:>2}  [{label}]  {r.model}")
        print(f"           {r.outcome}")

    print(f"\nAgents in rotation: {', '.join(DEFAULT_MODELS)}")
    print("Each round, one model attacks the CURRENT code for real in the sandbox.")
    print("If it breaks, a different model fixes it, and that fix has to survive")
    print("the exact same exploit before it's trusted. Stops once 2 different")
    print("models in a row can't break what's left standing.\n")

    report = run_adversarial_hardening(finding, _state["source"], on_round=_print_round)

    print(f"\n{'=' * 72}")
    if report.hardened:
        print(f"RESULT: hardened — {report.stopped_reason}")
    else:
        print(f"RESULT: stopped without full confirmation — {report.stopped_reason}")
    print("=" * 72)
    print(f"\nFinal surviving code for {finding.symbol}():\n{report.final_source}")


def main() -> None:
    print("=" * 72)
    print("KAGUTSUCHI — real vulnerability scanning, real attacks, real fixes.")
    print("=" * 72)
    if not _has_groq_key():
        print(
            "\nHeads up: GROQ_API_KEY isn't set in this terminal. The deterministic "
            "scan still works fully, but the AI scan and live-attack options will "
            "say so and skip themselves rather than run."
        )

    while True:
        print(f"\n{'=' * 72}")
        if _state["file"]:
            print(f"Last scanned: {_state['file'].name}  ({len(_state['findings'])} finding(s) found)")
        print(
            "\n  [1] Scan a file for vulnerabilities"
            "\n  [2] Attack a finding from the last scan"
            "\n  [3] Demo: is the AI's confidence trustworthy?"
            "\n  [4] Demo: how new vulnerability classes get discovered"
            "\n  [5] Demo: 4 AI models fight over the same code till one wins"
            "\n  [q] Quit"
        )
        choice = input("\nWhat would you like to do? ").strip().lower()

        try:
            if choice == "1":
                action_scan()
            elif choice == "2":
                action_attack()
            elif choice == "3":
                action_calibration()
            elif choice == "4":
                action_new_classes()
            elif choice == "5":
                action_adversarial()
            elif choice in ("q", "quit", "exit"):
                print("\nBye!")
                return
            else:
                print("Didn't recognize that — please enter one of the numbers above, or 'q'.")
                continue
        except KeyboardInterrupt:
            print("\n\nBye!")
            return
        except Exception as exc:  # noqa: BLE001 - never let a demo crash out of the menu
            print(f"\nSomething unexpected went wrong: {exc!r}")
            print("(This is a bug in the demo script, not a security finding — try again.)")

        _pause()


if __name__ == "__main__":
    main()
