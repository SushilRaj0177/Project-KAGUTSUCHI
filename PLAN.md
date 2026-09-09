# Build Plan — Kagutsuchi (P0: 36-hour demo)

## Scope discipline (from the deck)

> One excellent, deterministic verification loop beats twenty unreliable
> vulnerability classes.

P0 = **one** team-owned vulnerable fixture, taken end-to-end through:
`ingest → detect → hypothesis → attack → evidence → fix → replay → verified`.
Everything else is P1+ and out of scope until that loop is solid.

Degrade-don't-die targets (design to these, don't build fallbacks for them
yet unless time allows): LLM down → deterministic fixture still runs;
dashboard down → CLI still verifies; seccomp/eBPF missing → container
boundary alone still holds.

## Recommended stack (proposal — confirm before either side starts)

- **Language:** Python 3.11+ for both workstreams (fastest path to
  Tree-sitter/AST bindings, Docker SDK, and an OpenAI-compatible LLM client).
- **Contracts:** Pydantic models mirroring `contracts/CONTRACTS.md`,
  living in `contracts/` and imported by both sides (not copy-pasted).
- **CLI:** Typer or argparse — CLI is the canonical interface per the deck
  ("if the UI fails, the pipeline still runs").
- **Sandbox:** `docker` Python SDK, P0 isolation only (no seccomp/eBPF yet).
- **LLM:** Groq API (free tier, e.g. Llama 3.3 70B or similar hosted model)
  for hypothesis generation — reasons only, never executes. Chosen over a
  paid API to keep the hackathon build at zero cost. Groq's free tier has
  rate limits — cache/hardcode the P0 demo fixture's hypothesis output as
  a fallback so a live rate-limit hit doesn't kill the demo (this is the
  same "degrade, don't die" principle as the LLM-down case above).
- **Dashboard (stretch):** whatever's fastest to stand up read-only over
  the CLI's JSON output — not on the P0 critical path.

If either of you disagrees with this stack, raise it now — changing it
after modules exist is expensive.

## Milestones

### Phase 0 — Setup (hour 0–2, parallel)
- [Sushil] Confirm stack, scaffold `system/` module boundaries, pick and
  commit **one** real vulnerable fixture class to target for P0 (e.g. shell
  command injection) so both sides build against the same target.
- [Charanpreet] Confirm contract fields work for her hypothesis/attack
  generation approach; flag any needed changes to `contracts/CONTRACTS.md`
  immediately (see `CONTRIBUTING.md` §3).

### Phase 1 — Independent build (hour 2–20, parallel, no cross-folder edits)

**System swimlane (Sushil):**
1. `system/analysis` — parse a git diff, extract the changed function via
   AST/Tree-sitter, tag it against the sensitive-op taxonomy → emit
   `SecurityFinding`.
2. `system/sandbox` — Docker-isolated execution: take a payload (from
   `AttackHypothesis`), run it against the candidate code, capture
   stdout/stderr/exit code/fs diff → emit `ExecutionEvidence`. No network
   egress from the container.
3. `system/orchestration` + `system/cli` — wire analysis → sandbox, expose
   as a CLI command, so the system half is independently testable with a
   hand-written fake `AttackHypothesis` before verification/ is ready.

**Verification swimlane (Charanpreet):**
1. `verification/fixtures` — the one team-owned vulnerable fixture (real
   sink, not a scanner demo) agreed in Phase 0, plus its fixed version.
2. `verification/hypothesis` — given a `SecurityFinding`, use the LLM to
   produce one concrete, deterministic `AttackHypothesis` (not a fuzzer).
3. `verification/evidence` + `verification/regression` — given a pair of
   `ExecutionEvidence` (before/after), compare against
   `expected_if_vulnerable` / `expected_if_safe` and emit a
   `VerificationResult`. Independently testable with hand-written fake
   `ExecutionEvidence` before system/ is ready.

Both sides should be able to fully unit-test their half using **hand-built
fake contract objects** — that's the point of the contract boundary. Don't
wait on the other person to start testing your own module.

### Phase 2 — Integration (hour 20–28, Sushil only, in `integration/`)
- Wire real `system/` output into real `verification/` input and back.
- Run the full loop on the agreed fixture: before (vulnerable) → attack →
  evidence → fix → replay (after) → verdict.
- Fix seam issues (they should be small if `contracts/` was respected).

### Phase 3 — Hardening + demo prep (hour 28–34)
- Both: fix bugs surfaced by integration, in your own folder only.
- Sushil: CLI output polish (this is the artifact judges see if UI fails).
- Stretch: minimal dashboard reading the CLI's JSON output, if time allows.

### Phase 4 — Demo rehearsal (hour 34–36)
- Full dry run of the 8-step demo flow from the deck: ingest → detect →
  hypothesis → attack → evidence → fix → replay → verified.
- Confirm the "signature" moment works live: exploit succeeds before,
  identical payload fails after — not just an LLM asserting safety.

## Definition of done for P0

- One real vulnerable fixture, one real fix, one real adversarial payload.
- The *exact same* payload is replayed before and after (byte-identical —
  this is the credibility claim of the whole project).
- Verdict is binary and evidence-backed, not LLM self-assessment.
- CLI runs the full loop standalone, no dashboard required.
