# Roadmap

Honest status tracking — a milestone is only checked off once it's real,
tested code, the same standard the rest of this project holds itself to.
No milestone is marked done because a plan for it exists.

- [x] **M0 — Dismantle & inventory.** Project KAGUTSUCHI's engine (sandbox,
      analysis, verification, integration, webapp, deploy tooling, tests)
      moved intact into `engine-archive/kagutsuchi/`, with a README mapping
      each piece to the milestone that reintroduces it. Nothing deleted;
      nothing left half-migrated. New repo root established with
      `ARCHITECTURE.md` grounding every future decision in cited,
      verifiable research.
- [x] **M1 — Foundation.** `wsqfai/domain/quality_model.py`: ISO/IEC
      25010:2011's 8 characteristics + real sub-characteristics, plus
      ISO/IEC 25059:2023's AI-specific additions (Functional Adaptability,
      User Controllability, Transparency, Intervenability, Societal and
      Ethical Risk Mitigation), each sourced and cited, not invented.
      `wsqfai/domain/evidence.py`: the canonical `Finding` / `Evidence` /
      `Observation` / `AIAssessment` model — a Finding must cite a real,
      correctly-scoped sub-characteristic and at least one Evidence item,
      enforced by validation, not convention.
      `wsqfai/ingestion/repository.py`: real repo cloning (safety pattern
      carried over from KAGUTSUCHI's proven server/repo_scan.py, extended
      from Python-only to any language) and file/language classification.
      19 tests, including one real end-to-end clone against a live public
      GitHub repo (skipped, not faked, if network is unavailable).
- **M2 — SQuaRE quality measurement.** Deterministic measurement of real
      SQuaRE product-quality characteristics — each metric traceable to the
      specific sub-characteristic it measures. Split honestly into slices
      rather than checked off as one lump, since only one slice is real so
      far:
  - [x] **M2a — Maintainability slice.** `wsqfai/measurement/maintainability.py`:
        deterministic, structural metrics against a `RepositorySnapshot`
        for three Maintainability sub-characteristics — Modularity
        (god-file line-count thresholds, the same order of magnitude
        Checkstyle/PMD use by default), Analysability (average
        characters-per-line, catching minified/generated code a human or
        AI reader would struggle with), and Testability (ratio of
        test-file-convention matches to code files, explicitly labelled a
        structural proxy, not real coverage). Every Finding cites a real
        `sub_characteristic_key` and at least one Evidence item pointing
        at the file(s) that produced it. 12 tests, including one real
        end-to-end run against a live cloned public repo. Deliberately
        scoped to what `RepositorySnapshot` can measure without
        re-reading file content (path/language/size/line-count only) —
        see the module's own docstring for why that's a stated
        limitation, not an oversight.
  - **M2b — Remaining SQuaRE characteristics.** Reliability, Performance
        Efficiency, Compatibility, Usability, Portability. Started, not
        finished:
    - [x] **Reliability (Fault Tolerance).** `wsqfai/measurement/reliability.py`:
          real Python AST-based detection (not text/regex matching, which
          would misfire inside strings/comments) of bare `except:` clauses
          (HIGH — catches SystemExit/KeyboardInterrupt/GeneratorExit too,
          not just the intended fault) and swallowed `except Exception`/
          `except BaseException` handlers whose body is only `pass` (MEDIUM
          — a fault occurred and the system proceeds as if it hadn't). A
          broad handler that logs, re-raises, or returns is correctly left
          unflagged — the breadth of the catch isn't the problem, silently
          discarding the fault is. 9 tests.
    - [x] **Portability (Installability).** `wsqfai/measurement/portability.py`:
          detects fully unpinned dependencies in `requirements.txt` and
          `pyproject.toml`'s `[project.dependencies]` (parsed with the
          stdlib `tomllib`, not regex) — a dependency with no version
          operator at all can silently resolve to a different, untested
          version on a fresh install, ISO/IEC 25010's Installability
          sub-characteristic. Deliberately narrow: any version operator at
          all (even a loose `>=`) is treated as constrained, since the
          goal is catching completely unconstrained dependencies, the
          clearest low-false-positive signal, not grading pin strictness.
          9 tests.
    - [ ] Performance Efficiency, Compatibility, Usability — not started.
          Each needs its own honest scoping pass; Performance Efficiency in
          particular can't be measured from static source alone at all —
          it needs a profiling run, not a source read.
