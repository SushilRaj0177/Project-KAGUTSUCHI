import {
  AccentChip,
  CornerBrackets,
  Crosshair,
  Cursor,
  DotGrid,
  Glitch,
  Grain,
  HazardStripe,
  IndexLabel,
  LineField,
  LiveCounter,
  Parallax,
  ReadoutCluster,
  RedactedLine,
  Scanlines,
  ScrollReveal,
  Sweep,
  TickRuler,
  Vignette,
} from "@/components/ornament";

// WORKING DESIGN-LANGUAGE TEST, v5 -- v4 fixed the static/boxed
// "document" problem structurally (one canvas, oversized type, torn
// fragments) but was still only ambient motion (a looping glitch, a
// looping sweep) playing out identically regardless of what the visitor
// did. "Super dynamic" means the page has to actually RESPOND:
//  - ScrollReveal: every major block assembles into place as it enters
//    the viewport, instead of the whole page sitting fully rendered and
//    inert at first paint.
//  - Parallax: the background line-field and the HUD readout cluster
//    drift at different rates as the mouse moves (and the line-field
//    also drifts with scroll) -- depth that responds to the visitor,
//    not just a fixed picture behind the text.
//  - hud-button hover/focus state on every CTA (see CornerBrackets.tsx
//    + globals.css): the brackets extend and brighten on interaction
//    instead of sitting inert until clicked.
//  - LiveCounter: a readout that visibly ticks upward on an interval --
//    a concrete "this is live" signal beyond ambient background loops.
export default function HomePage() {
  return (
    <main className="on-deep relative min-h-screen overflow-x-clip">
      <Cursor />
      <Grain />
      <Scanlines />
      <Vignette />
      <Parallax depth={22} scrollSpeed={0.08} className="pointer-events-none fixed inset-0 h-full w-full">
        <LineField tone="light" variant="a" className="h-full w-full opacity-80" />
      </Parallax>

      {/* ============ Continuous hero canvas ============ */}
      <div className="relative mx-auto max-w-[1600px] px-6 pt-8 sm:px-10">
        <div className="flex flex-wrap items-center justify-between gap-y-3">
          <div className="flex items-center gap-3">
            <Crosshair />
            <span className="font-mono-tech text-xs whitespace-nowrap">KAGUTSUCHI</span>
          </div>
          <div className="hidden items-center gap-4 sm:flex">
            <TickRuler ticks={10} labelLeft="LV7" labelRight="D1" className="w-56 opacity-60" />
            <span className="font-mono-tech text-[10px] whitespace-nowrap opacity-50">
              SCANS RUN: <LiveCounter from={41862} />
            </span>
          </div>
        </div>

        <section className="relative flex min-h-[86vh] flex-col justify-center py-16 sm:py-24">
          <Sweep className="left-0 w-full sm:left-1/4 sm:w-3/4" />

          <div
            className="font-mono-tech pointer-events-none absolute top-1/2 left-2 hidden -translate-y-1/2 -rotate-90 text-[10px] tracking-[0.3em] whitespace-nowrap opacity-40 sm:block"
            aria-hidden="true"
          >
            KAGUTSUCHI // VERIFICATION SUBSTRATE // 001
          </div>

          <div className="mb-4 flex items-center gap-3">
            <IndexLabel className="opacity-60">001.04 — SYSTEM</IndexLabel>
            <DotGrid />
          </div>

          <h1 className="font-display leading-[0.86] font-bold tracking-tighter uppercase" style={{ fontSize: "clamp(3.2rem, 11vw, 11rem)" }}>
            <Glitch>Trust nothing.</Glitch>
            <br />
            <span className="opacity-90">Verify everything.</span>
          </h1>

          <div className="mt-8 flex flex-wrap items-end justify-between gap-8">
            <ScrollReveal className="max-w-sm">
              <p className="font-mono-tech text-[11px] leading-relaxed opacity-60">
                every finding is attacked for real, in an isolated sandbox — before it is ever called a vulnerability.
              </p>
              <RedactedLine widths={[60, 30, 44, 18, 52]} className="mt-5 opacity-40" />
            </ScrollReveal>

            <Parallax depth={-10}>
              <ReadoutCluster
                index="P0 / SCAN"
                bars={[
                  { tone: "paper", width: 72 },
                  { tone: "magenta", width: 44 },
                  { tone: "blue", width: 58 },
                  { tone: "cyan", width: 30 },
                ]}
                className="opacity-90"
              />
            </Parallax>
          </div>

          <div className="mt-14 flex flex-wrap items-center gap-x-8 gap-y-4">
            <CornerBrackets className="px-6 py-3">
              <span className="font-mono-tech text-xs whitespace-nowrap uppercase">Run a scan →</span>
            </CornerBrackets>
            <div className="flex items-center gap-2">
              <AccentChip tone="lime" />
              <span className="font-mono-tech text-[10px] whitespace-nowrap uppercase opacity-60">verified fixed</span>
            </div>
            <div className="flex items-center gap-2">
              <HazardStripe className="h-2.5 w-6" />
              <span className="font-mono-tech text-[10px] whitespace-nowrap uppercase opacity-60">high severity</span>
            </div>
          </div>
        </section>

        {/* ============ Evidence fragment -- rotated, torn-edge insert, not a slide ============ */}
        <section className="relative py-16 sm:py-24">
          <ScrollReveal>
            <div
              className="on-ice relative mx-auto max-w-3xl -rotate-1 px-8 py-10 shadow-[0_30px_80px_rgba(0,0,0,0.6)] sm:px-14 sm:py-14"
              style={{ clipPath: "polygon(0 0, 97% 0, 100% 6%, 100% 100%, 3% 100%, 0 94%)" }}
            >
              <div className="flex items-start justify-between">
                <IndexLabel className="opacity-70">002 — EVIDENCE FILE</IndexLabel>
                <div className="text-right">
                  <div className="font-display text-xl leading-none font-bold tracking-tight uppercase">Substance</div>
                  <div className="font-mono-tech mt-2 text-[10px] opacity-60">04 / VERIFIED</div>
                </div>
              </div>

              <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-3">
                {[
                  ["01", "Detect", "AST + AI scan surface real candidates, nothing trusted yet."],
                  ["02", "Attack", "A live exploit runs in an isolated, network-disabled sandbox."],
                  ["03", "Verify", "The proposed fix is attacked again, with the identical payload."],
                ].map(([n, title, body], i) => (
                  <ScrollReveal key={n} delayMs={i * 120}>
                    <div className="font-mono-tech text-[10px] opacity-50">{n}</div>
                    <div className="font-display mt-1 text-base font-bold tracking-tight uppercase">{title}</div>
                    <p className="mt-2 text-[13px] leading-relaxed opacity-70">{body}</p>
                  </ScrollReveal>
                ))}
              </div>
            </div>
          </ScrollReveal>
          {/* torn fragment sitting just outside the panel, reinforcing "pinned insert" rather than "card" */}
          <div className="font-mono-tech absolute top-2 left-4 -rotate-3 text-[9px] tracking-widest opacity-30 sm:top-6 sm:left-12">
            EXHIBIT C3.1 — DO NOT DUPLICATE
          </div>
        </section>

        {/* ============ Closing directive -- still the same canvas, no border between sections ============ */}
        <section className="relative flex min-h-[70vh] flex-col justify-between py-16 sm:py-20">
          <div className="flex items-start justify-between">
            <IndexLabel>003 — VERDICT</IndexLabel>
            <span className="font-mono-tech text-[10px] opacity-50">Δ7</span>
          </div>

          <ScrollReveal className="max-w-3xl">
            <p
              className="font-display font-bold tracking-tight uppercase"
              style={{ fontSize: "clamp(1.6rem, 4.4vw, 3.4rem)", lineHeight: 1.15 }}
            >
              <Glitch>An exploit proven</Glitch> is worth more than a warning believed.
            </p>
            <div className="mt-10">
              <CornerBrackets className="inline-block px-6 py-3">
                <span className="font-mono-tech text-xs whitespace-nowrap uppercase">Run a scan →</span>
              </CornerBrackets>
            </div>
          </ScrollReveal>

          <div className="font-mono-tech flex justify-between text-[10px] opacity-50">
            <span>F2</span>
            <span>KAGUTSUCHI © LV.MAX</span>
          </div>
        </section>
      </div>
    </main>
  );
}
