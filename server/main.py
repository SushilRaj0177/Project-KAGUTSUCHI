"""
The always-on backend: lets a real user upload arbitrary Python source,
runs the same detect -> hypothesize -> attack -> replay -> verdict
pipeline the fixtures use, and returns real, sandboxed evidence.

Two endpoints, stateless by design (no DB, no session) so a single
long-running process behind a tunnel is enough for the hackathon:

  POST /api/analyze  - AST-only, never executes anything. Returns the
                        SecurityFinding list for the uploaded source.
  POST /api/verify    - Takes the uploaded source back PLUS one finding
                        from /api/analyze's response, and actually runs
                        the attack (and, if it lands, a fix attempt) in
                        the Docker sandbox. This is the only endpoint
                        that executes anything, and only ever inside
                        system/sandbox's network-disabled container.

Run with: uvicorn server.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from contracts import SecurityFinding
from integration.upload_pipeline import AttackGenerationUnavailable, verify_upload
from server.rate_limit import rate_limit
from server.repo_scan import CloneFailed, InvalidRepoUrl, scan_repo
from system.analysis.ast_scan import scan_source
from system.sandbox.docker_runner import SandboxUnavailableError

app = FastAPI(title="KAGUTSUCHI upload API")

_allowed_origins = [
    origin.strip()
    for origin in os.environ.get("KAGUTSUCHI_ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    source: str
    file_path: str = "uploaded.py"


class AnalyzeResponse(BaseModel):
    findings: list[SecurityFinding]


class VerifyRequest(BaseModel):
    source: str
    finding: SecurityFinding


class RepoAnalyzeRequest(BaseModel):
    repo_url: str


class RepoAnalyzeResponse(BaseModel):
    owner: str
    repo: str
    files_scanned: int
    findings: list[SecurityFinding]
    sources: dict[str, str]
    truncated: bool


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Pure AST scan. Never imports or executes the uploaded source."""
    try:
        findings = scan_source(req.source, req.file_path)
    except SyntaxError as exc:
        raise HTTPException(status_code=400, detail=f"Not valid Python: {exc}") from exc
    return AnalyzeResponse(findings=findings)


@app.post("/api/analyze-repo", response_model=RepoAnalyzeResponse, dependencies=[Depends(rate_limit)])
def analyze_repo(req: RepoAnalyzeRequest) -> RepoAnalyzeResponse:
    """Clone a public GitHub repo and AST-scan every .py file in it.
    Never imports or executes anything from the repo."""
    try:
        result = scan_repo(req.repo_url)
    except InvalidRepoUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CloneFailed as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    findings = sorted(result.findings, key=lambda f: severity_rank.get(f.severity_hint.value, 3))

    return RepoAnalyzeResponse(
        owner=result.owner,
        repo=result.repo,
        files_scanned=result.files_scanned,
        findings=findings,
        sources=result.sources,
        truncated=result.truncated,
    )


@app.post("/api/verify", dependencies=[Depends(rate_limit)])
def verify(req: VerifyRequest) -> dict:
    """Attack the finding for real, in the Docker sandbox, then (if it
    lands) attempt and replay a fix. Only endpoint that executes anything."""
    try:
        bundle = verify_upload(source=req.source, finding=req.finding)
    except AttackGenerationUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SandboxUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "finding": bundle.finding.model_dump(mode="json"),
        "hypothesis": bundle.hypothesis.model_dump(mode="json"),
        "before": bundle.before.model_dump(mode="json"),
        "fixed_source": bundle.fixed_source,
        "after": bundle.after.model_dump(mode="json") if bundle.after else None,
        "result": bundle.result.model_dump(mode="json") if bundle.result else None,
        "fix_error": bundle.fix_error,
    }
