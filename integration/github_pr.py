"""Open a real GitHub pull request carrying a verified fix.

Deliberately the ONLY place in this codebase that talks to GitHub's
write API. Takes a personal access token per-call, uses it exactly once
to make the handful of API calls a PR needs, and never logs, stores, or
echoes it back anywhere - not even in an exception message. This is the
MVP path (see COORDINATION.md); a proper GitHub OAuth App can replace
"paste a token" with "sign in with GitHub" later without changing
anything below the token itself.
"""
from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass

import requests

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


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _request(method: str, url: str, token: str, **kwargs) -> dict:
    try:
        resp = requests.request(method, url, headers=_headers(token), timeout=_TIMEOUT_S, **kwargs)
    except requests.RequestException as exc:
        raise GitHubPrError(f"Could not reach GitHub: {_redact(token, str(exc))}") from exc

    if resp.status_code == 401:
        raise GitHubPrError("GitHub rejected the token — it's invalid or expired.")
    if resp.status_code == 403:
        raise GitHubPrError(
            "GitHub refused this action (403) — the token likely lacks 'repo' write "
            "scope, or you don't have push access to this repository."
        )
    if resp.status_code == 404:
        raise GitHubPrError(
            "GitHub returned 404 — either the repo doesn't exist, it's private and the "
            "token can't see it, or the target branch/file doesn't exist."
        )
    if not resp.ok:
        detail = resp.text[:300]
        raise GitHubPrError(f"GitHub API error {resp.status_code}: {_redact(token, detail)}")

    return resp.json() if resp.content else {}


def open_fix_pr(
    *,
    token: str,
    owner: str,
    repo: str,
    file_path: str,
    new_file_content: str,
    symbol: str,
    finding_summary: str,
    base_branch: str | None = None,
) -> OpenedPr:
    """Creates a branch off `base_branch` (or the repo's default branch),
    commits `new_file_content` at `file_path` on it, and opens a PR back
    into `base_branch`. Raises GitHubPrError on any failure - callers
    should surface that message as-is, it's already safe and specific."""
    if not token:
        raise GitHubPrError("No GitHub token provided.")

    repo_info = _request("GET", f"{_API_ROOT}/repos/{owner}/{repo}", token)
    base = base_branch or repo_info.get("default_branch", "main")

    base_ref = _request("GET", f"{_API_ROOT}/repos/{owner}/{repo}/git/ref/heads/{base}", token)
    base_sha = base_ref["object"]["sha"]

    new_branch = f"kagutsuchi-fix/{symbol}-{uuid.uuid4().hex[:8]}"
    _request(
        "POST",
        f"{_API_ROOT}/repos/{owner}/{repo}/git/refs",
        token,
        json={"ref": f"refs/heads/{new_branch}", "sha": base_sha},
    )

    # Contents API needs the file's current blob sha on the branch being
    # written to update it (omitting `sha` would mean "create," which
    # 422s on a file that already exists) - the new branch starts
    # identical to base, so base's sha is also correct here.
    existing = _request(
        "GET",
        f"{_API_ROOT}/repos/{owner}/{repo}/contents/{file_path}",
        token,
        params={"ref": base},
    )
    file_sha = existing.get("sha")

    commit_message = f"Fix {symbol}: {finding_summary}"[:250]
    _request(
        "PUT",
        f"{_API_ROOT}/repos/{owner}/{repo}/contents/{file_path}",
        token,
        json={
            "message": commit_message,
            "content": base64.b64encode(new_file_content.encode("utf-8")).decode("ascii"),
            "sha": file_sha,
            "branch": new_branch,
        },
    )

    pr_body = (
        f"Automated fix from [KAGUTSUCHI](https://github.com/) for a vulnerability "
        f"found in `{symbol}` ({file_path}).\n\n"
        f"**What was wrong:** {finding_summary}\n\n"
        f"This fix was proven, not just proposed: the same real exploit that broke "
        f"the original code was replayed against this fix in an isolated sandbox, "
        f"and it no longer succeeds. Please review before merging like any other PR."
    )
    pr = _request(
        "POST",
        f"{_API_ROOT}/repos/{owner}/{repo}/pulls",
        token,
        json={
            "title": f"[KAGUTSUCHI] Fix {symbol} — verified vulnerability patch",
            "head": new_branch,
            "base": base,
            "body": pr_body,
        },
    )

    return OpenedPr(pr_url=pr["html_url"], branch=new_branch)
