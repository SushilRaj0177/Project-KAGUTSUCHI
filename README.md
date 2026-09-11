# Project KAGUTSUCHI

**Autonomous Code Security Verification — proof, not opinion.**
Team CIPHER-X

KAGUTSUCHI doesn't just flag vulnerabilities — it actually attacks them in
an isolated sandbox to prove they're real, then attacks the proposed fix
with the identical payload before ever calling it fixed. Nothing here is
trusted because an LLM asserted it; every verdict comes from an observed
result, not a claim.

> An explanation is not an exploit, and "looks fixed" is not a verdict.

## Live

- **Website**: paste any public GitHub repo and watch it scan, attack, and
  fix in real time — `/scan` (the tool), `/dashboard` (real usage, not
  sample data), `/compare` (diff two branches), `/calibration` (is the AI's
  confidence trustworthy?), `/detector-proposals` (AI-discovered
  vulnerability classes awaiting review).
- **One click to actually fix it**: a verified fix isn't just a code block —
  `/scan` can open a real GitHub pull request carrying it, straight from the
  browser (see `integration/github_pr.py`).
- **Repo scanning is asynchronous**: a large repo scan runs as a background
  job instead of one blocking request, so it can't 504 on a slow connection
  or a big codebase (see `server/jobs.py`).
- **Real-world function signatures**: the attack/fix harness handles
  functions taking more than one argument, not just the single-string-arg
  shape every hand-built fixture happens to have (see
  `system/orchestration/signature.py`).
