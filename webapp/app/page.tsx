import {
  AccentChip,
  CornerBrackets,
  Crosshair,
  DotGrid,
  Glitch,
  Grain,
  HazardStripe,
  IndexLabel,
  LineField,
  ReadoutCluster,
  RedactedLine,
  Scanlines,
  TickRuler,
  Vignette,
} from "@/components/ornament";

// WORKING DESIGN-LANGUAGE TEST, v3 -- v2 read as clean editorial/agency
// (warm beige panel, soft icy-pale section, undamaged type) instead of
// the futuristic/dystopian register actually asked for. Rebuilt around:
// a mostly-void palette (light surfaces are the rare exception, not a
// third of the page), RGB-split "corrupted signal" type, scanlines +
// vignette, hazard-tape amber reserved for danger, and a redacted-
// document motif -- concrete dystopian/surveillance signals the first
// two passes had none of.
export default function HomePage() {
  return (
    <main className="relative">
      <Grain />
      <Scanlines />
      <Vignette />

      {/* ============ BAND 1: dark industrial steel, dense HUD annotation ============ */}
      <section className="on-warm relative overflow-hidden">
        <LineField tone="light" variant="b" className="pointer-events-none absolute inset-0 h-full w-full opacity-30" />
        <div className="relative mx-auto max-w-6xl px-6 py-8 sm:px-8 sm:py-10">
          <div className="flex flex-wrap items-center justify-between gap-y-3">
            <div className="flex items-center gap-3">
              <Crosshair />
              <span className="font-mono-tech text-xs whitespace-nowrap">KAGUTSUCHI</span>
            </div>
            <TickRuler ticks={10} labelLeft="LV7" labelRight="D1" className="hidden w-72 opacity-60 sm:flex" />
          </div>

          <div className="mt-14 flex flex-wrap items-start justify-between gap-10 sm:mt-24">
            <div className="max-w-2xl">
              <div className="mb-3 flex items-center gap-3">
                <IndexLabel className="opacity-60">001.04 — SYSTEM</IndexLabel>
                <DotGrid />
              </div>
              <h1 className="font-display text-4xl leading-[0.95] font-bold tracking-tight uppercase sm:text-6xl md:text-7xl">
                <Glitch>Trust nothing.</Glitch>
                <br />
                Verify everything.
              </h1>
              <p className="font-mono-tech mt-6 max-w-sm text-[11px] leading-relaxed opacity-60">
                every finding is attacked for real, in an isolated sandbox — before it is ever called a vulnerability.
              </p>

              <div className="mt-6 flex items-center gap-3 opacity-50">
                <RedactedLine widths={[60, 30, 44, 18, 52]} />
              </div>
            </div>

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
          </div>

          <div className="mt-16 flex flex-wrap items-center gap-x-8 gap-y-4 sm:mt-20">
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
        </div>
      </section>

      {/* ============ BAND 2: the one pale register -- a classified evidence panel, not a bright hero ============ */}
      <section className="on-ice relative overflow-hidden">
        <div aria-hidden="true" className="absolute inset-x-0 top-0 h-56 overflow-hidden sm:h-64">
          {[
            { top: "10%", op: 0.5, h: 2 },
            { top: "38%", op: 0.95, h: 4 },
            { top: "39%", op: 0.28, h: 26 },
            { top: "68%", op: 0.35, h: 1.5 },
          ].map((b, i) => (
            <div
              key={i}
              className="absolute bg-[var(--deep-950)]"
              style={{ top: b.top, left: "-10%", width: "160%", height: b.h, opacity: b.op, transform: "rotate(-13deg)" }}
            />
          ))}
        </div>

        <div className="relative mx-auto max-w-6xl px-6 py-20 sm:px-8 sm:py-28">
          <div className="flex items-start justify-between">
            <IndexLabel className="opacity-70">002 — EVIDENCE FILE</IndexLabel>
            <div className="text-right">
              <div className="font-display text-2xl leading-none font-bold tracking-tight uppercase">Substance</div>
              <div className="font-mono-tech mt-2 text-[10px] opacity-60">04 / VERIFIED</div>
            </div>
          </div>

          <div className="mt-28 grid grid-cols-1 gap-10 sm:mt-36 sm:grid-cols-3 sm:gap-6">
            {[
              ["01", "Detect", "AST + AI scan surface real candidates, nothing trusted yet."],
              ["02", "Attack", "A live exploit runs in an isolated, network-disabled sandbox."],
              ["03", "Verify", "The proposed fix is attacked again, with the identical payload."],
            ].map(([n, title, body]) => (
              <div key={n} className="border-t pt-4" style={{ borderColor: "var(--line-on-light-strong)" }}>
                <div className="font-mono-tech text-[10px] opacity-50">{n}</div>
                <div className="font-display mt-1 text-lg font-bold tracking-tight uppercase">{title}</div>
                <p className="mt-2 max-w-[22ch] text-[13px] leading-relaxed opacity-70">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ BAND 3: deep void, glowing line-field, closing directive ============ */}
      <section className="on-deep relative min-h-[640px] overflow-hidden">
        <LineField tone="light" className="pointer-events-none absolute inset-0 h-full w-full opacity-90" />
        <div className="relative mx-auto flex min-h-[640px] max-w-6xl flex-col justify-between px-6 py-16 sm:px-8 sm:py-20">
          <div className="flex items-start justify-between">
            <IndexLabel>003 — VERDICT</IndexLabel>
            <span className="font-mono-tech text-[10px] opacity-50">Δ7</span>
          </div>

          <div className="max-w-xl">
            <p className="font-display text-2xl leading-[1.2] font-bold tracking-tight uppercase sm:text-4xl">
              <Glitch>An exploit proven</Glitch> is worth more than a warning believed.
            </p>
            <div className="mt-10">
              <CornerBrackets className="inline-block px-6 py-3">
                <span className="font-mono-tech text-xs whitespace-nowrap uppercase">Run a scan →</span>
              </CornerBrackets>
            </div>
          </div>

          <div className="font-mono-tech flex justify-between text-[10px] opacity-50">
            <span>F2</span>
            <span>KAGUTSUCHI © LV.MAX</span>
          </div>
        </div>
      </section>
    </main>
  );
}
