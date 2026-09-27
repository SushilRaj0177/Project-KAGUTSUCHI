# WSQF-AI

**An AI-systems extension of Waseda's Software Quality Framework methodology —
evidence-based dependability auditing, not an LLM's opinion of your code.**

> Status: active rebuild, milestone M0 (dismantle prior product, ground the
> new architecture) complete. See [`ROADMAP.md`](ROADMAP.md) for what's real
> today versus what's planned, and [`ARCHITECTURE.md`](ARCHITECTURE.md) for
> how every major design decision traces to a specific, cited piece of
> published research — not an invented rubric.

## What this is

WSQF-AI takes a software repository and produces a **dependability
assessment grounded in real standards**, not a static-analysis dashboard
wearing an AI badge:

- Quality characteristics measured against **ISO/IEC 25000 (SQuaRE)**, the
  same standard Prof. Hironori Washizaki's own **WSQF/WSQB** (Waseda
  Software Quality Framework/Benchmark, ICSE 2019) concretizes into
  measurable metrics — this project follows that same "measure the real
  characteristic, don't invent a score" discipline, extended to AI/ML
  repositories specifically.
- AI/ML-specific quality dimensions aligned to **ISO/IEC 25059**, the SQuaRE
  extension for AI systems (e.g. Functional Adaptability).
- **ML design-pattern detection** — Prof. Washizaki's own most distinctive
  research line (*Machine Learning Architecture and Design Patterns*,
  Computer 2022; ML reliability solution patterns, PLoP 2024) — recognizing
  and recommending established ML software patterns, not just flagging
  anti-patterns.
- Security findings that are **proven, not asserted**: reusing Project
  KAGUTSUCHI's real exploit-and-verify engine (see `engine-archive/`) so a
  finding means "we attacked it and it worked," framed through Washizaki &
  Yoshioka's **AI Security Continuum** (CAIN 2024) rather than generic
  OWASP language.
- Findings structured around **SWEBOK v4.0** knowledge areas (Quality,
  Security, Architecture, Testing, Maintenance) — the body of knowledge
  Prof. Washizaki personally edited for IEEE Computer Society in 2024.

## Why this exists

Full research synthesis and the reasoning behind every architectural choice
is in [`ARCHITECTURE.md`](ARCHITECTURE.md). Short version: this project
starts from Prof. Washizaki's actual, current, published work — not a
generic "AI code reviewer" idea with his name attached after the fact.

## Where the prior product went

This repository previously shipped **Project KAGUTSUCHI**, a narrower
exploit-and-verify security tool. It wasn't discarded — its real, tested
engine (Docker/Landlock sandbox, attack-hypothesis generation, verified-fix
delivery) is held in [`engine-archive/`](engine-archive/) and reconnects at
Milestone M4. See that directory's own README for exactly what's there and
where it's going.

## Repository layout

```
ARCHITECTURE.md      -- the research grounding + design rationale (read this first)
ROADMAP.md           -- milestones, what's built vs planned, honestly
engine-archive/       -- Project KAGUTSUCHI, dismantled and held for reuse
<new WSQF-AI code lands here as each milestone is built>
```
