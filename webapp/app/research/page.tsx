import type { Metadata } from "next";
import Header from "../Header";

export const metadata: Metadata = {
  title: "WSQF-AI — Research grounding",
  description:
    "Every design decision in WSQF-AI traces to a specific, citable piece of Prof. Hironori Washizaki's published work or standards involvement.",
};

export default function Research() {
  return (
    <>
      <Header />

      <section className="hero">
        <div className="wrap">
          <span className="eyebrow">Research grounding</span>
          <h1>Who this is grounded in, and why it matters</h1>
          <p className="lede">
            Every major design decision in WSQF-AI traces to a specific, citable piece of Prof. Hironori
            Washizaki&apos;s published work or standards involvement — not a generic &quot;AI code auditor&quot;
            concept with his name attached afterward. This page is that trace, kept explicit and falsifiable: if a
            design choice below can&apos;t be pointed at a real citation, it doesn&apos;t belong here.
          </p>
        </div>
      </section>

      <section id="bio">
        <div className="wrap">
          <span className="eyebrow">Prof. Hironori Washizaki</span>
          <h2>Waseda University · Visiting Professor, National Institute of Informatics</h2>
          <p className="lede">As of 2024–2025:</p>
          <div className="cards">
            <div className="card">
              <h3>Editor, SWEBOK Guide v4.0</h3>
              <p>
                The field&apos;s canonical Software Engineering Body of Knowledge. v4.0 added three knowledge areas
                under his editorship: Software Architecture, Software Security, and Software Engineering
                Operations, alongside the long-standing Software Quality and Software Testing KAs.
              </p>
              <span className="src">IEEE Computer Society, Oct 2024</span>
            </div>
            <div className="card">
              <h3>Convener, ISO/IEC JTC1 SC7/WG20</h3>
              <p>
                Standardizing bodies of knowledge and professional certification — the ISO/IEC 24773 series.
              </p>
              <span className="src">Since 2015</span>
            </div>
            <div className="card">
              <h3>Creator, WSQF/WSQB</h3>
              <p>
                Waseda Software Quality Framework/Benchmark — a SQuaRE-based framework that doesn&apos;t score
                software abstractly, it measures real products against the standard&apos;s characteristics and
                benchmarks them.
              </p>
              <span className="src">ICSE 2019 · 21 commercial products</span>
            </div>
            <div className="card">
              <h3>ML design-pattern research</h3>
              <p>
                Lead author on a sustained line of machine-learning design-pattern research: Machine Learning
                Architecture and Design Patterns (Computer, 2022); Studying Software Engineering Patterns for
                Designing Machine Learning Systems (arXiv:1910.04736); Pattern Application Support Framework in
                Machine Learning Reliability Solution Patterns (PLoP 2024).
              </p>
              <span className="src">Computer 2022 · arXiv:1910.04736 · PLoP 2024</span>
            </div>
            <div className="card">
              <h3>AI Security Continuum</h3>
              <p>
                Co-author, with Nobukazu Yoshioka, of a multi-dimensional model spanning the AI computing-environment
                continuum, technical-activity continuum, architecture-layer continuum, AI automation level, and AI
                security measure level.
              </p>
              <span className="src">CAIN 2024</span>
            </div>
            <div className="card">
              <h3>Reliable Software Engineering Lab</h3>
              <p>
                Principal Investigator (Washizaki &amp; Ubayashi Lab), whose stated three-pillar mission is (1)
                AI/data-driven development efficiency, (2) quality assurance of software systems using AI as the
                evaluation platform, (3) talent — with QA explicitly the pillar linking the other two.
              </p>
              <span className="src">Waseda University</span>
            </div>
          </div>
          <p className="lede" style={{ fontSize: "0.85rem", marginTop: 20 }}>
            Also: editorial-board history on Japan&apos;s SQuBOK (Software Quality Body of Knowledge); connected to
            Japan&apos;s QA4AI Consortium and AIST&apos;s Machine Learning Quality Management Guideline (AIQM).
            Sources: his lab site (washi.cs.waseda.ac.jp), Waseda&apos;s Vision150 feature on his AI-reliability
            framework work, the WSQF/WSQB project page, the SWEBOK v4.0 release announcement, the CAIN 2024 AI
            Security Continuum paper, his ML design-patterns papers, and AIST/QA4AI&apos;s published guidelines.
          </p>
        </div>
      </section>

      <section id="trace">
        <div className="wrap">
          <span className="eyebrow">Design-decision trace</span>
          <h2>Every choice, traced to a citation</h2>
          <div className="trace">
            <div className="row">
              <span className="decision">
                Quality is <em>measured</em> against a standard&apos;s real characteristics, never an invented 0–100
                score
              </span>
              <span className="source">WSQF/WSQB&apos;s entire methodology (ICSE 2019)</span>
            </div>
            <div className="row">
              <span className="decision">
                A dedicated AI/ML quality dimension (not bolted onto generic code quality)
              </span>
              <span className="source">ISO/IEC 25059 (SQuaRE&apos;s AI extension)</span>
            </div>
            <div className="row">
              <span className="decision">A design-pattern recognition engine for ML code</span>
              <span className="source">
                Washizaki&apos;s own ML design-pattern research (Computer 2022; PLoP 2024) — his most distinctive,
                ownable contribution
              </span>
            </div>
            <div className="row">
              <span className="decision">
                Security findings must be <em>proven</em> (exploited in a real sandbox), never asserted from a
                static match
              </span>
              <span className="source">
                Reused directly from Project KAGUTSUCHI&apos;s engine — independently arrived at, but consonant with
                the evidence-based rigor WSQF/WSQB itself demands
              </span>
            </div>
            <div className="row">
              <span className="decision">
                Security findings will be framed via a multi-dimensional continuum, not flat OWASP-style tags
                (planned, M4c)
              </span>
              <span className="source">AI Security Continuum (Washizaki &amp; Yoshioka, CAIN 2024)</span>
            </div>
            <div className="row">
              <span className="decision">Findings organized by SWEBOK knowledge area</span>
              <span className="source">SWEBOK Guide v4.0, personally edited by Washizaki (2024)</span>
            </div>
            <div className="row">
              <span className="decision">
                Evidence has explicit provenance (repo → file → line → analyzer → rule → observation), never a flat
                &quot;AI said so&quot;
              </span>
              <span className="source">SQuaRE&apos;s own vocabulary discipline (ISO/IEC 25000-2)</span>
            </div>
            <div className="row">
              <span className="decision">A benchmark corpus, not just a single-repo report</span>
              <span className="source">WSQF/WSQB&apos;s 21-product comparative benchmark study</span>
            </div>
          </div>
        </div>
      </section>

      <section id="pipeline-diagram">
        <div className="wrap">
          <span className="eyebrow">The pipeline (target state)</span>
          <h2>How the standards map onto the build</h2>
          <pre
            style={{
              background: "var(--mono-bg)",
              border: "1px solid var(--line)",
              borderRadius: 10,
              padding: "18px 20px",
              overflowX: "auto",
              fontFamily: "var(--font-mono), monospace",
              fontSize: "0.82rem",
              lineHeight: 1.7,
              marginTop: 24,
            }}
          >
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
        </div>
      </section>

      <section id="not">
        <div className="wrap">
          <span className="eyebrow">What this project is not</span>
          <p className="lede">
            Not &quot;paste a repo into an LLM and get a report.&quot; The AI layer (wherever it appears — pattern
            recognition assistance, finding explanation, hypothesis generation for the security layer) sits inside
            a pipeline whose ground truth comes from standards-grounded measurement and, for security claims,
            actual sandboxed proof — exactly the &quot;AI proposes, something deterministic and reviewed
            disposes&quot; principle Project KAGUTSUCHI was already built on, now extended to the full
            SQuaRE/SWEBOK-grounded scope described above.
          </p>
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
