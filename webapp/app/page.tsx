import Link from "next/link";
import CopyCommand from "./CopyCommand";
import Header from "./Header";
import Reveal from "./components/Reveal";
import WordReveal from "./components/WordReveal";
import Spotlight from "./components/Spotlight";
import { HoverRow, HoverStat } from "./components/Hoverable";

export default function Home() {
  return (
    <>
      <Header />

      <section className="hero">
        <Spotlight />
        <div className="wrap">
          <Reveal from="none">
            <span className="eyebrow">Evidence-based dependability auditing</span>
          </Reveal>
          <h1>
            <WordReveal text="Every finding cites a file, a line, and a standard." />
            <br />
            <WordReveal text="Not an LLM's opinion of your code." delay={0.35} className="hero-emphasis" />
          </h1>
          <Reveal delay={0.15}>
            <p className="lede">
              WSQF-AI extends Prof. Hironori Washizaki&apos;s Waseda Software Quality Framework (WSQF/WSQB) to AI-era
              repositories — measuring real ISO/IEC 25010/25059 characteristics against your source, instead of asking
              a model to guess a score.
            </p>
          </Reveal>
          <Reveal delay={0.25}>
            <CopyCommand command={"pip install -e .\nwsqfai https://github.com/pallets/flask"} />
          </Reveal>
          <Reveal delay={0.35}>
            <div className="badges">
              {[
                <>
                  <b>208</b> tests passing
                </>,
                <>
                  ISO/IEC <b>25010</b> · <b>25059</b>
                </>,
                "8 milestone slices shipped",
                "sandbox-verified security findings",
              ].map((content, i) => (
                <HoverStat key={i} tag="span" className="badge">
                  {content}
                </HoverStat>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <section id="research-teaser">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">Standards-based, not vibes-based</span>
          </Reveal>
          <h2>
            <WordReveal text="Every check maps to a cited standard or paper" />
          </h2>
          <Reveal delay={0.1}>
            <p className="lede">
              ISO/IEC 25010 and 25059 define what gets measured; WSQF/WSQB defines how it&apos;s benchmarked. Each
              design decision has a specific source, not a vague appeal to authority.
            </p>
            <p className="lede" style={{ marginTop: 14 }}>
              <Link href="/research" className="inline-link">
                See the sources <span className="arrow">→</span>
              </Link>
            </p>
          </Reveal>
        </div>
      </section>

      <section id="demo">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">A real run, not a mockup</span>
          </Reveal>
          <h2>
            <WordReveal text="Auditing pallets/flask" />
          </h2>
          <Reveal delay={0.1}>
            <p className="lede">
              Output from an actual <code className="loc">wsqfai https://github.com/pallets/flask</code> run against
              Flask&apos;s real source.
            </p>
          </Reveal>

          <div className="stats">
            {[
              { n: "236", l: "files scanned" },
              { n: "19,188", l: "lines" },
              { n: "13", l: "findings" },
              { n: "1", l: "fix proposed" },
            ].map((stat, i) => (
              <Reveal key={stat.l} delay={i * 0.06} from="up">
                <HoverStat tag="div" className="stat">
                  <span className="n">{stat.n}</span>
                  <span className="l">{stat.l}</span>
                </HoverStat>
              </Reveal>
            ))}
          </div>

          <Reveal delay={0.1}>
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
                  <HoverRow>
                    <td>
                      <span className="sev high">high</span>
                    </td>
                    <td>reliability / fault_tolerance</td>
                    <td>Bare &apos;except:&apos; clause</td>
                    <td>
                      <code className="loc">src/flask/app.py</code>
                    </td>
                  </HoverRow>
                  <HoverRow>
                    <td>
                      <span className="sev medium">medium</span>
                    </td>
                    <td>maintainability / modularity</td>
                    <td>Large file reduces modularity</td>
                    <td>
                      <code className="loc">src/flask/cli.py</code>
                    </td>
                  </HoverRow>
                  <HoverRow>
                    <td>
                      <span className="sev medium">medium</span>
                    </td>
                    <td>reliability / fault_tolerance</td>
                    <td>Swallowed exception</td>
                    <td>
                      <code className="loc">src/flask/config.py</code>
                    </td>
                  </HoverRow>
                  <HoverRow>
                    <td>
                      <span className="sev medium">medium</span>
                    </td>
                    <td>portability / installability</td>
                    <td>Unpinned dependencies</td>
                    <td>
                      <code className="loc">examples/tutorial/pyproject.toml</code>
                    </td>
                  </HoverRow>
                </tbody>
              </table>
            </div>
          </Reveal>

          <Reveal delay={0.15}>
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
                  <HoverRow>
                    <td>
                      <code className="loc">src/flask/app.py</code>
                    </td>
                    <td>
                      Narrowed bare &apos;except:&apos; to &apos;except Exception:&apos; so
                      SystemExit/KeyboardInterrupt/GeneratorExit propagate normally.
                    </td>
                  </HoverRow>
                </tbody>
              </table>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <p className="lede" style={{ marginTop: 36 }}>
              Flask&apos;s <code className="loc">exec()</code> hypothesis stays unverified, honestly — sandbox
              verification only covers one mechanically reconstructible shape so far (a direct single-parameter
              shell-exec call). Point it at code that <em>is</em> that shape, and the sandbox actually proves the
              exploit instead of trusting the pattern:
            </p>
          </Reveal>

          <Reveal delay={0.1}>
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
                  <HoverRow className="row-critical">
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
                  </HoverRow>
                </tbody>
              </table>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="lede" style={{ fontSize: "0.85rem" }}>
              The exact same static pattern in a function that validates its input first is correctly cleared instead
              — verification runs the real code, it doesn&apos;t trust the match.
            </p>
          </Reveal>
        </div>
      </section>

      <section id="pipeline">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">How it&apos;s built</span>
          </Reveal>
          <h2>
            <WordReveal text="Pipeline & honest status" />
          </h2>
          <Reveal delay={0.1}>
            <p className="lede">
              A milestone is only marked done once it&apos;s real, tested code — never because a plan for it exists.
            </p>
          </Reveal>
          <div className="pipeline">
            {[
              {
                m: "M1",
                name: "Ingestion & canonical model",
                small: "Finding / Evidence / Observation, ISO/IEC 25000-2 vocabulary",
                pill: "done",
                label: "Done",
              },
              {
                m: "M2",
                name: "SQuaRE quality measurement",
                small: "Maintainability + Reliability + Portability real; two characteristics remain",
                pill: "partial",
                label: "Partial",
              },
              {
                m: "M3",
                name: "AI/ML quality extension",
                small: "ML-repository detection + ML Versioning check; catalogue patterns remain",
                pill: "partial",
                label: "Partial",
              },
              {
                m: "M4",
                name: "Security, proven not asserted",
                small: "AST hypothesis generation + real sandbox verification (one shape so far, kernel-confined)",
                pill: "partial",
                label: "Partial",
              },
              {
                m: "M5",
                name: "Evidence & benchmark engine",
                small: "Corpus-comparison methodology real; a curated reference corpus remains",
                pill: "partial",
                label: "Partial",
              },
              {
                m: "M7",
                name: "Remediation & real backend",
                small: "Real auto-fix diffs, a FastAPI service, GitHub PR delivery — this page is next",
                pill: "partial",
                label: "Partial",
              },
            ].map((stage, i) => (
              <Reveal key={stage.m} delay={i * 0.05} from="left">
                <HoverRow tag="div" className="stage">
                  <span className="m">{stage.m}</span>
                  <span className="name">
                    {stage.name}
                    <small>{stage.small}</small>
                  </span>
                  <span className={`pill ${stage.pill}`}>{stage.label}</span>
                </HoverRow>
              </Reveal>
            ))}
          </div>
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
