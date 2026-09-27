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

from wsqfai.report import analyze_repository, render_html, render_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wsqfai",
        description="WSQF-AI: evidence-based dependability auditing for a public GitHub repository.",
    )
    parser.add_argument("repo_url", help="https://github.com/<owner>/<repo>")
    parser.add_argument("--ref", default=None, help="branch or tag to scan (default: the repository's default branch)")
    parser.add_argument("--format", choices=("text", "json", "html"), default="text", help="output format (default: text)")
    parser.add_argument("--json", action="store_true", help="shorthand for --format json")
    parser.add_argument("--html", action="store_true", help="shorthand for --format html")
    parser.add_argument(
        "--patch", action="store_true",
        help="print only the proposed fixes as one unified diff (git apply -p1 the output against a clone of the repo)",
    )
    args = parser.parse_args(argv)
    fmt = "json" if args.json else "html" if args.html else args.format

    report = analyze_repository(args.repo_url, ref=args.ref)
    if args.patch:
        print(report.combined_patch(), end="")
    elif fmt == "json":
        print(report.model_dump_json(indent=2))
    elif fmt == "html":
        print(render_html(report))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
