import type { Metadata } from "next";
import Header from "../Header";
import Reveal from "../components/Reveal";
import WordReveal from "../components/WordReveal";
import { HoverRow, HoverStat } from "../components/Hoverable";

export const metadata: Metadata = {
  title: "WSQF-AI — Research grounding",
  description: "The standards and papers WSQF-AI's design decisions actually cite, with a source for each one.",
};

const SOURCE_CARDS = [
  {
    title: "WSQF/WSQB",
    body: "A SQuaRE-based framework (Washizaki et al., ICSE 2019) that measures real products against the standard's characteristics and benchmarks them against each other, instead of producing an abstract score. This is the methodology this project's measurement layer follows.",
    src: "ICSE 2019 · 21 commercial products",
  },
  {
    title: "SWEBOK Guide v4.0",
    body: "The field's Software Engineering Body of Knowledge. v4.0 added Software Architecture, Security, and Operations as knowledge areas. Findings here are organized along the same knowledge-area lines.",
    src: "IEEE Computer Society, Oct 2024",
  },
  {
    title: "ML design-pattern catalogue",
    body: "A multivocal literature review cataloguing 12 ML architecture patterns, 13 design patterns, and 8 anti-patterns (building on Sculley et al.'s \"Hidden Technical Debt in Machine Learning Systems\", NeurIPS 2015). Source for this project's ML-pattern detectors.",
    src: "IEEE Computer, Vol. 55 No. 3, 2022",
  },
  {
    title: "AI Security Continuum",
    body: "A multi-dimensional model (computing-environment, technical-activity, and architecture-layer continua, plus automation and security-measure levels) for framing AI security risk. Planned as the basis for M4c's severity framing — not yet implemented.",
    src: "CAIN 2024",
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
    source: "Washizaki et al.'s ML design-pattern catalogue (Computer 2022; PLoP 2024)",
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
    source: "SWEBOK Guide v4.0 (2024)",
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
            <WordReveal text="What this is built on, with a source for each claim" />
          </h1>
          <Reveal delay={0.15}>
            <p className="lede">
              WSQF-AI's measurement layer follows Prof. Hironori Washizaki&apos;s WSQF/WSQB methodology, and its
              design pulls from a handful of specific, citable papers and standards below — not a generic
              &quot;AI code auditor&quot; with a name attached for credibility. If a design choice on this page
              can&apos;t be pointed at a real citation, it doesn&apos;t belong here.
            </p>
          </Reveal>
        </div>
      </section>

      <section id="bio">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">Primary sources</span>
          </Reveal>
          <h2>
            <WordReveal text="The standards and papers this cites" />
          </h2>
          <div className="cards">
            {SOURCE_CARDS.map((card, i) => (
              <Reveal key={card.title} delay={i * 0.07} from="up">
                <HoverStat tag="div" className="card">
                  <h3>{card.title}</h3>
                  <p>{card.body}</p>
                  <span className="src">{card.src}</span>
                </HoverStat>
              </Reveal>
            ))}
          </div>
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
          <p>WSQF-AI — evidence-based dependability auditing, grounded in cited research.</p>
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
