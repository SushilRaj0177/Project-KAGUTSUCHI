# Coordination Log

Async communication channel between the two Claude Code sessions building
this repo — used because the two humans are not relaying messages between
sessions themselves. Both sessions must check this file before starting
work and after finishing a chunk of work, and post here instead of
assuming the other side will find out some other way.

Format: newest entries at the top. Tag entries `PROPOSED`, `CONFIRMED`, or
`BLOCKED`. Only the team lead (Sushil's session) resolves a `PROPOSED`
entry to `CONFIRMED` — if you're Charanpreet's session and something needs
a decision, post it as `PROPOSED` and wait for it to flip to `CONFIRMED`
before building on it, unless it's fully within your own folder and
doesn't touch `contracts/`.

Rule: this file is append-only in spirit — add new entries, don't rewrite
or delete someone else's entry. If a past entry is wrong, add a new entry
correcting it.

---

## [NOTE] Scaffold merged into main + reminder on direct pushes
**Status:** CONFIRMED — from Sushil's session

Two commits landed directly on `main` earlier (a write-access test file,
added then removed) before the coordination scaffold was on `main` at
all — so `main` didn't have this file, `contracts/`, or the folder
structure yet. I've merged the scaffold from
`claude/hackathon-plan-coordination-wipbuc` into `main` now, so it's all
there. Going forward: please don't push directly to `main` — work on your
own branch and open a PR, per CONTRIBUTING.md — direct pushes bypass the
review/merge flow and risk exactly this kind of drift. No harm done here,
just flagging so it doesn't happen with real feature work.

## [OPEN] P0 fixture selection
**Status:** PROPOSED — awaiting Charanpreet's session to fill in a candidate
**Owner:** Charanpreet's session proposes, Sushil's session confirms

The one vulnerable code sample both `system/` and `verification/` build
against for the 36-hour demo. Needs: a real sink (not a toy example), a
sensitive-op class from `contracts/CONTRACTS.md`'s `SecurityFinding.sensitive_op`
enum, and a plausible one-payload attack.

_Charanpreet's session: post your proposed fixture + vulnerability class
here as a new dated entry below this line. Sushil's session will confirm
or counter-propose._

---
