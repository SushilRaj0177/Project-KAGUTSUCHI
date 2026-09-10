#!/usr/bin/env python3
"""
Turns an AI-discovered detector proposal (see system/analysis/llm_scan.py
and the /detector-proposals page) into a ready-to-review code snippet for
ast_scan.py's deterministic _SIGNATURES table.

Deliberately does NOT edit ast_scan.py itself. Auto-applying live,
LLM-derived output to the trusted static-analysis code path would be a
real self-modifying-code risk (a crafted repo could try to trick the
model into proposing a bogus or overly broad signature) - this project's
whole design principle is "the AI proposes, something deterministic and
reviewed disposes." A human (or a session acting on a human's behalf)
reads the printed snippet, judges whether the signature is real and
correctly scoped, adds it themselves, writes a test the same way every
other detector in this file has one, and only then confirms promotion.

Usage:
    # fetch a proposal from the live site by id (shown on /detector-proposals)
    python scripts/promote_detector.py <proposal-id> [--site-url URL]

    # or work fully offline from explicit values
    python scripts/promote_detector.py \\
        --class-name server_side_request_forgery \\
        --call-signature requests.get \\
        --rationale "..." --severity high

    # after manually adding the signature + a test, mark it promoted so
    # it drops off the pending list:
    python scripts/promote_detector.py <proposal-id> --confirm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

_DEFAULT_SITE_URL = os.environ.get("KAGUTSUCHI_SITE_URL", "http://localhost:3000")

# Best-fit existing SensitiveOp category, purely to suggest a starting
# point in the printed snippet - the reviewer should override this if it
# doesn't fit. New classes that don't fit any existing category should
# get their own SensitiveOp member (contracts/models.py) rather than
# being forced into "other" forever once there's more than one of them.
_CATEGORY_HINTS: dict[str, tuple[str, ...]] = {
    "NETWORK_EGRESS": ("request", "http", "url", "fetch", "ssrf", "socket"),
    "FILESYSTEM": ("path", "file", "extract", "tar", "zip", "traversal"),
    "AUTH_CHANGE": ("auth", "session", "token", "jwt", "permission", "password", "credential"),
    "DESERIALIZATION": ("deserial", "pickle", "yaml", "marshal", "unmarshal"),
    "SQL_QUERY": ("sql", "query", "database", "orm"),
    "SHELL_EXEC": ("shell", "command"),
    "SUBPROCESS": ("subprocess", "exec", "spawn"),
}


def _suggest_category(class_name: str, rationale: str) -> str:
    haystack = f"{class_name} {rationale}".lower()
    for category, keywords in _CATEGORY_HINTS.items():
        if any(kw in haystack for kw in keywords):
            return category
    return "OTHER"


def _fetch_proposal(proposal_id: str, site_url: str) -> dict:
    url = f"{site_url.rstrip('/')}/api/detector-proposals/{proposal_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310 - trusted, our own API
            return json.load(resp)
    except urllib.error.URLError as exc:
        print(f"Could not fetch proposal {proposal_id!r} from {url}: {exc}", file=sys.stderr)
        print("Pass --class-name/--call-signature/--rationale/--severity to work offline instead.", file=sys.stderr)
        sys.exit(1)


def _confirm_promoted(proposal_id: str, site_url: str) -> None:
    url = f"{site_url.rstrip('/')}/api/detector-proposals/{proposal_id}"
    req = urllib.request.Request(url, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            resp.read()
        print(f"Marked {proposal_id} as promoted - it will no longer show as pending.")
    except urllib.error.URLError as exc:
        print(f"Could not mark {proposal_id} as promoted: {exc}", file=sys.stderr)
        sys.exit(1)


def _print_snippet(class_name: str, call_signature: str, rationale: str, severity: str) -> None:
    category = _suggest_category(class_name, rationale)
    severity_const = {"low": "Severity.LOW", "medium": "Severity.MEDIUM", "high": "Severity.HIGH"}.get(
        severity, "Severity.MEDIUM"
    )
    print("=" * 72)
    print("Proposed ast_scan.py addition - REVIEW before adding, do not paste blind.")
    print("=" * 72)
    if category == "OTHER":
        print(
            f"\nNo existing SensitiveOp category fit well. Consider adding a new one to "
            f"contracts/models.py's SensitiveOp enum, e.g.:\n\n"
            f"    {class_name.upper()} = {class_name!r}\n"
        )
    print(f"\nSuggested _SIGNATURES entry (system/analysis/ast_scan.py):\n")
    print(f'    "{call_signature}": (')
    print(f"        SensitiveOp.{category},")
    print(f'        "{rationale}",')
    print(f'        "ast.{class_name}.{call_signature.replace(".", "_")}",')
    print("    ),")
    print(f"\nSuggested _SEVERITY_BY_OP entry, if this category is new:\n")
    print(f"    SensitiveOp.{category}: {severity_const},")
    print(
        f"\nAlso write a test (verification/tests/ or system/ tests) confirming a real "
        f"call to `{call_signature}` gets flagged, matching every existing detector's "
        f"pattern - a signature with no test is exactly the kind of unverified claim "
        f"this project doesn't ship elsewhere."
    )
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("proposal_id", nargs="?", help="Proposal id from /detector-proposals")
    parser.add_argument("--site-url", default=_DEFAULT_SITE_URL)
    parser.add_argument("--confirm", action="store_true", help="Mark this proposal as promoted (after you've added it yourself)")
    parser.add_argument("--class-name")
    parser.add_argument("--call-signature")
    parser.add_argument("--rationale")
    parser.add_argument("--severity", default="medium", choices=["low", "medium", "high"])
    args = parser.parse_args()

    if args.confirm:
        if not args.proposal_id:
            parser.error("--confirm requires a proposal_id")
        _confirm_promoted(args.proposal_id, args.site_url)
        return

    if args.proposal_id:
        proposal = _fetch_proposal(args.proposal_id, args.site_url)
        class_name = proposal["class_name"]
        call_signature = proposal["call_signature"]
        rationale = proposal["rationale"]
        severity = proposal["severity_hint"]
    else:
        if not (args.class_name and args.call_signature and args.rationale):
            parser.error("either a proposal_id, or all of --class-name/--call-signature/--rationale")
        class_name, call_signature, rationale, severity = (
            args.class_name,
            args.call_signature,
            args.rationale,
            args.severity,
        )

    _print_snippet(class_name, call_signature, rationale, severity)


if __name__ == "__main__":
    main()
