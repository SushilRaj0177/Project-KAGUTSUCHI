import { AccentBar, AccentChip, CornerBrackets, Crosshair, DotGrid, Grain, IndexLabel, LineField, TickRuler } from "@/components/ornament";

// WORKING DESIGN-LANGUAGE TEST -- not the final landing page. Exists to
// visually verify the token/ornament system before building the real
// nav, hero copy, and page structure on top of it.
export default function HomePage() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <Grain />
      <LineField className="pointer-events-none absolute inset-0 h-full w-full opacity-70" />

      <div className="relative mx-auto max-w-6xl px-6 py-8 sm:px-8 sm:py-10">
        <div className="flex flex-wrap items-center justify-between gap-y-3">
          <div className="flex items-center gap-3">
            <Crosshair className="text-[var(--steel-500)]" />
            <span className="font-mono-tech text-xs whitespace-nowrap text-[var(--steel-300)]">KAGUTSUCHI</span>
          </div>
          <TickRuler ticks={8} labelLeft="00" labelRight="04" className="hidden w-64 sm:flex" />
        </div>

        <section className="mt-16 max-w-3xl sm:mt-32">
          <div className="mb-4 flex items-center gap-3">
            <IndexLabel>001.04 — SYSTEM</IndexLabel>
            <DotGrid className="text-[var(--steel-700)]" />
          </div>
          <h1 className="font-serif-elegy text-3xl leading-[1.15] text-[var(--paper)] sm:text-5xl sm:leading-[1.1] md:text-6xl md:leading-[1.05]">
            an exploit proven is worth more than a warning believed.
          </h1>
          <p className="font-mono-tech mt-6 max-w-md text-[11px] leading-relaxed text-[var(--steel-500)] sm:mt-8">
            every finding is attacked for real, in an isolated sandbox, before it is ever called a vulnerability.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-4 sm:mt-10">
            <CornerBrackets className="px-6 py-3">
              <span className="font-mono-tech text-xs whitespace-nowrap text-[var(--paper)] uppercase">Run a scan</span>
            </CornerBrackets>
            <div className="flex items-center gap-2">
              <AccentChip tone="lime" />
              <span className="font-mono-tech text-[10px] whitespace-nowrap text-[var(--steel-500)] uppercase">verified fixed</span>
            </div>
            <div className="flex items-center gap-2">
              <AccentChip tone="magenta" />
              <span className="font-mono-tech text-[10px] whitespace-nowrap text-[var(--steel-500)] uppercase">high severity</span>
            </div>
            <AccentBar tone="blue" />
          </div>
        </section>

        <div className="mt-24 grid grid-cols-1 gap-px bg-[var(--line)] sm:mt-40 sm:grid-cols-3">
          {["05 vulnerability classes", "2 detection engines", "0 unverified verdicts"].map((label, i) => (
            <div key={i} className="panel-mist p-6">
              <div className="font-mono-tech text-3xl">{["05", "02", "00"][i]}</div>
              <div className="font-mono-tech mt-1 text-[10px] text-[var(--steel-700)] uppercase">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
