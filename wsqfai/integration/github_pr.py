"""
Open a real GitHub pull request carrying one or more real, mechanically
generated fixes (wsqfai.remediation.Fix) - re-platformed from
`engine-archive/kagutsuchi/integration/github_pr.py`, where opening a real
PR from a verified fix was already built and working.

Deliberately the ONLY place in this codebase that talks to GitHub's write
API. Takes a personal access token per-call, uses it exactly once to make
the handful of API calls a PR needs, and never logs, stores, or echoes it
back anywhere - not even in an exception message. This is the same
"paste a token" MVP path the archived version used; a proper GitHub OAuth
flow can replace the token itself later without changing anything below
it.

Adapted from the original in one real way: the archived version patched
exactly one file per call (it only ever fixed one function at a time).
wsqfai's remediation engine can produce multiple independent Fixes across
multiple files in one run (an unpinned dependency here, a bare except
there), so this version commits every fix onto one branch and opens a
single PR describing all of them - a person reviewing one PR with three
related fixes is a better experience than three separate PRs for the same
scan.

Uses the standard library's urllib rather than the `requests` package -
wsqfai has no HTTP client dependency yet (see remediation.py's PyPI
lookup, which made the same choice), and this doesn't need one either.
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass

from wsqfai.remediation import Fix

_API_ROOT = "https://api.github.com"
_TIMEOUT_S = 15.0


class GitHubPrError(RuntimeError):
    """Raised for any failure talking to GitHub. The message is safe to
    show to a user - it never includes the token (see _redact below)."""


@dataclass
class OpenedPr:
    pr_url: str
    branch: str


def _redact(token: str, text: str) -> str:
    return text.replace(token, "***") if token else text


def _request(method: str, url: str, token: str, *, json_body: dict | None = None, params: dict | None = None) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_S) as response:  # noqa: S310 - a fixed, hardcoded host
            body = response.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = _redact(token, exc.read().decode("utf-8", errors="replace")[:300])
        if exc.code == 401:
            raise GitHubPrError("GitHub rejected the token — it's invalid or expired.") from exc
        if exc.code == 403:
            raise GitHubPrError(
                "GitHub refused this action (403) — the token likely lacks 'repo' write "
                "scope, or you don't have push access to this repository."
            ) from exc
        if exc.code == 404:
            raise GitHubPrError(
                "GitHub returned 404 — either the repo doesn't exist, it's private and the "
                "token can't see it, or the target branch/file doesn't exist."
            ) from exc
        raise GitHubPrError(f"GitHub API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise GitHubPrError(f"Could not reach GitHub: {_redact(token, str(exc))}") from exc


def _pr_body(fixes: list[Fix]) -> str:
    lines = [
        "Automated fixes from [WSQF-AI](https://github.com/) — evidence-based dependability "
        "auditing extending Prof. Hironori Washizaki's Waseda Software Quality Framework.",
        "",
        f"**{len(fixes)} fix(es) applied:**",
        "",
    ]
    for fix in fixes:
        lines.append(f"- `{fix.file_path}` — {fix.summary}")
    lines += [
        "",
        "Each fix above is mechanically generated from this repository's own file content - "
        "not a generic snippet. Please review before merging like any other PR.",
    ]
    return "\n".join(lines)


def open_fix_pr(
    *,
    token: str,
    owner: str,
    repo: str,
    fixes: list[Fix],
    base_branch: str | None = None,
) -> OpenedPr:
    """Creates a branch off `base_branch` (or the repo's default branch),
    commits every fix's patched content onto it, and opens a PR back into
    `base_branch` describing all of them. Raises GitHubPrError on any
    failure - callers should surface that message as-is, it's already
    safe and specific. Raises ValueError if `fixes` is empty - there's
    nothing to open a PR for."""
    if not token:
        raise GitHubPrError("No GitHub token provided.")
    if not fixes:
        raise ValueError("open_fix_pr() needs at least one Fix.")

    repo_info = _request("GET", f"{_API_ROOT}/repos/{owner}/{repo}", token)
    base = base_branch or repo_info.get("default_branch", "main")

    base_ref = _request("GET", f"{_API_ROOT}/repos/{owner}/{repo}/git/ref/heads/{base}", token)
    base_sha = base_ref["object"]["sha"]

    new_branch = f"wsqfai-fix/{uuid.uuid4().hex[:8]}"
    _request(
        "POST",
        f"{_API_ROOT}/repos/{owner}/{repo}/git/refs",
        token,
        json_body={"ref": f"refs/heads/{new_branch}", "sha": base_sha},
    )

    for fix in fixes:
        # Contents API needs the file's current blob sha on the branch
        # being written to update it (omitting `sha` would mean "create,"
        # which 422s on a file that already exists) - the new branch
        # starts identical to base, so base's sha is also correct here.
        existing = _request(
            "GET",
            f"{_API_ROOT}/repos/{owner}/{repo}/contents/{fix.file_path}",
            token,
            params={"ref": base},
        )
        file_sha = existing.get("sha")

        _request(
            "PUT",
            f"{_API_ROOT}/repos/{owner}/{repo}/contents/{fix.file_path}",
            token,
            json_body={
                "message": f"Fix {fix.file_path}: {fix.summary}"[:250],
                "content": base64.b64encode(fix.patched_content.encode("utf-8")).decode("ascii"),
                "sha": file_sha,
                "branch": new_branch,
            },
        )

    file_list = ", ".join(fix.file_path for fix in fixes)
    pr = _request(
        "POST",
        f"{_API_ROOT}/repos/{owner}/{repo}/pulls",
        token,
        json_body={
            "title": f"[WSQF-AI] {len(fixes)} fix(es): {file_list}"[:250],
            "head": new_branch,
            "base": base,
            "body": _pr_body(fixes),
        },
    )

    return OpenedPr(pr_url=pr["html_url"], branch=new_branch)