- **Backend**: FastAPI, hosted on Render (falls back to a locked-down
  subprocess sandbox when Docker isn't reachable on the host — disclosed
  honestly in the UI whenever that's what ran).

## The pipeline

```
system/analysis        --SecurityFinding-->      verification/hypothesis
verification/hypothesis --AttackHypothesis-->     system/sandbox
system/sandbox          --ExecutionEvidence-->    verification/regression
verification/regression --VerificationResult-->   system/orchestration
```

Two detection engines feed the same pipeline:
1. **Deterministic AST scan** — matches a fixed table of dangerous call
   signatures. Instant, no network, no false negatives on what it knows.
2. **AI scan** — reads the code for *meaning*, catches classes the fixed
   list doesn't know about yet, and can propose a brand-new detector
   signature for human review at `/detector-proposals`. Never
   auto-applied: a human clicking Approve is what makes a proposal start
   being checked for on every future scan (as plain data — a dotted call
   name, matched through the exact same taint-gated logic as every
   built-in detector, never AI-authored code running unreviewed), and a
   human hand-writing it into `ast_scan.py` (see
   `scripts/promote_detector.py`) is what makes it permanent.

Every finding — from either engine — flows into the same
hypothesize → attack → verify loop. A wrong AI guess comes back
`FALSE_POSITIVE`; nothing gets a free pass because a model said so.

## Vulnerability classes covered

| Class | Fixture | Sink | Fix |
|---|---|---|---|
| Command injection | `verification/fixtures/netdiag.py` | `os.system(f"ping ... {host}")` | allowlist + `subprocess.run(shell=False)` |
| SQL injection | `verification/fixtures/sql_injection.py` | `cursor.executescript(f"... {name}")` | parameterized `execute()` |
| Insecure deserialization | `verification/fixtures/insecure_deserialization.py` | `pickle.loads(...)` | `json.loads(...)` |
| Path traversal | `verification/fixtures/path_traversal.py` | `os.path.join(base, filename)` silently discarding `base` on an absolute path | `os.path.realpath` + `commonpath` check |
| Unsafe tar extraction (CVE-2007-4559 class) | `verification/fixtures/tar_extraction.py` | `tarfile.extractall()` with no filter | resolve + validate each member's path before extracting |

Plus whatever the AI scanner discovers beyond this list — see
`/detector-proposals` and `scripts/promote_detector.py`.

## Where everything lives

| Path | What it is |
|---|---|
| `contracts/` | The four shared Pydantic models (`SecurityFinding`, `AttackHypothesis`, `ExecutionEvidence`, `VerificationResult`) — the **only** integration surface between `system/` and `verification/`. See `contracts/CONTRACTS.md`. |
| `system/analysis/ast_scan.py` | Deterministic AST scanner — the fixed-signature detection engine. |
| `system/analysis/llm_scan.py` | AI scanner — reads code for meaning, proposes new detector classes. |
| `system/orchestration/` | Builds a runnable script from a fixture/source + a target function, drives attack/replay through the sandbox. |
| `system/orchestration/signature.py` | Determines a function's real parameter count from source, so the harness can drive functions taking more than one argument instead of assuming exactly one. |
| `system/sandbox/docker_runner.py` | Real Docker sandbox — network-disabled, memory-capped, destroyed per run. |
| `system/sandbox/subprocess_runner.py` | Fallback sandbox (resource-limited subprocess, scrubbed env) used only when Docker isn't reachable. |
| `system/cli/main.py` | Typer CLI: `analyze`, `analyze-diff`, `ingest`, `verify`. |
| `verification/fixtures/` | The 5 vulnerable/fixed code pairs listed above. |
| `verification/hypothesis/generate.py` | Turns a `SecurityFinding` into a live attack payload (Groq), with per-class hardcoded fallbacks. |
| `verification/hypothesis/propose_fix.py` | Turns a proven-vulnerable finding into a proposed fix, AST-validated for self-containment before it's trusted to run. |
| `verification/hypothesis/groq_client.py` | Groq API wrapper — retries automatically (up to 3x, temperature nudged up each time) on a malformed generation before giving up. |
| `verification/regression/verify.py` | The actual verdict logic — deterministic marker-file comparison, not an LLM opinion. |
| `verification/calibration.py` | Scores the AI's stated confidence against real sandbox outcomes (Brier score) — powers `/calibration`. |
| `verification/attacks/` | Payload variants per fixture (proof each vulnerability is exploitable more than one way) and a local (non-sandboxed, dev-only) attack runner. |
| `integration/upload_pipeline.py` | The real-product path: arbitrary uploaded source + a finding → full attack/fix/verify. Powers `/api/verify`. |
| `integration/pipeline.py` | The fixture-demo path: known vulnerable/fixed pair → full verification, used by `integration/demo*.py`. |
| `integration/demo.py`, `demo_sql.py`, `demo_deserialize.py` | One-shot end-to-end demos per fixture, fallback-hypothesis based (no API key needed). |
| `integration/publish_result.py` | Publishes a real pipeline run to the live dashboard's database. |
| `integration/file_patch.py` | Splices a verified fix's self-contained function back into its original file, preserving everything else (imports, decorators, other functions). |
| `integration/github_pr.py` | Opens a real GitHub PR carrying a verified fix — the only place in the codebase that talks to GitHub's write API. |
| `server/main.py` | FastAPI app — `/api/analyze`, `/api/analyze-repo` (+ `/start` and `/jobs/{id}` for the async version), `/api/verify`, `/api/open-pr`, `/api/health`. |
| `server/repo_scan.py` | Clones a public GitHub repo and scans every `.py` file (AST on all, AI on a capped concurrent subset). |
| `server/jobs.py` | In-memory background job runner backing `/api/analyze-repo/start` — turns a slow scan into a poll instead of one long blocking request. |
| `server/rate_limit.py` | Per-IP, per-endpoint rate limiting — a short window (stops a retry storm) and a daily one (stops a script quietly burning the whole day's Groq quota). |
| `webapp/app/page.tsx` | Landing page — what the project is, why the name, what it does. |
| `webapp/app/scan/` | The scanning tool itself (paste a repo, see findings, attack one). |
| `webapp/app/dashboard/` | Live Runs — real completed verifications from actual site usage. |
| `webapp/app/compare/` | Diffs findings between two branches/refs of the same repo. |
| `webapp/app/calibration/` | The AI-confidence-vs-reality page, backed by `verification/calibration.py`'s method. |
| `webapp/app/detector-proposals/` | AI-discovered vulnerability classes awaiting human review/promotion. |
| `webapp/app/api/backend/` | Server-side proxy routes to the FastAPI backend (avoids browser CORS entirely). |
| `webapp/lib/db.ts` | Postgres schema + queries (`runs`, `repo_scan_cache`, `detector_proposals` tables). |
| `scripts/demo_scan.py` | Interactive CLI demo console — scan, attack, calibration, and discovery, all from one menu. |
| `scripts/promote_detector.py` | Turns an accepted AI-proposed detector into a ready-to-review `ast_scan.py` code snippet. |
| `scripts/start_live_demo.sh` | Runs the backend with real Docker + a Cloudflare Tunnel, for environments (like Codespaces) where you want the real sandbox instead of the fallback. |
| `tests/`, `verification/tests/` | The automated test suite (176 passing as of this build). |
| `COORDINATION.md` | Append-only cross-session build log — every merge, every bug found, every design decision, in order. |

## Try it

**Interactive console (recommended, needs `GROQ_API_KEY` for the AI/attack steps):**
```
pip install -r requirements.txt -r server/requirements.txt -r verification/requirements.txt
PYTHONPATH=. python scripts/demo_scan.py
```

**One-shot fixture demos (no API key needed, uses hardcoded fallback hypotheses):**
```
PYTHONPATH=. python -m integration.demo               # command injection
PYTHONPATH=. python -m integration.demo_sql            # SQL injection
PYTHONPATH=. python -m integration.demo_deserialize    # insecure deserialization
```

**CLI for scanning arbitrary code:**
```
python -m system.cli.main analyze <file.py>
python -m system.cli.main analyze-diff <old> <new> <path>
```

All of the above work without Docker — they fall back to the subprocess
sandbox automatically and say so in the output.

## Team & ownership

| Person | Role | Owns |
|---|---|---|
| **Sushil Raj** (Team Lead) | System & Security Engineering | `system/`, `integration/`, `webapp/`, `server/`, `scripts/`, final demo |
| **Charanpreet Kaur** | Adversarial Verification & Evaluation | `verification/` — fixtures, attack hypothesis generation, fix proposal, calibration, regression/verdict logic |

Both workstreams integrate **only** through `contracts/` — never through a
shared working tree. See [`PLAN.md`](PLAN.md) for the build plan,
[`CONTRIBUTING.md`](CONTRIBUTING.md) for collaboration rules, and
[`COORDINATION.md`](COORDINATION.md) for the full build/verification log.
