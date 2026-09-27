"""
CLI entry point: `python -m wsqfai <github-url>`.

Clones a public GitHub repository, runs every measurement and security
module built so far against it, and prints a report. This is the
project's first genuinely runnable demonstration, not just a test suite -
see wsqfai/report.py's docstring for what it does and doesn't claim yet.
"""
from __future__ import annotations

import argparse
import sys

from wsqfai.report import analyze_repository, render_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wsqfai",
        description="WSQF-AI: evidence-based dependability auditing for a public GitHub repository.",
    )
    parser.add_argument("repo_url", help="https://github.com/<owner>/<repo>")
    parser.add_argument("--ref", default=None, help="branch or tag to scan (default: the repository's default branch)")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON instead of a text summary")
    args = parser.parse_args(argv)

    report = analyze_repository(args.repo_url, ref=args.ref)
    print(report.model_dump_json(indent=2) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
