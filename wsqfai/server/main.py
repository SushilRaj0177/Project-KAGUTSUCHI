"""
The always-on backend behind a future WSQF-AI web frontend: takes a
public GitHub repo URL, runs the same ingest -> measure -> hypothesize ->
verify -> propose-fix pipeline `wsqfai.report` already proves out via its
own tests and the CLI, and returns the report as JSON. Also opens a real
GitHub pull request carrying whichever fixes the caller selects.

Design carried over deliberately from `engine-archive/kagutsuchi/server/main.py`,
which already solved the two real problems a public "paste a repo link"
tool actually has:
  - a repo scan can take longer than a typical serverless proxy's request
    timeout (this caused a live 504 in the original product) - solved by
    making it a background job the caller polls, not a synchronous request
  - a public, unauthenticated endpoint that clones repos and calls PyPI
    is a target for abuse - solved by per-IP rate limiting

Run with: uvicorn wsqfai.server.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from wsqfai.ingestion.repository import InvalidRepoUrl, ingest
from wsqfai.ingestion.repository import _parse_github_url as parse_github_url
from wsqfai.integration.github_pr import GitHubPrError, open_fix_pr
from wsqfai.remediation import Fix
from wsqfai.report import RepositoryReport, analyze_snapshot
from wsqfai.server.jobs import get_job, start_job
from wsqfai.server.rate_limit import daily_rate_limit, rate_limit

app = FastAPI(title="WSQF-AI API")

_allowed_origins = [
    origin.strip()
    for origin in os.environ.get("WSQFAI_ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


class RepoAnalyzeRequest(BaseModel):
    repo_url: str
    ref: str | None = None  # branch/tag to scan instead of the default branch


class JobStartedResponse(BaseModel):
    job_id: str


class RepoAnalyzeJobStatus(BaseModel):
    status: str  # "running" | "done" | "error"
    result: RepositoryReport | None = None
    error: str | None = None


def _run_analysis(repo_url: str, ref: str | None) -> RepositoryReport:
    snapshot = ingest(repo_url, ref=ref)
    return analyze_snapshot(snapshot)


@app.post("/api/analyze-repo/start", response_model=JobStartedResponse, dependencies=[Depends(rate_limit), Depends(daily_rate_limit)])
def analyze_repo_start(req: RepoAnalyzeRequest) -> JobStartedResponse:
    """Clone and analyze `req.repo_url` in a background thread (see
    wsqfai/server/jobs.py). Returns a job id almost instantly regardless
    of how long the scan takes; poll /api/analyze-repo/jobs/{job_id} for
    the result. Input validation (bad URL) fails fast, synchronously,
    since it's free - only the actual clone+scan runs in the background."""
    try:
        parse_github_url(req.repo_url)
    except InvalidRepoUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = start_job(lambda: _run_analysis(req.repo_url, req.ref))
    return JobStartedResponse(job_id=job_id)


@app.get("/api/analyze-repo/jobs/{job_id}", response_model=RepoAnalyzeJobStatus)
def analyze_repo_job_status(job_id: str) -> RepoAnalyzeJobStatus:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found (it may have finished a while ago and expired).")

    if job.status == "running":
        return RepoAnalyzeJobStatus(status="running")
    if job.status == "error":
        # CloneFailed's message is written to be user-safe (see
        # wsqfai.ingestion.repository) - fine to surface directly, unlike
        # an arbitrary internal exception string.
        detail = job.error if isinstance(job.error, str) else "Unknown error"
        return RepoAnalyzeJobStatus(status="error", error=detail)
    return RepoAnalyzeJobStatus(status="done", result=job.result)


class OpenPrRequest(BaseModel):
    repo_url: str
    fixes: list[Fix]
    github_token: str
    base_branch: str | None = None


class OpenPrResponse(BaseModel):
    pr_url: str
    branch: str


@app.post("/api/open-pr", response_model=OpenPrResponse, dependencies=[Depends(rate_limit), Depends(daily_rate_limit)])
def open_pr(req: OpenPrRequest) -> OpenPrResponse:
    """Deliver the selected fixes as a real GitHub PR, instead of leaving
    them as diffs the user has to copy-paste and apply themselves.
    `github_token` is used exactly once, right here, to make the GitHub
    API calls - never logged, never persisted, never returned in any
    response (see wsqfai/integration/github_pr.py's own docstring)."""
    if not req.fixes:
        raise HTTPException(status_code=400, detail="No fixes provided - nothing to open a PR for.")
    try:
        owner, repo = parse_github_url(req.repo_url)
    except InvalidRepoUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = open_fix_pr(
            token=req.github_token,
            owner=owner,
            repo=repo,
            fixes=req.fixes,
            base_branch=req.base_branch,
        )
    except GitHubPrError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return OpenPrResponse(pr_url=result.pr_url, branch=result.branch)
