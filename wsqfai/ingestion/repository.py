"""
Repository ingestion: clone a public Git repository and produce a
RepositorySnapshot - file inventory, per-language breakdown, basic size
metrics. This is the first stage of the M1-M6 pipeline in ARCHITECTURE.md;
everything downstream (SQuaRE measurement, AI/ML quality extension,
security) reads from this snapshot rather than re-cloning or re-walking
the repository itself.

The clone/validation safety pattern (URL allowlist, ref validation,
--depth 1, a hard timeout, skip-list directories, per-file size cap) is
carried over from Project KAGUTSUCHI's server/repo_scan.py, which was
exercised against real public repositories in production - not
reinvented here, generalized from Python-only to any language.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

_GITHUB_URL_RE = re.compile(r"^https://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(\.git)?/?$")
_SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")

_SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "site-packages", "__pycache__",
    "dist", "build", "target", ".next", ".turbo", "vendor", "coverage",
}
_MAX_FILES = 5000
_MAX_FILE_BYTES = 500_000
_CLONE_TIMEOUT_S = 60

# Extension -> language label. Deliberately a flat, explicit map (not a
# heuristic/library dependency) so the classification a snapshot reports
# is always traceable to one line in this file.
_LANGUAGE_BY_EXTENSION: dict[str, str] = {
    ".py": "Python", ".pyi": "Python",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".java": "Java", ".kt": "Kotlin",
    ".go": "Go", ".rs": "Rust",
    ".rb": "Ruby", ".php": "PHP",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".hpp": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".sql": "SQL",
    ".sh": "Shell", ".bash": "Shell",
    ".yaml": "YAML", ".yml": "YAML",
    ".json": "JSON",
    ".md": "Markdown",
}


class InvalidRepoUrl(ValueError):
    """repo_url isn't a plain https://github.com/<owner>/<repo> URL, or ref
    isn't a safe branch/tag name."""


class CloneFailed(RuntimeError):
    """git clone failed or timed out."""


@dataclass
class FileRecord:
    path: str  # repository-relative, forward slashes
    language: str | None
    size_bytes: int
    line_count: int


@dataclass
class RepositorySnapshot:
    owner: str
    repo: str
    ref: str | None
    files: list[FileRecord] = field(default_factory=list)
    truncated: bool = False

    @property
    def files_by_language(self) -> dict[str, list[FileRecord]]:
        out: dict[str, list[FileRecord]] = {}
        for f in self.files:
            if f.language is not None:
                out.setdefault(f.language, []).append(f)
        return out

    @property
    def total_lines(self) -> int:
        return sum(f.line_count for f in self.files)

    def language_summary(self) -> dict[str, dict[str, int]]:
        """{"Python": {"files": 12, "lines": 3400}, ...}, sorted by lines
        descending - the shape a report/dashboard actually wants to render."""
        summary = {
            lang: {"files": len(records), "lines": sum(r.line_count for r in records)}
            for lang, records in self.files_by_language.items()
        }
        return dict(sorted(summary.items(), key=lambda kv: kv[1]["lines"], reverse=True))


def _parse_github_url(repo_url: str) -> tuple[str, str]:
    match = _GITHUB_URL_RE.match(repo_url.strip())
    if not match:
        raise InvalidRepoUrl("Expected a public GitHub repo URL like https://github.com/<owner>/<repo>")
    return match.group("owner"), match.group("repo")


def _clone(repo_url: str, dest: Path, ref: str | None) -> None:
    if ref is not None and not _SAFE_REF_RE.match(ref):
        raise InvalidRepoUrl(f"Not a valid branch/tag name: {ref!r}")
    cmd = ["git", "clone", "--depth", "1", "--single-branch"]
    if ref is not None:
        cmd += ["--branch", ref]
    cmd += [repo_url, str(dest)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=_CLONE_TIMEOUT_S, text=True)
    except subprocess.CalledProcessError as exc:
        raise CloneFailed(f"git clone failed (repo/branch may be private, deleted, or wrong): {exc.stderr.strip()}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CloneFailed("git clone timed out - repo is too large for a live ingest.") from exc


def _classify(path: Path) -> str | None:
    return _LANGUAGE_BY_EXTENSION.get(path.suffix.lower())


def _count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _snapshot_from_dir(root: Path, owner: str, repo: str, ref: str | None) -> RepositorySnapshot:
    files: list[FileRecord] = []
    truncated = False
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > _MAX_FILE_BYTES:
            continue
        count += 1
        if count > _MAX_FILES:
            truncated = True
            continue
        language = _classify(path)
        files.append(FileRecord(
            path=path.relative_to(root).as_posix(),
            language=language,
            size_bytes=size,
            line_count=_count_lines(path) if language is not None else 0,
        ))
    return RepositorySnapshot(owner=owner, repo=repo, ref=ref, files=files, truncated=truncated)


def ingest(repo_url: str, ref: str | None = None) -> RepositorySnapshot:
    """Clone `repo_url` (optionally at `ref`) into a scratch directory and
    return a RepositorySnapshot. The clone is always removed before this
    returns - nothing downstream should assume the working tree still
    exists on disk; re-clone (cheap, --depth 1) if raw file content is
    needed again later, rather than caching a path that may already be
    gone."""
    owner, repo = _parse_github_url(repo_url)
    with tempfile.TemporaryDirectory(prefix="wsqfai-ingest-") as tmp:
        root = Path(tmp)
        _clone(repo_url, root, ref)
        return _snapshot_from_dir(root, owner, repo, ref)
