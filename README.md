# Project KAGUTSUCHI

**Autonomous Code Integrity & Runtime Verification Engine**
Team CIPHER-X · Hack Summit 7.0 · Track: AI for Safety & Security

Kagutsuchi treats AI-generated code as untrusted until a targeted attack has
been executed, evidenced, remediated, and replayed. The LLM reasons
(hypothesizes attacks); the infrastructure verifies (executes, observes,
issues a binary verdict).

> An explanation is not an exploit, and "looks fixed" is not a verdict.

## Status: working, verified on real Docker

Three structurally different vulnerability classes run through the exact
same pipeline, with no per-class special-casing:

| Class | Fixture | Sink | Fix |
|---|---|---|---|
| Shell/command injection | `verification/fixtures/netdiag.py` | `os.system(f"ping ... {host}")` | allowlist + `subprocess.run(shell=False)` |
| SQL injection | `verification/fixtures/sql_injection.py` | `cursor.executescript(f"... {name}")` | parameterized `execute()` |
| Insecure deserialization | `verification/fixtures/insecure_deserialization.py` | `pickle.loads(...)` | `json.loads(...)` |

For each: an attack is generated (LLM + hardcoded fallback), run against the
vulnerable code in an isolated Docker sandbox, then replayed
**byte-identically** against the fixed code. All three have returned
`VERIFIED_FIXED` on a real Docker daemon (not mocked) — see
`COORDINATION.md` for the verification history.

## Try it

Needs Docker running. From the repo root:

```
pip install -r requirements.txt -r verification/requirements.txt
PYTHONPATH=. python -m integration.demo               # command injection
PYTHONPATH=. python -m integration.demo_sql            # SQL injection
PYTHONPATH=. python -m integration.demo_deserialize    # insecure deserialization
```

Each prints a `VerificationResult` — the verdict, confidence, and whether
the before/after replay used the identical payload.

A CLI is also available for scanning arbitrary code:

```
python -m system.cli.main analyze <file.py>       # whole-file scan
python -m system.cli.main analyze-diff <old> <new> <path>  # diff-scoped scan
python -m system.cli.main ingest <repo> <file> --base <rev> --head <rev>
```

## Web dashboard

`webapp/` is a real Next.js + Postgres dashboard (deployable to Vercel) that
displays actual verification runs — no sample/fake data. Publish a real run
to it with `integration/publish_result.py` once deployed. See
`webapp/README.md` for deployment steps.

## Architecture

```
system/analysis   --SecurityFinding-->   verification/hypothesis
verification/hypothesis  --AttackHypothesis-->   system/sandbox
system/sandbox    --ExecutionEvidence-->   verification/regression
verification/regression  --VerificationResult-->   system/orchestration
```

- **`system/`** (Sushil) — AST-based static analysis, git diff ingestion,
  the Docker sandbox, and orchestration. Never trusts an LLM's claim about
  safety — only executes and observes.
- **`verification/`** (Charanpreet) — vulnerable/fixed fixtures, LLM-driven
  attack hypothesis generation (Groq, with hardcoded fallbacks so the demo
  never depends on a live API call), and evidence-based verdict scoring.
- **`contracts/`** — the four shared types (`SecurityFinding`,
  `AttackHypothesis`, `ExecutionEvidence`, `VerificationResult`) that are the
  *only* integration surface between the two — see `contracts/CONTRACTS.md`.
- **`integration/`** (Sushil) — wires `system/` and `verification/` together
  end to end; the only module that imports from both.

## Team & ownership

| Person | Role | Owns |
|---|---|---|
| **Sushil Raj** (Team Lead) | System & Security Engineering | `system/`, `integration/`, `webapp/`, final demo |
| **Charanpreet Kaur** | Adversarial Verification & Evaluation | `verification/` — all three fixtures, attack hypothesis generation, regression/verdict logic |

Both workstreams integrate **only** through `contracts/` — never through a
shared working tree. See [`PLAN.md`](PLAN.md) for the build plan,
[`CONTRIBUTING.md`](CONTRIBUTING.md) for collaboration rules, and
[`COORDINATION.md`](COORDINATION.md) for the full build/verification log —
including two real bugs caught only by testing on real Docker (a
filesystem-noise false positive, and a cross-platform pickle
serialization bug), not by mocked tests alone.