- **M3 — AI/ML quality extension.** ISO/IEC 25059 characteristics for
      ML-containing repositories, plus the ML design-pattern
      detection/recommendation engine, grounded in Washizaki et al.'s own
      catalogue (IEEE Computer, Vol. 55 No. 3, March 2022: 12 ML
      architecture patterns, 13 ML design patterns, 8 ML anti-patterns,
      itself building on Sculley et al.'s "Hidden Technical Debt in
      Machine Learning Systems", NeurIPS 2015). Split into slices for the
      same reason M2 was:
  - [x] **M3a — ML-repository detection + ML Versioning check.**
        `wsqfai/measurement/ml_patterns.py`: `is_ml_repository()` detects
        real, direct imports of a general-purpose ML/DL framework
        (scikit-learn, PyTorch, TensorFlow/Keras, XGBoost, LightGBM,
        CatBoost, Transformers, JAX) — deliberately excluding bare
        numpy/pandas usage as too weak a signal. For ML-containing repos,
        checks for a real "ML Versioning" signal (Washizaki's cataloged
        good pattern) — DVC config, MLflow/model-registry usage, or a
        versioned artifact filename (`*_v<N>.<ext>`) — and flags a
        Maintainability/Modifiability Finding, citing the pattern by name
        and source, when none is found. 9 tests. This required extending
        `wsqfai/ingestion/repository.py`'s `FileRecord` to retain each
        classified file's text content (previously discarded right after
        line-counting) — a real, deliberate scope change to M1's
        ingestion layer, covered by 2 new tests there (34 → all still
        passing).
  - [ ] **M3b — Remaining catalogue patterns/anti-patterns.** Glue Code,
        Pipeline Jungles, Dead Experimental Codepaths, Test Infrastructure
        Independence, Wrap Black-box Packages into Common APIs, and the
        rest of the 12+13+8 catalogue. Each needs a detection heuristic
        honest enough not to be mostly false positives from a static,
        no-execution read of source — that's real design work per
        pattern, not a batch of regexes to add in one sitting.
  - [ ] **M3c — ISO/IEC 25059 AI-specific characteristics themselves**
        (Functional Adaptability, User Controllability, Transparency,
        Intervenability, Societal/Ethical Risk Mitigation from
        `quality_model.py`) — these need signals beyond static structure
        (e.g. whether a model-serving endpoint exposes an explanation/
        override mechanism), which is further scoping work, not yet
        started.
- **M4 — Security, proven not asserted.** Reintroduce
      `engine-archive/kagutsuchi`'s sandbox + attack-hypothesis + verify
      pipeline, re-platformed onto the new Finding/Evidence model, findings
      framed via the AI Security Continuum's dimensions. Split for the same
      reason M2/M3 were:
  - [x] **M4a — Static hypothesis generation.** `wsqfai/security/ast_scan.py`
        re-platforms `engine-archive/kagutsuchi/system/analysis/ast_scan.py`'s
        AST-based sensitive-operation scanner (shell exec, subprocess,
        deserialization, SQL/Django/YAML/SSTI injection heuristics, all
        gated by a taint-propagation check so a dangerous call built from
        only hardcoded arguments isn't flagged) onto wsqfai's domain model
        — detection logic carried over near-verbatim since it was already
        proven against real code, only its *output* changes. Every hit
        becomes an `Observation`, deliberately NOT a `Finding`: a static
        AST match is evidence of a pattern, not proof of a vulnerability,
        and minting a Finding from it would violate this project's own
        "proven, not asserted" discipline (ARCHITECTURE.md's #1 security
        design decision). `wsqfai/security/scanner.py` runs it across a
        whole `RepositorySnapshot`. 25 tests (22 detector-level, 3
        repository-level), ported from the archive's own
        `tests/system/test_ast_scan.py` test-by-test. `LearnedSignature`/
        `extra_signatures` and `scan_diff`/diff-scoped scanning were left
        out of this port deliberately — they depended on a review/approval
        workflow and a CI diff view that haven't been re-platformed yet.
  - [ ] **M4b — Sandbox verification.** Reintroduce
        `engine-archive/kagutsuchi/system/sandbox` (Docker/subprocess
        isolation) and `verification/` (attack-hypothesis generation,
        execution, before/after evidence, verdicts) to actually attempt
        exploiting an M4a Observation and only then mint a `Finding` -
        the step that makes a Security Finding mean something more than
        "an AST pattern matched somewhere".
  - [ ] **M4c — AI Security Continuum framing.** Reframe M4a/M4b findings
        via Washizaki & Yoshioka's multi-dimensional continuum (CAIN 2024)
        instead of flat severity tags.
- [ ] **M5 — Evidence & benchmark engine.** WSQF/WSQB-style benchmarking:
      build a small reference corpus of scanned repositories and report a
      repo's measurements *relative to that corpus*, not as a lonely
      number.
- [ ] **M6 — Dashboard, report, CI/PR integration.** A real frontend
      (reusing KAGUTSUCHI's auth/i18n infrastructure from the archive where
      it fits), a generated report, and a CI-gate mode.

## Immediately next

An end-to-end entry point that actually runs M1+M2a+M2b+M3a+M4a against a
real repository and produces one combined report - `wsqfai/report.py` and
a CLI - so the project is demonstrable as a working tool, not just a set
of passing test suites. Everything built so far has been proven correct in
isolation; nothing yet proves the pieces compose. After that: M4b (sandbox
verification, the highest-value remaining milestone since it's the step
that makes Security findings mean "proven exploitable", not just "pattern
matched") and M2b/M3b's remaining slices.
