# Working rules for this project

## Current top priority: get the live site actually working

Before adding any more features, coverage, or polish: get
`webapp/app/analyze` on the deployed site to actually complete a real scan
against a real backend, end to end, for a real visitor. Everything else
in "Build-merge-continue loop" below still applies, but "the next
highest-value item" always means "whatever gets the live site from
broken to working" until it demonstrably works - confirmed by actually
using the live URL, not by a local test passing. Once it works, resume
picking from ROADMAP.md's "Immediately next" as usual, and keep
expanding/hardening every aspect of it (breadth, robustness, coverage)
from that working baseline rather than around it.

## Build-merge-continue loop

The default operating mode on this project is autonomous, checkpointed
building:

- Work happens on a feature branch, gets committed, pushed, and opened as
  a PR (subscribe to it for CI/review activity).
- After a PR is opened, pause new feature work — don't start the next
  checkpoint while one is still awaiting merge.
- **The moment a PR of mine is merged, that is the standing green light
  to immediately continue building the next checkpoint** — do not wait
  for an explicit "keep building" message each time. Pick the next
  highest-value, honestly-scoped item (see ROADMAP.md's "Immediately
  next" section) and start it.
- Still stop and ask (or just report status) if genuinely blocked: an
  architectural decision only the user can make, ambiguous scope, or a
  CI/review situation the babysit/steward rules say to escalate.
- A user message telling me to pause (e.g. "pause after a few
  checkpoints") overrides this until they say otherwise.

## Tone and framing (hard-learned)

Ground claims in cited standards/papers (ISO/IEC 25010/25059, SWEBOK,
specific papers), not in a tribute narrative around any one named
researcher. Prof. Washizaki's work is *grounding*, not the subject of the
product. Keep UI polish tasteful and restrained — subtle, not "insane" —
even when asked for lots of animation.

## Honesty discipline

Every ROADMAP checkbox is backed by real, tested code and (where
practical) a real end-to-end run against live data — never checked off
because a plan exists. When a bug is found, document it in ROADMAP.md
the same way prior bugs are documented (what broke, why tests didn't
catch it, the fix, the regression test).
