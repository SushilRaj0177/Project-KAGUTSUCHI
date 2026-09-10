"""
Clone a public GitHub repo and run the AST scanner (system/analysis) over
every Python file in it. This is what makes the site's headline feature —
"paste a repo URL, get real vulnerabilities back" — work on ANY public
repo, not just our own fixtures.

Only ever clones and reads text. Never imports or executes anything from
the target repo outside the Docker sandbox (that only happens later, per
finding, via integration.upload_pipeline.verify_upload).
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from contracts import SecurityFinding
from system.analysis.ast_scan import scan_source
from system.analysis.llm_scan import scan_source_with_llm

_GITHUB_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(\.git)?/?$"
)

_SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "env", "site-packages", "__pycache__", "dist", "build"}
_MAX_FILES = 300
_MAX_FILE_BYTES = 300_000
_CLONE_TIMEOUT_S = 30
# The AST pass is free and instant so it runs on every file up to
# _MAX_FILES; the LLM pass is a real network call per file, so it's
# capped separately to keep a repo scan from firing hundreds of Groq
# calls and blowing past latency/rate limits. Still covers the files most
# likely to matter, since findings.py sorts by severity afterward anyway.
_MAX_LLM_FILES = 15


class InvalidRepoUrl(ValueError):
    """Raised when repo_url isn't a plain https://github.com/<owner>/<repo> URL."""


class CloneFailed(RuntimeError):
    """Raised when `git clone` fails or times out."""


@dataclass
class ScannedFile:
    file_path: str
    source: str


@dataclass
class RepoScanResult:
    owner: str
    repo: str
    files_scanned: int
    findings: list[SecurityFinding]
    sources: dict[str, str]  # file_path -> source, only for files with findings
    truncated: bool  # True if the repo had more matching files than _MAX_FILES


def _parse_github_url(repo_url: str) -> tuple[str, str]:
    match = _GITHUB_URL_RE.match(repo_url.strip())
    if not match:
        raise InvalidRepoUrl(
            "Expected a public GitHub repo URL like https://github.com/<owner>/<repo>"
        )
    return match.group("owner"), match.group("repo")


def _clone(repo_url: str, dest: Path) -> None:
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", repo_url, str(dest)],
            check=True,
            capture_output=True,
            timeout=_CLONE_TIMEOUT_S,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise CloneFailed(
            f"git clone failed (repo may be private, deleted, or the URL is wrong): {exc.stderr.strip()}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CloneFailed("git clone timed out — repo is too large for a live scan.") from exc


def _iter_python_files(root: Path):
    """Yields matching files up to _MAX_FILES, then keeps counting (without
    reading file contents) so the caller can tell whether the cap actually
    truncated the scan rather than just happening to match the file count."""
    count = 0
    for path in root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.stat().st_size > _MAX_FILE_BYTES:
            continue
        count += 1
        if count <= _MAX_FILES:
            yield path
    if count > _MAX_FILES:
        yield None  # sentinel: more matching files existed than the cap


def scan_repo(repo_url: str) -> RepoScanResult:
    owner, repo = _parse_github_url(repo_url)

    with tempfile.TemporaryDirectory(prefix="kagutsuchi-repo-") as tmp:
        root = Path(tmp)
        _clone(repo_url, root)

        findings: list[SecurityFinding] = []
        sources: dict[str, str] = {}
        files_scanned = 0
        truncated = False

        for path in _iter_python_files(root):
            if path is None:
                truncated = True
                continue
            rel_path = str(path.relative_to(root))
            try:
                source = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            files_scanned += 1
            try:
                file_findings = scan_source(source, rel_path)
            except SyntaxError:
                continue
            if files_scanned <= _MAX_LLM_FILES:
                file_findings = file_findings + scan_source_with_llm(source, rel_path)
            if file_findings:
                findings.extend(file_findings)
                sources[rel_path] = source

        return RepoScanResult(
            owner=owner,
            repo=repo,
            files_scanned=files_scanned,
            findings=findings,
            sources=sources,
            truncated=truncated,
        )
