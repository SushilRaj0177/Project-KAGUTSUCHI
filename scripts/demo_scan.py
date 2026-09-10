#!/usr/bin/env python3
"""
KAGUTSUCHI interactive demo console. Run it once, then drive every
feature from one menu — nothing to memorize, nothing to re-run.

Usage:
    PYTHONPATH=. python scripts/demo_scan.py

Needs GROQ_API_KEY set for the AI scan / live attack menu items - the
menu still runs without it, those items just report the LLM is
unavailable (same honest-failure behavior as the live site).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from contracts import SecurityFinding
from system.analysis.ast_scan import scan_source
from system.analysis.llm_scan import scan_source_with_llm

_FIXTURES_DIR = Path(__file__).parent.parent / "verification" / "fixtures"

# Session state, carried between menu choices in this one run.
_state: dict = {"file": None, "source": None, "findings": []}


def _pause() -> None:
    input("\n[press Enter to return to the menu] ")


def _list_fixtures() -> list[Path]:
    return sorted(p for p in _FIXTURES_DIR.glob("*.py") if p.name != "__init__.py")


def _print_finding(i: int, f: SecurityFinding) -> None:
    print(f"\n[{i}] {f.sensitive_op.value.upper()}  ({f.severity_hint.value})  — {f.symbol}()")
    print(f"    detected by : {f.detected_by}")
    print(f"    why         : {f.rationale}")


# ---- Menu actions ----------------------------------------------------


def action_scan() -> None:
    files = _list_fixtures()
    print("\nWhich file do you want to scan?\n")
    for i, f in enumerate(files):
        print(f"  [{i}] {f.name}")
    print(f"  [c] custom path")
    choice = input(f"\nEnter a number [0-{len(files) - 1}] or 'c': ").strip().lower()
    if choice == "c":
        path = Path(input("Path to the file: ").strip())
    elif choice.isdigit() and 0 <= int(choice) < len(files):
        path = files[int(choice)]
    else:
        print("Not a valid choice.")
        return

    if not path.exists():
        print(f"No such file: {path}")
        return

    source = path.read_text()
    print(f"\n{'=' * 72}\nSCANNING {path}\n{'=' * 72}")

    print("\n--- Deterministic AST scan (fixed pattern list, instant, no network) ---")
    try:
        ast_findings = scan_source(source, str(path))
    except SyntaxError as exc:
        print(f"Not valid Python: {exc}")
        return
    if not ast_findings:
        print("  (nothing matched a known pattern)")

    print("\n--- AI scan (reads the code for meaning, real Groq call) ---")
    llm_result = scan_source_with_llm(source, str(path))
    if not llm_result.findings:
        print("  (nothing found beyond the AST pass)")
    if llm_result.proposal:
        p = llm_result.proposal
        print(
            f"\n  >> New detector class proposed: {p.class_name!r} "
            f"(call signature: {p.call_signature!r}, severity: {p.severity_hint})"
        )
        print(f"     {p.rationale}")
        print("     (queued for human review — never auto-applied, see /detector-proposals)")

    all_findings = ast_findings + llm_result.findings
    print(f"\n{'=' * 72}\n{len(all_findings)} finding(s) total ({len(ast_findings)} AST + {len(llm_result.findings)} AI)")
    print("=" * 72)
    for i, f in enumerate(all_findings):
        _print_finding(i, f)

    _state["file"] = path
    _state["source"] = source
    _state["findings"] = all_findings

    if not all_findings:
        return

    # Flow straight into the attack instead of dead-ending back at the
    # menu - scanning without immediately offering to attack is exactly
    # the confusing dead stop this was rewritten to avoid.
    choice = input(
        f"\nAttack which finding right now? [0-{len(all_findings) - 1}], or Enter to skip: "
    ).strip()
    if choice.isdigit() and 0 <= int(choice) < len(all_findings):
        _run_attack(int(choice))


def action_attack() -> None:
    if not _state["findings"]:
        print("\nNo findings yet — run 'Scan a file' first.")
        return

    print(f"\nFindings from {_state['file'].name}:")
    for i, f in enumerate(_state["findings"]):
        _print_finding(i, f)

    choice = input(f"\nAttack which finding? [0-{len(_state['findings']) - 1}]: ").strip()
    if not (choice.isdigit() and 0 <= int(choice) < len(_state["findings"])):
        print("Not a valid choice.")
        return
    _run_attack(int(choice))


def _run_attack(index: int) -> None:
    target = _state["findings"][index]

    print(f"\n{'=' * 72}\nATTACKING finding [{index}]: {target.symbol}() — live Groq call, no fallback")
    print("=" * 72)

    from integration.upload_pipeline import AttackGenerationUnavailable, verify_upload

    try:
        bundle = verify_upload(source=_state["source"], finding=target)
    except AttackGenerationUnavailable as exc:
        print(f"\nCould not generate a live attack: {exc}")
        if exc.__cause__ is not None:
            print(f"Underlying cause: {exc.__cause__!r}")
        return

    print(f"\nGenerated attack payload : {bundle.hypothesis.payload}")
    if bundle.confidence is not None:
        print(f"Model's stated confidence: {bundle.confidence:.0%}")

    is_docker = bundle.before.container_id != "subprocess-fallback"
    sandbox_label = (
        f"REAL DOCKER CONTAINER  (id: {bundle.before.container_id})"
        if is_docker
        else "SUBPROCESS FALLBACK  (no Docker daemon reachable on this host)"
    )
    print(f"Sandbox used             : {sandbox_label}")

    marker_hit = "/tmp/kagutsuchi_pwned" in bundle.before.filesystem_diff.get("created", [])
    print(f"Exploit succeeded against vulnerable code: {marker_hit}")

    if bundle.result:
        print(f"\nVerdict: {bundle.result.verdict}")
        print(f"Summary: {bundle.result.summary}")
        if bundle.fixed_source:
            print(f"\n--- Live-generated fix ---\n{bundle.fixed_source}")
    elif bundle.fix_error:
        print(f"\nFix step did not complete: {bundle.fix_error}")
    else:
        print("\nThe generated attack didn't actually exploit the code (false positive) — nothing to fix.")


def action_calibration() -> None:
    print(f"\n{'=' * 72}\nCONFIDENCE CALIBRATION — is the model's stated confidence trustworthy?\n{'=' * 72}")
    from verification.calibration import CalibrationEntry, calibration_summary

    print(
        "\nverification/calibration.py compares the model's own stated confidence "
        "(from generate_with_confidence) against what the sandbox actually observed. "
        "Demonstrating the scoring logic on a few example outcomes:\n"
    )
    example = [
        CalibrationEntry("h1", 0.95, True),
        CalibrationEntry("h2", 0.80, True),
        CalibrationEntry("h3", 0.60, False),
        CalibrationEntry("h4", 0.40, False),
        CalibrationEntry("h5", 0.90, True),
    ]
    summary = calibration_summary(example)
    print(json.dumps(summary, indent=2))
    print(
        "\nOn the live site, /calibration shows this computed from real production "
        "runs, not this example data — see the 'Attack & verify' menu item here for "
        "a real one being generated right now."
    )


def action_new_classes() -> None:
    print(f"\n{'=' * 72}\nAI-DISCOVERED VULNERABILITY CLASSES\n{'=' * 72}")
    print(
        "\nEvery scan (menu option 1) already asks the AI to propose a new "
        "deterministic detector when it spots something outside the known "
        "pattern list — watch for a '>> New detector class proposed' line "
        "after scanning path_traversal.py or tar_extraction.py, since those "
        "two aren't in the AST list yet.\n"
        "\nOn the live site this queues on /detector-proposals for review. "
        "To turn an accepted one into real code:\n"
        "\n  python scripts/promote_detector.py --class-name <name> "
        "--call-signature <dotted.call> --rationale \"...\" --severity high\n"
    )


def main() -> None:
    while True:
        print(f"\n{'=' * 72}")
        print("KAGUTSUCHI — interactive demo console")
        print("=" * 72)
        if _state["file"]:
            print(f"(last scanned: {_state['file'].name}, {len(_state['findings'])} finding(s))")
        print(
            "\n  [1] Scan a file (deterministic AST + AI, both engines)"
            "\n  [2] Attack & verify a finding (live Groq + real Docker sandbox)"
            "\n  [3] Confidence calibration demo"
            "\n  [4] AI-discovered new vulnerability classes"
            "\n  [q] Quit"
        )
        choice = input("\n> ").strip().lower()

        try:
            if choice == "1":
                action_scan()
            elif choice == "2":
                action_attack()
            elif choice == "3":
                action_calibration()
            elif choice == "4":
                action_new_classes()
            elif choice in ("q", "quit", "exit"):
                return
            else:
                print("Not a valid choice.")
                continue
        except KeyboardInterrupt:
            print()
            return
        except Exception as exc:  # noqa: BLE001 - never let a demo crash out of the menu
            print(f"\nSomething went wrong: {exc!r}")

        _pause()


if __name__ == "__main__":
    main()
