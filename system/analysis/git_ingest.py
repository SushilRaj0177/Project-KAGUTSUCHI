"""
Git ingestion: pull a file's content at two revisions straight from git,
so 'detect' can run against a real commit instead of two manually
prepared files.
"""
from __future__ import annotations

import subprocess


class GitIngestError(RuntimeError):
    """Raised when git can't produce the requested file content (bad ref,
    file not in that revision, not a git repo, etc.)."""


def read_file_at_revision(repo_path: str, revision: str, file_path: str) -> str:
    """Return the content of `file_path` as it existed at `revision`
    (e.g. 'HEAD', 'HEAD~1', a commit sha) inside the git repo at
    `repo_path`. Raises GitIngestError if the file didn't exist there."""
    result = subprocess.run(
        ["git", "-C", repo_path, "show", f"{revision}:{file_path}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitIngestError(
            f"git show {revision}:{file_path} failed: {result.stderr.strip()}"
        )
    return result.stdout


def diff_pair(repo_path: str, file_path: str, base: str = "HEAD~1", head: str = "HEAD") -> tuple[str, str]:
    """Convenience: return (old_content, new_content) for `file_path`
    between `base` and `head`. A file newly added at `head` yields an
    empty string for old_content rather than raising."""
    try:
        old = read_file_at_revision(repo_path, base, file_path)
    except GitIngestError:
        old = ""
    new = read_file_at_revision(repo_path, head, file_path)
    return old, new
