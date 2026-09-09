# Project KAGUTSUCHI

**Autonomous Code Integrity & Runtime Verification Engine**
Team CIPHER-X · Hack Summit 7.0 · Track: AI for Safety & Security

Kagutsuchi treats AI-generated code as untrusted until a targeted attack has
been executed, evidenced, remediated, and replayed. The LLM reasons
(hypothesizes attacks); the infrastructure verifies (executes, observes,
issues a binary verdict).

> An explanation is not an exploit, and "looks fixed" is not a verdict.

## Team & ownership

| Person | Role | Owns |
|---|---|---|
| **Sushil Raj** (Team Lead) | System & Security Engineering | `system/`, `integration/`, final demo |
| **Charanpreet Kaur** | Adversarial Verification & Evaluation | `verification/` |

Both workstreams integrate **only** through the versioned types in
[`contracts/`](contracts/CONTRACTS.md) — never through a shared working
tree. See [`PLAN.md`](PLAN.md) for the full build plan and
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the collaboration rules that keep
two independent Claude Code sessions from stepping on each other.

## Status

Planning phase. No application code yet — see `PLAN.md` for the P0 (36-hour
demo) milestones.
