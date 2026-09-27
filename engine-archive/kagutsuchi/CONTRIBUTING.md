# Collaboration rules

Two people, two separate Claude Code sessions, one repo, 36-hour clock. The
rules below exist so neither session ever has to guess what the other is
doing or resolve a conflict mid-build.

## 1. Folder ownership is absolute

| Path | Owner | The other person |
|---|---|---|
| `system/**` | Sushil | never edits |
| `verification/**` | Charanpreet | never edits |
| `dashboard/**` | assigned later, once P0 core is done | — |
| `contracts/**` | Sushil (seed), shared | propose changes, don't unilaterally rewrite |
| `integration/**` | Sushil | never edits |
| `docs/`, root files (`README.md`, `PLAN.md`, `CONTRIBUTING.md`) | Sushil | never edits |

If a task seems to need touching the other person's folder, it doesn't —
it means the interface belongs in `contracts/` instead. Raise it with the
team lead (Sushil, via this chat) rather than reaching across the boundary.

## 2. Branches

- `main` — protected. Only the team lead's session merges into it.
- Sushil's session works on `claude/hackathon-plan-coordination-wipbuc` (this branch) for `system/`, `contracts/` seed, and later `integration/`.
- Charanpreet's session works on its own branch (whatever it's named — no
  need to match Sushil's naming) for `verification/` only.
- Each session opens a PR from its branch into `main` scoped to its own
  folder. Neither human is relaying approvals — Sushil's session reviews
  and merges both PRs itself, acting with Sushil's authority, without
  waiting for a manual human click. Charanpreet's session should not merge
  its own PR into `main` even if it looks ready — open it and let Sushil's
  session merge it.
- Nobody force-pushes `main`. Nobody rewrites the other person's branch history.

## 3. Changing `contracts/`

`contracts/CONTRACTS.md` (and later its schema file) is the only shared
surface. A field rename/type change there breaks the other person's
in-progress code silently. So:

1. Don't edit `contracts/` to unblock yourself without saying so.
2. Post the proposed change in this chat (Sushil) / your session (Charanpreet reports to Sushil via the team lead).
3. Sushil applies the change, bumps the version note at the top of the file, and both sides re-sync.

Additive changes (new optional field) are low-risk and can be called out
after the fact. Renames/removals/type changes are not.

## 4. Integration happens in one place

Neither workstream is "done" in isolation — they're done when
`system/sandbox` can take a `verification/hypothesis`-generated
`AttackHypothesis` and produce evidence that `verification/regression` can
score. That wiring lives in `integration/` and is built **only** by the
team lead, only after both sides have working, independently-tested
modules that speak the `contracts/` types. Don't try to pre-wire your own
half against guesses about the other half's internals — build to the
contract, hand off, let the lead connect it.

## 5. Commit hygiene

- Prefix commits with your initials during the hackathon so `git log` is
  scannable across two people, e.g. `[SR] add AST diff extractor`.
- Small, frequent commits over one giant end-of-day commit — the team lead
  needs to be able to pull partial progress at any point to integrate early.
- Don't commit secrets, API keys, or `.env` files — Docker sandbox config
  and any LLM API keys go through environment variables, documented in
  `docs/` (never hardcoded).

## 6. If something looks blocked

Stop and say so rather than working around it by touching another folder
or silently changing a contract. Losing 10 minutes to ask is cheaper than
losing an hour to a merge that can't be reconciled before the demo.

## 7. Cross-session communication (no human relay)

The two humans are not manually relaying messages between the two Claude
Code sessions. Use [`COORDINATION.md`](COORDINATION.md) as the async
channel instead: check it before starting work and post to it — new
dated entries, never edit someone else's — for any decision that crosses
the folder boundary (fixture choice, a proposed `contracts/` change, a
question about the other side's module). Anything that's fully inside
your own folder and doesn't touch `contracts/` doesn't need a
`COORDINATION.md` entry — just build it.
