# Engine archive

This directory holds **Project KAGUTSUCHI** — the prior product this repository
shipped — dismantled but not discarded. Every component in here is real,
tested, working code (193 passing tests, a live deployment, a real Docker/
Landlock sandbox that actually exploits and re-verifies fixes). None of it
is a prototype or a demo; it's proven infrastructure being held for reuse
rather than rebuilt from scratch.

## Why it's here instead of deleted

The project's direction changed: from a narrow (5 vulnerability classes)
exploit-and-verify tool into **WSQF-AI**, a dependability/quality auditor
whose architecture is grounded explicitly in Prof. Hironori Washizaki's
published research (SQuaRE/ISO 25000, his WSQF/WSQB benchmark methodology,
ISO/IEC 25059's AI quality extensions, SWEBOK v4, and his ML design-pattern
research) — see `/ARCHITECTURE.md` and `/ROADMAP.md` at the repo root.

Kagutsuchi's exploit-and-verify engine isn't obsolete under that new
direction — it's the single most technically credible thing to reuse:
"prove a security finding is real by actually attacking it, then prove a
fix by attacking it again" is exactly the kind of evidence-based rigor
WSQF-AI's whole thesis depends on. Rebuilding that from zero would mean
throwing away real, working, tested infrastructure to re-derive something
strictly weaker in the short term.

## What's here

| Path | What it is | Where it reconnects |
|---|---|---|
| `kagutsuchi/system/sandbox/` | Real Docker sandbox + Landlock-based unprivileged fallback confinement | M4 (Security layer) |
| `kagutsuchi/system/analysis/` | Deterministic AST scanner + AI/LLM scanner, including the detector-proposal closed loop | M4 (Security layer) |
| `kagutsuchi/verification/` | Attack-hypothesis generation, regression/verdict logic, calibration | M4 (Security layer) |
| `kagutsuchi/integration/` | Upload pipeline, GitHub PR delivery, file patching | M4 (Security layer) + M6 (remediation delivery) |
| `kagutsuchi/server/` | FastAPI app wiring the above into HTTP endpoints | Superseded by WSQF-AI's own API surface; kept for reference and reusable route patterns |
| `kagutsuchi/webapp/` | The full Next.js frontend (rebuilt this session — scan flow, GitHub OAuth, EN/JP i18n, dashboard, calibration, compare, detector-proposals) | Reference implementation for M6 (dashboard); several components (auth, i18n infra, sandbox probe) are directly reusable |
| `kagutsuchi/deploy/` | Real VPS + free self-hosted deployment paths for genuine sandbox isolation | M4, once the security layer needs a real Docker host again |
| `kagutsuchi/tests/`, `kagutsuchi/scripts/` | The engine's test suite and CLI/demo tooling | Alongside their respective code above |
| `kagutsuchi/COORDINATION.md`, `PLAN.md` | The full build/decision log from the Kagutsuchi era | Historical record — not superseded, just from the prior chapter |

## Rule while this stays archived

Nothing in here should be treated as "the current architecture." New code
under WSQF-AI's own structure (see repo root) is what's live. This archive
gets *read from* — copied, adapted, or imported — at the milestones noted
above, never edited in place as if it were still the active product.
