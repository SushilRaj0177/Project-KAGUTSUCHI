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

from contracts import SecurityFinding, Severity, SensitiveOp
from integration.file_patch import SymbolNotFound, apply_function_fix
from integration.github_pr import GitHubPrError, open_fix_pr
from integration.upload_pipeline import AttackGenerationUnavailable, verify_upload
from server.jobs import get_job, start_job
from server.rate_limit import daily_rate_limit, rate_limit
from server.repo_scan import CloneFailed, InvalidRepoUrl, _parse_github_url, scan_repo
from system.analysis.ast_scan import LearnedSignature, scan_source
from system.analysis.llm_scan import DetectorProposal, scan_source_with_llm
from system.sandbox.docker_runner import SandboxUnavailableError
from system.sandbox.isolation_probe import run_isolation_probe

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


class LearnedSignatureIn(BaseModel):
    """An approved detector proposal, sent along with a scan request by
    the webapp (see webapp/lib/db.ts's listApprovedLearnedSignatures) so
    a human's Approve click on /detector-proposals starts actually being
    checked for immediately. Plain data - a dotted call name plus a
    rationale and severity - converted below into the same LearnedSignature
    shape ast_scan.py matches through its normal, taint-gated call-name
    lookup. Nothing here is ever executed as code."""

    class_name: str
    call_signature: str
    rationale: str
    severity_hint: str = "medium"


def _severity_from_hint(hint: str) -> Severity:
    return {"low": Severity.LOW, "high": Severity.HIGH}.get(hint.lower(), Severity.MEDIUM)


def _extra_signatures(items: list[LearnedSignatureIn]) -> dict[str, LearnedSignature]:
    return {
        item.call_signature: LearnedSignature(
            op=SensitiveOp.OTHER,
            rationale=f"{item.rationale} (community-approved detector: {item.class_name})",
            detector=f"learned.{item.class_name}",
            severity=_severity_from_hint(item.severity_hint),
        )
        for item in items
    }


class AnalyzeRequest(BaseModel):
    source: str
    file_path: str = "uploaded.py"
    learned_signatures: list[LearnedSignatureIn] = []


class DetectorProposalOut(BaseModel):
    """A candidate new deterministic detector, discovered by the LLM scan
    finding a vulnerability pattern outside ast_scan.py's fixed category
    list. Advisory only - see system/analysis/llm_scan.py's docstring for
    why this is never auto-applied to the real _SIGNATURES table, and
    scripts/promote_detector.py for the reviewed path to actually add one."""

    class_name: str
    call_signature: str
    rationale: str
    severity_hint: str
    source_file_path: str


def _proposal_out(proposal: DetectorProposal | None) -> DetectorProposalOut | None:
    if proposal is None:
        return None
    return DetectorProposalOut(
        class_name=proposal.class_name,
        call_signature=proposal.call_signature,
        rationale=proposal.rationale,
        severity_hint=proposal.severity_hint,
        source_file_path=proposal.source_file_path,
    )


class AnalyzeResponse(BaseModel):
    findings: list[SecurityFinding]
    new_detector_proposal: DetectorProposalOut | None = None


class VerifyRequest(BaseModel):
    source: str
    finding: SecurityFinding


class RepoAnalyzeRequest(BaseModel):
    repo_url: str
    ref: str | None = None  # branch/tag to scan instead of the default branch
    learned_signatures: list[LearnedSignatureIn] = []


class OpenPrRequest(BaseModel):
    repo_url: str
    file_path: str
    symbol: str
    original_source: str
    fixed_function_source: str
    finding_summary: str
    github_token: str
    base_branch: str | None = None


class OpenPrResponse(BaseModel):
    pr_url: str
    branch: str


class RepoAnalyzeResponse(BaseModel):
    owner: str
    repo: str
    files_scanned: int
    findings: list[SecurityFinding]
    sources: dict[str, str]
    truncated: bool
    new_detector_proposals: list[DetectorProposalOut] = []


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/debug/isolation-probe", dependencies=[Depends(rate_limit)])
def isolation_probe() -> dict:
    """TEMPORARY diagnostic - see system/sandbox/isolation_probe.py and
    scripts/probe_isolation.py. Answers one question: can THIS deployed
    host build a bespoke namespace/cgroup-based sandbox runtime, or does
    it hit the same wall Docker-in-Docker already hits here? Every check
    is side-effect-free (spawns short-lived child processes, cleans up
    any scratch files it creates) - safe to hit on a live deployment.

    Remove this route once you have your answer; it's meant to be
    curled once from the live URL, not to stay in the shipped API
    surface indefinitely. Rate-limited like every other endpoint, but
    deliberately not behind any secret - the information it reveals
    (which kernel namespaces/cgroups this process can touch) has
    reconnaissance value but isn't a secret in itself."""
    return run_isolation_probe().as_dict()


