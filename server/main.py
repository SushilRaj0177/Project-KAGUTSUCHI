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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from contracts import SecurityFinding
from integration.upload_pipeline import AttackGenerationUnavailable, verify_upload
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


@app.post("/api/verify")
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
