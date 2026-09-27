import Link from "next/link";
import CopyCommand from "./CopyCommand";
import Header from "./Header";

export default function Home() {
  return (
    <>
      <Header />

      <section className="hero">
        <div className="wrap">
          <span className="eyebrow">Evidence-based dependability auditing</span>
          <h1>Every finding cites a file, a line, and a standard. Not an LLM&apos;s opinion of your code.</h1>
          <p className="lede">
            WSQF-AI extends Prof. Hironori Washizaki&apos;s Waseda Software Quality Framework (WSQF/WSQB) to AI-era
            repositories — measuring real ISO/IEC 25010/25059 characteristics against your source, instead of asking
            a model to guess a score.
          </p>
          <CopyCommand command={"pip install -e .\nwsqfai https://github.com/pallets/flask"} />
          <div className="badges">
            <span className="badge">
              <b>164</b> tests passing
            </span>
            <span className="badge">
              ISO/IEC <b>25010</b> · <b>25059</b>
            </span>
            <span className="badge">8 milestone slices shipped</span>
            <span className="badge">sandbox-verified security findings</span>
          </div>
        </div>
      </section>

      <section id="research-teaser">
        <div className="wrap">
          <span className="eyebrow">Grounded in real research</span>
          <h2>Not a generic auditor with a professor&apos;s name attached afterward</h2>
          <p className="lede">
            Every architectural decision in this project traces to a specific, citable piece of Prof. Hironori
            Washizaki&apos;s published work or standards role — WSQF/WSQB, SWEBOK v4.0, ISO/IEC 25059, ML design
            patterns, the AI Security Continuum.
          </p>
          <p className="lede" style={{ marginTop: 14 }}>
            <Link href="/research" style={{ color: "var(--accent)", fontWeight: 600 }}>
              Read the full research grounding →
            </Link>
          </p>
        </div>
      </section>

      <section id="demo">
        <div className="wrap">
          <span className="eyebrow">A real run, not a mockup</span>
          <h2>Auditing pallets/flask</h2>
          <p className="lede">
            Output from an actual <code className="loc">wsqfai https://github.com/pallets/flask</code> run against
            Flask&apos;s real source.
          </p>
          <div className="stats">
            <div className="stat">
              <span className="n">236</span>
              <span className="l">files scanned</span>
            </div>
            <div className="stat">
              <span className="n">19,188</span>
              <span className="l">lines</span>
            </div>
            <div className="stat">
              <span className="n">13</span>
              <span className="l">findings</span>
            </div>
            <div className="stat">
              <span className="n">1</span>
              <span className="l">fix proposed</span>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <caption>findings — sub-characteristic, title, location</caption>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Sub-characteristic</th>
                  <th>Finding</th>
                  <th>Location</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span className="sev high">high</span>
                  </td>
                  <td>reliability / fault_tolerance</td>
                  <td>Bare &apos;except:&apos; clause</td>
                  <td>
                    <code className="loc">src/flask/app.py</code>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span className="sev medium">medium</span>
                  </td>
                  <td>maintainability / modularity</td>
                  <td>Large file reduces modularity</td>
                  <td>
                    <code className="loc">src/flask/cli.py</code>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span className="sev medium">medium</span>
                  </td>
                  <td>reliability / fault_tolerance</td>
                  <td>Swallowed exception</td>
                  <td>
                    <code className="loc">src/flask/config.py</code>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span className="sev medium">medium</span>
                  </td>
                  <td>portability / installability</td>
                  <td>Unpinned dependencies</td>
                  <td>
                    <code className="loc">examples/tutorial/pyproject.toml</code>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="table-wrap">
            <table>
              <caption>a proposed fix — a real diff, generated from Flask&apos;s own file content</caption>
              <thead>
                <tr>
                  <th>File</th>
                  <th>Fix</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <code className="loc">src/flask/app.py</code>
                  </td>
                  <td>
                    Narrowed bare &apos;except:&apos; to &apos;except Exception:&apos; so SystemExit/KeyboardInterrupt/GeneratorExit
                    propagate normally.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="lede" style={{ marginTop: 36 }}>
            Flask&apos;s <code className="loc">exec()</code> hypothesis stays unverified, honestly — sandbox
            verification only covers one mechanically reconstructible shape so far (a direct single-parameter
            shell-exec call). Point it at code that <em>is</em> that shape, and the sandbox actually proves the
            exploit instead of trusting the pattern:
          </p>

          <div className="table-wrap">
            <table>
              <caption>a proven finding — the sandbox actually ran this function with an injection payload</caption>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Sub-characteristic</th>
                  <th>Finding</th>
                  <th>Location</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span className="sev critical">critical</span>
                  </td>
                  <td>security / integrity</td>
                  <td>
                    Proven command injection in <code className="loc">ping_host()</code>{" "}
                    <span className="verified">sandbox-confirmed</span>
                  </td>
                  <td>
                    <code className="loc">netdiag.py</code>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="lede" style={{ fontSize: "0.85rem" }}>
            The exact same static pattern in a function that validates its input first is correctly cleared instead
            — verification runs the real code, it doesn&apos;t trust the match.
          </p>
        </div>
      </section>

      <section id="pipeline">
        <div className="wrap">
          <span className="eyebrow">How it&apos;s built</span>
          <h2>Pipeline &amp; honest status</h2>
          <p className="lede">
            A milestone is only marked done once it&apos;s real, tested code — never because a plan for it exists.
          </p>
          <div className="pipeline">
            <div className="stage">
              <span className="m">M1</span>
              <span className="name">
                Ingestion &amp; canonical model
                <small>Finding / Evidence / Observation, ISO/IEC 25000-2 vocabulary</small>
              </span>
              <span className="pill done">Done</span>
            </div>
            <div className="stage">
              <span className="m">M2</span>
              <span className="name">
                SQuaRE quality measurement
                <small>Maintainability + Reliability + Portability real; two characteristics remain</small>
              </span>
              <span className="pill partial">Partial</span>
            </div>
            <div className="stage">
              <span className="m">M3</span>
              <span className="name">
                AI/ML quality extension
                <small>ML-repository detection + ML Versioning check; catalogue patterns remain</small>
              </span>
              <span className="pill partial">Partial</span>
            </div>
            <div className="stage">
              <span className="m">M4</span>
              <span className="name">
                Security, proven not asserted
                <small>AST hypothesis generation + real sandbox verification (one shape so far, kernel-confined)</small>
              </span>
              <span className="pill partial">Partial</span>
            </div>
            <div className="stage">
              <span className="m">M5</span>
              <span className="name">
                Evidence &amp; benchmark engine
                <small>Corpus-comparison methodology real; a curated reference corpus remains</small>
              </span>
              <span className="pill partial">Partial</span>
            </div>
            <div className="stage">
              <span className="m">M7</span>
              <span className="name">
                Remediation &amp; real backend
                <small>Real auto-fix diffs, a FastAPI service, GitHub PR delivery — this page is next</small>
              </span>
              <span className="pill partial">Partial</span>
            </div>
          </div>
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
