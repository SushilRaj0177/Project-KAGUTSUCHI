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
    - [ ] Performance Efficiency, Compatibility, Usability, Portability —
          not started. Each needs its own honest scoping pass (most can't
          be measured from static source alone at all — e.g. Performance
          Efficiency really needs a profiling run, not a source read).
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
- [ ] **M4 — Security, proven not asserted.** Reintroduce
      `engine-archive/kagutsuchi`'s sandbox + attack-hypothesis + verify
      pipeline, re-platformed onto the new Finding/Evidence model, findings
      framed via the AI Security Continuum's dimensions.
- [ ] **M5 — Evidence & benchmark engine.** WSQF/WSQB-style benchmarking:
      build a small reference corpus of scanned repositories and report a
      repo's measurements *relative to that corpus*, not as a lonely
      number.
- [ ] **M6 — Dashboard, report, CI/PR integration.** A real frontend
      (reusing KAGUTSUCHI's auth/i18n infrastructure from the archive where
      it fits), a generated report, and a CI-gate mode.

## Immediately next

M4 (Security). M2/M3 both have further honest slices left (M2b's other
four characteristics, M3b's harder catalogue patterns), but each remaining
slice needs its own scoping pass rather than being more of the same
pattern — reasonable to pick up incrementally rather than all before
moving on. M4 is a good next milestone to open in parallel: reintroducing
`engine-archive/kagutsuchi`'s proven sandbox/attack-hypothesis/verify
pipeline onto the new Finding/Evidence model is large, well-understood
(it's *already built and tested*, just archived), and is the piece of this
project with the most existing working code behind it.
