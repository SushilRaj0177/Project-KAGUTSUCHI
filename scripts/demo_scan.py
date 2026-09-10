#!/usr/bin/env python3
"""
Interactive demo CLI: pick a vulnerable fixture, watch the AST scanner
and the AI scanner find it side by side, then pick a finding and watch a
real live attack + real live fix + real verdict happen — a real Groq
call generates the attack hypothesis AND the fix proposal on the spot,
no fallback, no canned payload, run for real in the Docker sandbox.

Requires GROQ_API_KEY to be set for the AI scan and for the attack step
to do anything but fail with a clear error - this is deliberately the
"nothing fake" path, not the fallback-hypothesis demo.

Usage:
    PYTHONPATH=. python scripts/demo_scan.py                 # interactive menu
    PYTHONPATH=. python scripts/demo_scan.py <file>           # scan one file, then prompt
    PYTHONPATH=. python scripts/demo_scan.py <file> --attack --finding N   # non-interactive
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contracts import SecurityFinding
from system.analysis.ast_scan import scan_source
from system.analysis.llm_scan import scan_source_with_llm

_FIXTURES_DIR = Path(__file__).parent.parent / "verification" / "fixtures"


def _pick_file_interactively() -> Path:
    files = sorted(p for p in _FIXTURES_DIR.glob("*.py") if p.name != "__init__.py")
    print("Which vulnerable fixture do you want to scan?\n")
    for i, f in enumerate(files):
        print(f"  [{i}] {f.name}")
    print()
    while True:
        choice = input(f"Enter a number [0-{len(files) - 1}]: ").strip()
        if choice.isdigit() and 0 <= int(choice) < len(files):
            return files[int(choice)]
        print("Not a valid choice, try again.")


def _print_finding(i: int, f: SecurityFinding) -> None:
    print(f"\n[{i}] {f.sensitive_op.value.upper()}  ({f.severity_hint.value})  — {f.symbol}()")
    print(f"    detected by : {f.detected_by}")
    print(f"    why         : {f.rationale}")


def _run_attack(source: str, target: SecurityFinding, index: int) -> None:
    print(f"\n{'=' * 72}\nATTACKING finding [{index}]: {target.symbol}() — live Groq call, no fallback")
    print("=" * 72)

    from integration.upload_pipeline import AttackGenerationUnavailable, verify_upload

    try:
        bundle = verify_upload(source=source, finding=target)
    except AttackGenerationUnavailable as exc:
        print(f"\nCould not generate a live attack: {exc}", file=sys.stderr)
        if exc.__cause__ is not None:
            print(f"Underlying cause: {exc.__cause__!r}", file=sys.stderr)
        sys.exit(1)

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

    print(f"\nFull evidence:\n{json.dumps(bundle.before.model_dump(mode='json'), indent=2)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path, nargs="?", help="omit to pick from verification/fixtures/ interactively")
    parser.add_argument("--attack", action="store_true", help="skip the prompt, attack immediately (for scripting)")
    parser.add_argument("--finding", type=int, default=0, help="index of the finding to attack with --attack")
    args = parser.parse_args()

    file = args.file if args.file else _pick_file_interactively()
    source = file.read_text()

    print(f"\n{'=' * 72}\nSCANNING {file}\n{'=' * 72}")

    print("\n--- Deterministic AST scan (fixed pattern list, instant, no network) ---")
    try:
        ast_findings = scan_source(source, str(file))
    except SyntaxError as exc:
        print(f"Not valid Python: {exc}", file=sys.stderr)
        sys.exit(1)
    if not ast_findings:
        print("  (nothing matched a known pattern)")

    print("\n--- AI scan (reads the code for meaning, real Groq call) ---")
    llm_result = scan_source_with_llm(source, str(file))
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

    if not all_findings:
        print("\nNo findings to attack.")
        return

    if args.attack:
        if args.finding >= len(all_findings):
            print(f"\n--finding {args.finding} is out of range (0-{len(all_findings) - 1})", file=sys.stderr)
            sys.exit(1)
        _run_attack(source, all_findings[args.finding], args.finding)
        return

    # Interactive: keep letting the presenter pick findings to attack
    # (or scan another fixture) until they choose to quit - this is the
    # actual "interface" the CLI was missing, not a one-shot script.
    while True:
        print()
        choice = input(
            f"Attack which finding? [0-{len(all_findings) - 1}], "
            f"'n' for a different fixture, or Enter/'q' to quit: "
        ).strip().lower()
        if choice in ("", "q"):
            return
        if choice == "n":
            main()
            return
        if choice.isdigit() and 0 <= int(choice) < len(all_findings):
            _run_attack(source, all_findings[int(choice)], int(choice))
        else:
            print("Not a valid choice, try again.")


if __name__ == "__main__":
    main()
