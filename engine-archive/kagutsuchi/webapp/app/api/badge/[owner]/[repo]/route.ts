import { getLatestRepoScan } from "@/lib/db";

// A shields.io-style embeddable SVG badge, e.g.:
//   [![kagutsuchi](https://<site>/api/badge/pallets/flask)](https://<site>)
// Any README that embeds it advertises the product for free every time
// someone views that repo. Reflects the LAST scan this site actually ran
// against that repo (any commit, not one pinned like the permalink page)
// -- "0 findings, scanned 2 days ago" is a real, verifiable claim, not a
// vanity number, since it's exactly what a live re-scan would show as of
// that run.
function escapeXml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderBadge(label: string, message: string, color: string): string {
  // Rough per-character width estimate (Verdana 11px, shields.io's own
  // convention) - avoids pulling in a font-metrics library for a static
  // two-box badge.
  const charWidth = 6.5;
  const labelWidth = Math.round(label.length * charWidth) + 20;
  const messageWidth = Math.round(message.length * charWidth) + 20;
  const totalWidth = labelWidth + messageWidth;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="20" role="img" aria-label="${escapeXml(label)}: ${escapeXml(message)}">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="${totalWidth}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="${labelWidth}" height="20" fill="#0a0a0f"/>
    <rect x="${labelWidth}" width="${messageWidth}" height="20" fill="${color}"/>
    <rect width="${totalWidth}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text x="${labelWidth / 2}" y="14">${escapeXml(label)}</text>
    <text x="${labelWidth + messageWidth / 2}" y="14">${escapeXml(message)}</text>
  </g>
</svg>`;
}

export async function GET(_request: Request, { params }: { params: Promise<{ owner: string; repo: string }> }) {
  const { owner, repo } = await params;

  let svg: string;
  try {
    const latest = await getLatestRepoScan(owner, repo);
    if (!latest) {
      svg = renderBadge("kagutsuchi", "not yet scanned", "#6c7086");
    } else {
      const findings = (latest.response.findings as unknown[] | undefined) ?? [];
      const count = findings.length;
      svg = renderBadge(
        "kagutsuchi",
        count === 0 ? "0 findings" : `${count} finding${count === 1 ? "" : "s"}`,
        count === 0 ? "#00d4a0" : "#ff2e88",
      );
    }
  } catch {
    svg = renderBadge("kagutsuchi", "unavailable", "#6c7086");
  }

  return new Response(svg, {
    headers: {
      "Content-Type": "image/svg+xml",
      // Short cache - a badge that never updates after a repo's first
      // scan would be worse than no badge at all.
      "Cache-Control": "public, max-age=300, s-maxage=300",
    },
  });
}
