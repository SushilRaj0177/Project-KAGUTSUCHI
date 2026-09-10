#!/usr/bin/env python3
"""
Live demo script: shows the AST scanner and the AI scanner finding
vulnerabilities in the SAME file side by side, then (with --attack)
runs the real live pipeline against one of the findings — a real Groq
call generates the attack hypothesis AND the fix proposal on the spot,
no fallback, no canned payload.

Requires GROQ_API_KEY to be set for the LLM scan and for --attack to do
anything but fail with a clear error - this is deliberately the
"nothing fake" path, not the fallback-hypothesis demo.

Usage:
    PYTHONPATH=. python scripts/demo_scan.py <file> [--attack] [--finding N]

    --attack     after showing findings, run the real attack+fix+verify
                 pipeline against one of them (index 0 by default)
    --finding N  pick a specific finding by its index in the merged list
                 printed below, instead of the first one
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contracts import SecurityFinding
from system.analysis.ast_scan import scan_source
from system.analysis.llm_scan import scan_source_with_llm


def _print_finding(i: int, f: SecurityFinding, source: str) -> None:
    print(f"\n[{i}] {f.sensitive_op.value.upper()}  ({f.severity_hint.value})  — {f.symbol}()")
    print(f"    detected by : {f.detected_by}")
    print(f"    why         : {f.rationale}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path)
    parser.add_argument("--attack", action="store_true", help="run the real live attack+fix pipeline afterward")
    parser.add_argument("--finding", type=int, default=0, help="index of the finding to attack (default: 0)")
    args = parser.parse_args()

    source = args.file.read_text()

    print("=" * 72)
    print(f"SCANNING {args.file}")
    print("=" * 72)

    print("\n--- Deterministic AST scan (fixed pattern list, instant, no network) ---")
    try:
        ast_findings = scan_source(source, str(args.file))
    except SyntaxError as exc:
        print(f"Not valid Python: {exc}", file=sys.stderr)
        sys.exit(1)
    if not ast_findings:
        print("  (nothing matched a known pattern)")

    print("\n--- AI scan (reads the code for meaning, real Groq call) ---")
    llm_result = scan_source_with_llm(source, str(args.file))
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
        _print_finding(i, f, source)

    if not args.attack:
        return

    if not all_findings:
        print("\nNo findings to attack.")
        return
    if args.finding >= len(all_findings):
        print(f"\n--finding {args.finding} is out of range (0-{len(all_findings) - 1})", file=sys.stderr)
        sys.exit(1)

    target = all_findings[args.finding]
    print(f"\n{'=' * 72}\nATTACKING finding [{args.finding}]: {target.symbol}() — live Groq call, no fallback")
    print("=" * 72)

    from integration.upload_pipeline import AttackGenerationUnavailable, verify_upload

    try:
        bundle = verify_upload(source=source, finding=target)
    except AttackGenerationUnavailable as exc:
        print(f"\nCould not generate a live attack: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nGenerated attack payload : {bundle.hypothesis.payload}")
    if bundle.confidence is not None:
        print(f"Model's stated confidence: {bundle.confidence:.0%}")
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


if __name__ == "__main__":
    main()
