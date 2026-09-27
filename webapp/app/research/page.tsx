import type { Metadata } from "next";
import Header from "../Header";
import Reveal from "../components/Reveal";
import WordReveal from "../components/WordReveal";
import { HoverRow, HoverStat } from "../components/Hoverable";

export const metadata: Metadata = {
  title: "WSQF-AI — Research grounding",
  description:
    "Every design decision in WSQF-AI traces to a specific, citable piece of Prof. Hironori Washizaki's published work or standards involvement.",
};

const BIO_CARDS = [
  {
    title: "Editor, SWEBOK Guide v4.0",
    body: "The field's canonical Software Engineering Body of Knowledge. v4.0 added three knowledge areas under his editorship: Software Architecture, Software Security, and Software Engineering Operations, alongside the long-standing Software Quality and Software Testing KAs.",
    src: "IEEE Computer Society, Oct 2024",
  },
  {
    title: "Convener, ISO/IEC JTC1 SC7/WG20",
    body: "Standardizing bodies of knowledge and professional certification — the ISO/IEC 24773 series.",
    src: "Since 2015",
  },
  {
    title: "Creator, WSQF/WSQB",
    body: "Waseda Software Quality Framework/Benchmark — a SQuaRE-based framework that doesn't score software abstractly, it measures real products against the standard's characteristics and benchmarks them.",
    src: "ICSE 2019 · 21 commercial products",
  },
  {
    title: "ML design-pattern research",
    body: "Lead author on a sustained line of machine-learning design-pattern research: Machine Learning Architecture and Design Patterns (Computer, 2022); Studying Software Engineering Patterns for Designing Machine Learning Systems (arXiv:1910.04736); Pattern Application Support Framework in Machine Learning Reliability Solution Patterns (PLoP 2024).",
    src: "Computer 2022 · arXiv:1910.04736 · PLoP 2024",
  },
  {
    title: "AI Security Continuum",
    body: "Co-author, with Nobukazu Yoshioka, of a multi-dimensional model spanning the AI computing-environment continuum, technical-activity continuum, architecture-layer continuum, AI automation level, and AI security measure level.",
    src: "CAIN 2024",
  },
  {
    title: "Reliable Software Engineering Lab",
    body: "Principal Investigator (Washizaki & Ubayashi Lab), whose stated three-pillar mission is (1) AI/data-driven development efficiency, (2) quality assurance of software systems using AI as the evaluation platform, (3) talent — with QA explicitly the pillar linking the other two.",
    src: "Waseda University",
  },
];

const TRACE_ROWS = [
  {
    decision: "Quality is measured against a standard's real characteristics, never an invented 0–100 score",
    source: "WSQF/WSQB's entire methodology (ICSE 2019)",
  },
  {
    decision: "A dedicated AI/ML quality dimension (not bolted onto generic code quality)",
    source: "ISO/IEC 25059 (SQuaRE's AI extension)",
  },
  {
    decision: "A design-pattern recognition engine for ML code",
    source: "Washizaki's own ML design-pattern research (Computer 2022; PLoP 2024) — his most distinctive, ownable contribution",
  },
  {
    decision: "Security findings must be proven (exploited in a real sandbox), never asserted from a static match",
    source:
      "Reused directly from Project KAGUTSUCHI's engine — independently arrived at, but consonant with the evidence-based rigor WSQF/WSQB itself demands",
  },
  {
    decision: "Security findings will be framed via a multi-dimensional continuum, not flat OWASP-style tags (planned, M4c)",
    source: "AI Security Continuum (Washizaki & Yoshioka, CAIN 2024)",
  },
  {
    decision: "Findings organized by SWEBOK knowledge area",
    source: "SWEBOK Guide v4.0, personally edited by Washizaki (2024)",
  },
  {
    decision: "Evidence has explicit provenance (repo → file → line → analyzer → rule → observation), never a flat \"AI said so\"",
    source: "SQuaRE's own vocabulary discipline (ISO/IEC 25000-2)",
  },
  {
    decision: "A benchmark corpus, not just a single-repo report",
    source: "WSQF/WSQB's 21-product comparative benchmark study",
  },
];