def _dedup_findings(findings: list[SecurityFinding]) -> list[SecurityFinding]:
    """ast_scan and llm_scan can both flag the same call site - keep the
    first (ast_scan's, since it runs first below and is the cheaper,
    deterministic signal) when they agree on file/symbol/sensitive_op."""
    seen: set[tuple[str, str, str]] = set()
    deduped: list[SecurityFinding] = []
    for finding in findings:
        key = (finding.file_path, finding.symbol, finding.sensitive_op.value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


@app.post("/api/analyze", response_model=AnalyzeResponse, dependencies=[Depends(rate_limit), Depends(daily_rate_limit)])
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """AST scan (deterministic, fixed pattern list) PLUS an LLM pass that
    reads the source for vulnerability classes the AST rules don't know
    about. Neither scan executes the uploaded source - only /api/verify
    ever runs anything, and only in the sandbox. The LLM's findings are
    not trusted on their own say-so: they flow into the same
    hypothesize -> attack -> verify pipeline as everything else, so a
    wrong LLM hunch comes back FALSE_POSITIVE rather than a false claim."""
    try:
        findings = scan_source(req.source, req.file_path, extra_signatures=_extra_signatures(req.learned_signatures))
    except SyntaxError as exc:
        raise HTTPException(status_code=400, detail=f"Not valid Python: {exc}") from exc
    llm_result = scan_source_with_llm(req.source, req.file_path)
    findings.extend(llm_result.findings)
    return AnalyzeResponse(
        findings=_dedup_findings(findings),
        new_detector_proposal=_proposal_out(llm_result.proposal),
    )


def _repo_analyze_response(result) -> RepoAnalyzeResponse:
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    findings = sorted(_dedup_findings(result.findings), key=lambda f: severity_rank.get(f.severity_hint.value, 3))
    return RepoAnalyzeResponse(
        owner=result.owner,
        repo=result.repo,
        files_scanned=result.files_scanned,
        findings=findings,
        sources=result.sources,
        truncated=result.truncated,
        new_detector_proposals=[p for p in (_proposal_out(p) for p in result.new_detector_proposals) if p],
    )


@app.post("/api/analyze-repo", response_model=RepoAnalyzeResponse, dependencies=[Depends(rate_limit), Depends(daily_rate_limit)])
def analyze_repo(req: RepoAnalyzeRequest) -> RepoAnalyzeResponse:
    """Clone a public GitHub repo and AST-scan every .py file in it.
    Never imports or executes anything from the repo.

    Synchronous - fine for a small repo, but a large one can take longer
    than the webapp's own serverless proxy route allows (a live 504, see
    COORDINATION.md). /api/analyze-repo/start below is the same scan run
    as a background job instead, for callers that can poll."""
    try:
        result = scan_repo(req.repo_url, req.ref, extra_signatures=_extra_signatures(req.learned_signatures))
    except InvalidRepoUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CloneFailed as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _repo_analyze_response(result)


class JobStartedResponse(BaseModel):
    job_id: str


class RepoAnalyzeJobStatus(BaseModel):
    status: str  # "running" | "done" | "error"
    result: RepoAnalyzeResponse | None = None
    error: str | None = None


@app.post("/api/analyze-repo/start", response_model=JobStartedResponse, dependencies=[Depends(rate_limit), Depends(daily_rate_limit)])
def analyze_repo_start(req: RepoAnalyzeRequest) -> JobStartedResponse:
    """Same scan as /api/analyze-repo, run in a background thread (see
    server/jobs.py). Returns a job id almost instantly regardless of how
    long the actual scan takes; poll /api/analyze-repo/jobs/{job_id} for
    the result."""

    def _do_scan() -> RepoAnalyzeResponse:
        result = scan_repo(req.repo_url, req.ref, extra_signatures=_extra_signatures(req.learned_signatures))
        return _repo_analyze_response(result)

    job_id = start_job(_do_scan)
    return JobStartedResponse(job_id=job_id)


@app.get("/api/analyze-repo/jobs/{job_id}", response_model=RepoAnalyzeJobStatus)
def analyze_repo_job_status(job_id: str) -> RepoAnalyzeJobStatus:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found (it may have finished a while ago and expired).")

    if job.status == "running":
        return RepoAnalyzeJobStatus(status="running")
    if job.status == "error":
        return RepoAnalyzeJobStatus(status="error", error=job.error or "Unknown error")
    return RepoAnalyzeJobStatus(status="done", result=job.result)


@app.post("/api/verify", dependencies=[Depends(rate_limit), Depends(daily_rate_limit)])
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
        "hypothesis_confidence": bundle.confidence,
    }


@app.post("/api/open-pr", response_model=OpenPrResponse, dependencies=[Depends(rate_limit), Depends(daily_rate_limit)])
def open_pr(req: OpenPrRequest) -> OpenPrResponse:
    """Deliver a verified fix as a real GitHub PR, instead of leaving it
    as a code block the user has to copy-paste themselves. `github_token`
    is used exactly once, right here, to make the GitHub API calls -
    never logged, never persisted, never returned in any response.

    `fixed_function_source` must be the SELF-CONTAINED single-function
    output of verify_upload()/propose_fix() (see integration/file_patch.py's
    docstring for why this can't just overwrite the whole file)."""
    try:
        owner, repo = _parse_github_url(req.repo_url)
    except InvalidRepoUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        patched_file = apply_function_fix(req.original_source, req.symbol, req.fixed_function_source)
    except SymbolNotFound as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        result = open_fix_pr(
            token=req.github_token,
            owner=owner,
            repo=repo,
            file_path=req.file_path,
            new_file_content=patched_file,
            symbol=req.symbol,
            finding_summary=req.finding_summary,
            base_branch=req.base_branch,
        )
    except GitHubPrError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return OpenPrResponse(pr_url=result.pr_url, branch=result.branch)
