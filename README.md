# WSQF-AI

**An AI-systems extension of Waseda's Software Quality Framework methodology —
evidence-based dependability auditing, not an LLM's opinion of your code.**

> Status: active rebuild, real and runnable. M0 (dismantle prior product,
> ground the new architecture), M1 (quality/evidence model + real repo
> ingestion), M2a+ (Maintainability + Reliability + Portability
> measurement), M3a (ML-repository detection + a Washizaki-catalogued
> ML-pattern check), M4a+M4b (AST-based security hypothesis generation,
> actually sandbox-verified — a kernel-confined subprocess really attempts
> the exploit before any Security Finding is minted), M5a (a WSQF/WSQB-
> style corpus-comparison methodology), and M7a (real auto-fix diffs, not
> just findings) are built, tested, and wired into one CLI you can run
> against any public GitHub repo today. See
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

Real output from that exact command, against Flask's actual source:

```
WSQF-AI report for pallets/flask
236 files, 19188 lines
Top languages: Python (83 files, 18345 lines), TOML (5 files, 385 lines), YAML (8 files, 249 lines), Markdown (6 files, 153 lines), SQL (2 files, 28 lines)
ML-containing repository: no

Findings: 13
  high: 1
  medium: 12
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
  [MEDIUM] portability/installability: Unpinned dependencies in examples/tutorial/pyproject.toml (examples/tutorial/pyproject.toml)
  [MEDIUM] portability/installability: Unpinned dependencies in examples/celery/pyproject.toml (examples/celery/pyproject.toml)
  [MEDIUM] portability/installability: Unpinned dependencies in examples/javascript/pyproject.toml (examples/javascript/pyproject.toml)

Security hypotheses (raw static AST matches — a confirmed one is also promoted to a Finding above; see M4b in ROADMAP.md): 1
  [HIGH] deserialization: exec executes arbitrary Python from its argument. (call: exec, line 209) (src/flask/config.py:209)

Fixes proposed (real diffs — see --patch to get them as an applyable file): 1
  src/flask/app.py: Narrowed bare 'except:' to 'except Exception:' so SystemExit/KeyboardInterrupt/GeneratorExit propagate normally.
```

`wsqfai https://github.com/pallets/flask --patch` gives that fix as a real,
applyable diff, generated from Flask's own actual file content — not a
generic snippet:

```diff
--- a/src/flask/app.py
+++ b/src/flask/app.py
@@ -1601,7 +1601,7 @@
             except Exception as e:
                 error = e
                 response = self.handle_exception(ctx, e)
-            except:
+            except Exception:
                 error = sys.exc_info()[1]
                 raise
             return response(environ, start_response)
```

Flask's `exec()` call stays a hypothesis, honestly: M4b's sandbox
verification only covers one mechanically reconstructible shape so far (a
direct single-parameter shell-exec call), and `deserialization` isn't it
yet. Run it against code that *is* that shape and the sandbox actually
proves the exploit instead of just flagging the pattern:

```
WSQF-AI report for demo/netdiag-example
1 files, 6 lines
Top languages: Python (1 files, 6 lines)
ML-containing repository: no

Findings: 2
  critical: 2
  [CRITICAL] maintainability/testability: Few or no test files detected (.)
  [CRITICAL] security/integrity: Proven command injection in ping_host() (netdiag.py)

Security hypotheses (raw static AST matches — a confirmed one is also promoted to a Finding above; see M4b in ROADMAP.md): 1
  [HIGH] shell_exec: os.system runs its argument through the shell — string-built input here is a classic command injection sink. (call: os.system, line 6) (netdiag.py:6)
```

That `security/integrity` Finding isn't asserted from the pattern match —
`wsqfai/security/verify.py` actually built a runnable copy of
`ping_host()`, ran it in a Landlock-confined subprocess with an injection
payload, and only minted the Finding because the sandbox proved the
injected command executed. Point the exact same static pattern at a
function that validates its input first, and the sandbox correctly clears
it instead (see `tests/security/test_verify.py`).

Add `--json` for the full machine-readable report, `--format html` for a
self-contained HTML page, `--patch` to get every proposed fix as one
`git apply`-able diff, or `--ref <branch>` to scan a specific branch/tag
instead of the default.

Run `PYTHONPATH=. python3 -m pytest tests/ -q` to run all 221 tests (install
with `pip install -e ".[server]"` first if you want the 10 FastAPI server
tests included — the base install doesn't need FastAPI at all).

To run the real backend behind a future web frontend:

```bash
pip install -e ".[server]"
uvicorn wsqfai.server.main:app --reload
```

`POST /api/analyze-repo/start` kicks off a background scan and returns a
`job_id`; poll `GET /api/analyze-repo/jobs/{job_id}` for the result — the
same design the archived Kagutsuchi backend used to avoid a real 504 it
hit in production when a scan took longer than a serverless proxy's
request timeout. `POST /api/open-pr` opens a real GitHub pull request
carrying the fixes you select.

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
- Security findings that are **proven, not asserted**: a static match is
  labeled a hypothesis, not a Finding, until a Landlock-confined sandbox
  actually attempts the exploit and proves it — re-platforming Project
  KAGUTSUCHI's real exploit-and-verify engine (see `engine-archive/`) so a
  finding means "we attacked it and it worked," not "an AST pattern
  matched somewhere." AI Security Continuum (Washizaki & Yoshioka, CAIN
  2024)-based framing for these findings is a planned next step (M4c),
  not yet built.
- Findings structured around **SWEBOK v4.0** knowledge areas (Quality,
  Security, Architecture, Testing, Maintenance) — the body of knowledge
  Prof. Washizaki personally edited for IEEE Computer Society in 2024.
- **Fixes, not just findings**: for the handful of issues with an
  unambiguous, mechanical fix, WSQF-AI generates a real diff from the
  repository's own file content — `wsqfai <repo> --patch` gives you
  something to `git apply`, not another list to read and act on by hand.
  Everything else stays a Finding you decide how to act on, honestly —
  a fake fix would be worse than no fix.
- **A real backend, not just a CLI**: `wsqfai/server/` is an actual FastAPI
  service (background-job scanning so a slow clone can't 504 a request,
  per-IP rate limiting, and an endpoint that opens a real GitHub pull
  request carrying the selected fixes) — the API a "paste a repo link"
  website would call. The website itself (reconnecting
  `engine-archive/kagutsuchi/webapp`'s frontend) is the next milestone,
  not yet built.

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
  measurement/           -- Maintainability, Reliability, Portability, ML-pattern metrics (M2a/M2b/M3a)
  security/              -- AST hypothesis scanner (M4a) + hardcoded-credential detection + sandbox verification (M4b)
  benchmark.py           -- WSQF/WSQB-style corpus-comparison methodology (M5a)
  reference_corpus.py    -- curated default corpus to benchmark against, with caching (M5b)
  remediation.py         -- real auto-fix diffs for mechanically-fixable findings (M7a)
  integration/           -- opens a real GitHub PR carrying selected fixes (M7c-backend)
  server/                -- the FastAPI backend behind a future web frontend (M7c-backend)
  report.py, __main__.py -- the end-to-end report + `wsqfai` CLI (text/JSON/HTML/patch)
tests/                   -- 221 tests, mirroring wsqfai/'s package structure
```
