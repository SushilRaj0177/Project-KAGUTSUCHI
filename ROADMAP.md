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
  - [ ] **M2b — Remaining SQuaRE characteristics.** Reliability,
        Performance Efficiency, Compatibility, Usability, Portability.
        Most of these need actual file content (not just path/size/line
        metadata) or runtime signals `RepositorySnapshot` doesn't carry
        yet — scoping this honestly, rather than forcing a weak metric
        onto a characteristic that doesn't have one yet, is real M2b
        work, not something to guess at now.
- [ ] **M3 — AI/ML quality extension.** ISO/IEC 25059 characteristics for
      ML-containing repositories, plus the ML design-pattern
      detection/recommendation engine (Washizaki's Computer 2022 / PLoP
      2024 pattern catalog as the starting reference set).
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

M2b or M3. M2b (Reliability/Performance/Compatibility/Usability/
Portability) needs real file content to measure honestly, which means
extending ingestion to optionally retain source text for small repos
rather than discarding it after the clone — a real scoping decision, not
just more metric functions. M3 (AI/ML quality extension) can start
independently: ISO/IEC 25059 characteristics for ML-containing repos, plus
the ML design-pattern detection engine referencing Washizaki's own pattern
catalog (Computer 2022 / PLoP 2024) — arguably the single most
recruiter-legible, Washizaki-specific piece of this whole project, so it's
worth pulling forward rather than strictly waiting on M2b to fully close.
