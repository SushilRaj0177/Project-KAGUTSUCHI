# WSQF-AI

**An AI-systems extension of Waseda's Software Quality Framework methodology —
evidence-based dependability auditing, not an LLM's opinion of your code.**

> Status: active rebuild, real and runnable. M0 (dismantle prior product,
> ground the new architecture), M1 (quality/evidence model + real repo
> ingestion), M2a+ (Maintainability + Reliability measurement), M3a
> (ML-repository detection + a Washizaki-catalogued ML-pattern check), and
> M4a (AST-based security hypothesis generation) are built, tested, and
> wired into one CLI you can run against any public GitHub repo today. See
> [`ROADMAP.md`](ROADMAP.md) for exactly what's real versus what's still
> planned — every checkbox there is backed by tested code, none by a plan —
> and [`ARCHITECTURE.md`](ARCHITECTURE.md) for how every major design
> decision traces to a specific, cited piece of published research, not an
> invented rubric.

## Try it

```bash
git clone <this repo> && cd Project-KAGUTSUCHI
pip install -e .
wsqfai https://github.com/pallets/flask
```

(`wsqfai` is a console-script entry point installed by `pip install -e .`;
`python -m wsqfai <repo-url>` works identically if you'd rather not rely on
your `PATH` having picked it up.)

Real output from that exact command, against Flask's actual source, on the
`M4a` build:

```
WSQF-AI report for pallets/flask
236 files, 18803 lines
Top languages: Python (83 files, 18345 lines), YAML (8 files, 249 lines), Markdown (6 files, 153 lines), SQL (2 files, 28 lines), JSON (2 files, 21 lines)
ML-containing repository: no

Findings: 10
  high: 1
  medium: 9
  [HIGH] reliability/fault_tolerance: Bare 'except:' clause(s) in src/flask/app.py (src/flask/app.py)
  [MEDIUM] maintainability/modularity: Large file reduces modularity: src/flask/cli.py (src/flask/cli.py)
  [MEDIUM] maintainability/modularity: Large file reduces modularity: src/flask/app.py (src/flask/app.py)
  [MEDIUM] maintainability/modularity: Large file reduces modularity: src/flask/sansio/app.py (src/flask/sansio/app.py)
  [MEDIUM] maintainability/modularity: Large file reduces modularity: tests/test_basic.py (tests/test_basic.py)
  [MEDIUM] maintainability/modularity: Large file reduces modularity: tests/test_blueprints.py (tests/test_blueprints.py)
  [MEDIUM] reliability/fault_tolerance: Swallowed exception(s) in src/flask/config.py (src/flask/config.py)
  [MEDIUM] reliability/fault_tolerance: Swallowed exception(s) in tests/test_reqctx.py (tests/test_reqctx.py)
  [MEDIUM] reliability/fault_tolerance: Swallowed exception(s) in tests/test_basic.py (tests/test_basic.py)
  [MEDIUM] reliability/fault_tolerance: Swallowed exception(s) in tests/test_appctx.py (tests/test_appctx.py)

Security hypotheses (unverified static AST match, not sandbox-proven — see M4b in ROADMAP.md): 1
  [HIGH] deserialization: exec executes arbitrary Python from its argument. (call: exec, line 209) (src/flask/config.py:209)
```

Every line there is a real Finding or Observation, each citing an exact
file, an exact ISO/IEC 25010 sub-characteristic, and (for the security
hypothesis) an honest label that it's a static pattern match, not yet a
sandbox-proven exploit. Add `--json` for the full machine-readable report,
or `--ref <branch>` to scan a specific branch/tag instead of the default.

Run `PYTHONPATH=. python3 -m pytest tests/ -q` to run all 92 tests.

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
ARCHITECTURE.md          -- the research grounding + design rationale (read this first)
ROADMAP.md               -- milestones, what's built vs planned, honestly
engine-archive/          -- Project KAGUTSUCHI, dismantled and held for reuse
wsqfai/
  domain/                -- the ISO/IEC 25010+25059 quality model, Finding/Evidence/Observation
  ingestion/             -- real repo cloning + file/language classification
  measurement/           -- Maintainability, Reliability, ML-pattern metrics (M2a/M2b/M3a)
  security/              -- AST-based sensitive-operation scanner (M4a)
  report.py, __main__.py -- the end-to-end report + `python -m wsqfai` CLI
tests/                   -- 92 tests, mirroring wsqfai/'s package structure
```
