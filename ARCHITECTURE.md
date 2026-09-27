# Architecture & research grounding

Every major design decision in WSQF-AI traces to a specific, citable piece
of Prof. Hironori Washizaki's published work or standards involvement —
not a generic "AI code auditor" concept with his name attached afterward.
This document is that trace, kept explicit and falsifiable: if a design
choice below can't be pointed at a real citation, it doesn't belong in this
file.

## Who this is grounded in, and why it matters

Prof. Hironori Washizaki (Waseda University; Visiting Professor, National
Institute of Informatics) is, as of 2024-2025:

- **Editor of the SWEBOK Guide v4.0** (IEEE Computer Society, Oct 2024) —
  the field's canonical Software Engineering Body of Knowledge. v4.0 added
  three knowledge areas under his editorship: **Software Architecture,
  Software Security, and Software Engineering Operations**, alongside the
  long-standing Software Quality and Software Testing KAs.
- **Convener, ISO/IEC JTC1 SC7/WG20** (since 2015) — standardizing bodies
  of knowledge and professional certification (the ISO/IEC 24773 series).
- Deeply involved in **ISO/IEC 25000 (SQuaRE)** and its AI extension
  **ISO/IEC 25059**, and creator of **WSQF/WSQB** (Waseda Software Quality
  Framework/Benchmark) — a SQuaRE-based framework that doesn't score
  software abstractly, it *measures* real products against the standard's
  characteristics and benchmarks them (ICSE 2019, 21 commercial products).
- Editorial-board history on Japan's **SQuBOK** (Software Quality Body of
  Knowledge).
- Lead author on a sustained line of **machine-learning design-pattern**
  research: *Machine Learning Architecture and Design Patterns* (Computer,
  2022), *Studying Software Engineering Patterns for Designing Machine
  Learning Systems* (arXiv:1910.04736), *Pattern Application Support
  Framework in Machine Learning Reliability Solution Patterns* (PLoP 2024).
- Co-author of the **AI Security Continuum** framework with Nobukazu
  Yoshioka (CAIN 2024) — a multi-dimensional model spanning the AI
  computing-environment continuum, technical-activity continuum,
  architecture-layer continuum, AI automation level, and AI security
  measure level.
- Connected to Japan's **QA4AI Consortium** and **AIST's Machine Learning
  Quality Management Guideline (AIQM)** — ML-specific QA guidance.
- Principal Investigator of the **Reliable Software Engineering** lab
  (Washizaki & Ubayashi Lab), whose stated three-pillar mission is (1)
  AI/data-driven development efficiency, (2) quality assurance of software
  systems *using AI as the evaluation platform*, (3) talent — with QA
  explicitly the pillar linking the other two.

Sources (fetched during this project's research phase): his lab site
(washi.cs.waseda.ac.jp), Waseda's Vision150 feature on his AI-reliability
framework work, the WSQF/WSQB project page, the SWEBOK v4.0 release
announcement, the CAIN 2024 AI Security Continuum paper, his ML
design-patterns papers, and AIST/QA4AI's published guidelines.

## Design-decision trace

| Design decision | Traces to |
|---|---|
| Quality is *measured* against a standard's real characteristics, never an invented 0-100 score | WSQF/WSQB's entire methodology (ICSE 2019) |
| A dedicated AI/ML quality dimension (not bolted onto generic code quality) | ISO/IEC 25059 (SQuaRE's AI extension) |
| A design-pattern recognition/recommendation engine for ML code | Washizaki's own ML design-pattern research (Computer 2022; PLoP 2024) — his most distinctive, ownable contribution |
| Security findings must be *proven* (exploited in a sandbox), never asserted from a static match | Reused directly from Project KAGUTSUCHI's engine — independently arrived at, but consonant with the evidence-based rigor WSQF/WSQB itself demands |
| Security findings are framed via a multi-dimensional continuum (environment / activity / architecture layer / automation level / measure level), not flat OWASP-style tags | AI Security Continuum (Washizaki & Yoshioka, CAIN 2024) |
| Findings are organized by SWEBOK knowledge area (Quality, Security, Architecture, Testing, Maintenance) | SWEBOK Guide v4.0, personally edited by Washizaki (2024) |
| Evidence has explicit provenance (repo → file → line → analyzer → rule → observation → AI interpretation), never a flat "AI said so" | SQuaRE's own vocabulary discipline (ISO/IEC 25000-2) applied to this project's Finding/Evidence model |
| A benchmark corpus, not just a single-repo report | WSQF/WSQB's 21-product comparative benchmark study |

## The pipeline (target state)

```
Repository
    |
    v
Ingestion & canonical model        (M1 -- ISO/IEC 25000-2 vocabulary: Finding / Evidence / Observation)
    |
    v
SQuaRE quality measurement          (M2 -- Maintainability, Reliability, Performance Efficiency, ...)
    |
    v
AI/ML quality extension             (M3 -- ISO/IEC 25059 characteristics + ML design-pattern engine)
    |
    v
Security, proven not asserted       (M4 -- Project KAGUTSUCHI's engine, reintroduced from engine-archive/,
    |                                       framed via the AI Security Continuum)
    v
Evidence & benchmark engine         (M5 -- WSQF/WSQB-style corpus benchmarking)
    |
    v
Dashboard, report, CI/PR gate       (M6)
```

## What this project is not

Not "paste a repo into an LLM and get a report." The AI layer (wherever it
appears — pattern recognition assistance, finding explanation, hypothesis
generation for the security layer) sits *inside* a pipeline whose ground
truth comes from standards-grounded measurement and, for security claims,
actual sandboxed proof — exactly the "AI proposes, something deterministic
and reviewed disposes" principle Project KAGUTSUCHI was already built on,
now extended to the full SQuaRE/SWEBOK-grounded scope described above.