export default function Research() {
  return (
    <>
      <Header />

      <section className="hero">
        <div className="wrap">
          <Reveal from="none">
            <span className="eyebrow">Research grounding</span>
          </Reveal>
          <h1>
            <WordReveal text="Who this is grounded in, and why it matters" />
          </h1>
          <Reveal delay={0.15}>
            <p className="lede">
              Every major design decision in WSQF-AI traces to a specific, citable piece of Prof. Hironori
              Washizaki&apos;s published work or standards involvement — not a generic &quot;AI code auditor&quot;
              concept with his name attached afterward. This page is that trace, kept explicit and falsifiable: if a
              design choice below can&apos;t be pointed at a real citation, it doesn&apos;t belong here.
            </p>
          </Reveal>
        </div>
      </section>

      <section id="bio">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">Prof. Hironori Washizaki</span>
          </Reveal>
          <h2>
            <WordReveal text="Waseda University · Visiting Professor, National Institute of Informatics" />
          </h2>
          <Reveal delay={0.1}>
            <p className="lede">As of 2024–2025:</p>
          </Reveal>
          <div className="cards">
            {BIO_CARDS.map((card, i) => (
              <Reveal key={card.title} delay={i * 0.07} from="up">
                <HoverStat tag="div" className="card">
                  <h3>{card.title}</h3>
                  <p>{card.body}</p>
                  <span className="src">{card.src}</span>
                </HoverStat>
              </Reveal>
            ))}
          </div>
          <Reveal delay={0.1}>
            <p className="lede" style={{ fontSize: "0.85rem", marginTop: 20 }}>
              Also: editorial-board history on Japan&apos;s SQuBOK (Software Quality Body of Knowledge); connected to
              Japan&apos;s QA4AI Consortium and AIST&apos;s Machine Learning Quality Management Guideline (AIQM).
              Sources: his lab site (washi.cs.waseda.ac.jp), Waseda&apos;s Vision150 feature on his AI-reliability
              framework work, the WSQF/WSQB project page, the SWEBOK v4.0 release announcement, the CAIN 2024 AI
              Security Continuum paper, his ML design-patterns papers, and AIST/QA4AI&apos;s published guidelines.
            </p>
          </Reveal>
        </div>
      </section>

      <section id="trace">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">Design-decision trace</span>
          </Reveal>
          <h2>
            <WordReveal text="Every choice, traced to a citation" />
          </h2>
          <div className="trace">
            {TRACE_ROWS.map((row, i) => (
              <Reveal key={row.decision} delay={i * 0.04} from="left">
                <HoverRow tag="div" className="row">
                  <span className="decision">{row.decision}</span>
                  <span className="source">{row.source}</span>
                </HoverRow>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="pipeline-diagram">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">The pipeline (target state)</span>
          </Reveal>
          <h2>
            <WordReveal text="How the standards map onto the build" />
          </h2>
          <Reveal delay={0.1}>
            <pre className="pipeline-pre">
{`Repository
    |
    v
Ingestion & canonical model        (M1 -- ISO/IEC 25000-2 vocabulary: Finding / Evidence / Observation)
    |
    v
SQuaRE quality measurement          (M2 -- Maintainability, Reliability, Portability, ...)
    |
    v
AI/ML quality extension             (M3 -- ISO/IEC 25059 characteristics + ML design-pattern engine)
    |
    v
Security, proven not asserted       (M4 -- Kagutsuchi's engine, re-platformed,
    |                                       real sandbox verification, one shape so far)
    v
Remediation                         (M7 -- real auto-fix diffs + GitHub PR delivery)
    |
    v
Evidence & benchmark engine         (M5 -- WSQF/WSQB-style corpus benchmarking)
    |
    v
Dashboard, report, CI/PR gate       (M6 / M7c -- this website)`}
            </pre>
          </Reveal>
        </div>
      </section>

      <section id="not">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">What this project is not</span>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="lede">
              Not &quot;paste a repo into an LLM and get a report.&quot; The AI layer (wherever it appears — pattern
              recognition assistance, finding explanation, hypothesis generation for the security layer) sits inside
              a pipeline whose ground truth comes from standards-grounded measurement and, for security claims,
              actual sandboxed proof — exactly the &quot;AI proposes, something deterministic and reviewed
              disposes&quot; principle Project KAGUTSUCHI was already built on, now extended to the full
              SQuaRE/SWEBOK-grounded scope described above.
            </p>
          </Reveal>
        </div>
      </section>

      <footer>
        <div className="wrap">
          <p>WSQF-AI — built as an extension of Waseda&apos;s Software Quality Framework methodology.</p>
          <p>
            <a href="https://github.com/SushilRaj0177/Project-KAGUTSUCHI">
              github.com/SushilRaj0177/Project-KAGUTSUCHI
            </a>
          </p>
        </div>
      </footer>
    </>
  );
}
