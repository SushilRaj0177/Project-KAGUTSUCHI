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
- [ ] **M1 — Foundation.** Repository ingestion (clone, walk, classify
      languages/files) + a canonical `Finding` / `Evidence` / `Observation`
      model using ISO/IEC 25000-2 (SQuaRE Vocabulary) terms, not ad hoc
      field names.
- [ ] **M2 — SQuaRE quality measurement.** Deterministic measurement of
      real SQuaRE product-quality characteristics (Maintainability,
      Reliability, Performance Efficiency, Compatibility, Usability,
      Portability) — each metric traceable to the specific SQuaRE
      sub-characteristic it measures.
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

M1: the ingestion pipeline and the canonical model. This is deliberately
unglamorous — the same reasoning that put KAGUTSUCHI's own Evidence Engine
(M5 in that project's numbering) before its AI/scoring/dashboard layers:
nothing downstream is trustworthy if the foundational model is sloppy.
