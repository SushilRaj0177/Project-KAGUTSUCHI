import { ImageResponse } from "next/og";

export const alt = "KAGUTSUCHI — Find the vulnerability. Attack it for real. Prove the fix.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const NODES = [
  { x: 120, y: 90 }, { x: 320, y: 60 }, { x: 560, y: 130 }, { x: 780, y: 70 },
  { x: 1000, y: 110 }, { x: 1100, y: 260 }, { x: 60, y: 300 }, { x: 260, y: 380 },
  { x: 950, y: 420 }, { x: 1080, y: 520 }, { x: 140, y: 540 }, { x: 40, y: 480 },
];
const EDGES: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [0, 6], [6, 7], [7, 10], [10, 11], [5, 8], [8, 9],
];

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px 96px",
          background: "#020617",
          position: "relative",
        }}
      >
        <svg
          width="1200"
          height="630"
          style={{ position: "absolute", top: 0, left: 0 }}
        >
          {EDGES.map(([a, b], i) => (
            <line
              key={i}
              x1={NODES[a].x}
              y1={NODES[a].y}
              x2={NODES[b].x}
              y2={NODES[b].y}
              stroke="rgba(148,163,184,0.35)"
              strokeWidth={1.5}
            />
          ))}
          {NODES.map((n, i) => (
            <circle
              key={i}
              cx={n.x}
              cy={n.y}
              r={i === 9 ? 7 : 5}
              fill={i === 9 ? "#f43f5e" : "rgba(226,232,240,0.6)"}
            />
          ))}
        </svg>

        <div
          style={{
            display: "flex",
            fontSize: 28,
            letterSpacing: 4,
            color: "#94a3b8",
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          KAGUTSUCHI
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            marginTop: 24,
            fontSize: 58,
            lineHeight: 1.2,
            color: "#f8fafc",
            fontWeight: 700,
            width: 920,
          }}
        >
          <div style={{ display: "flex" }}>Find the vulnerability.</div>
          <div style={{ display: "flex" }}>Attack it for real.</div>
          <div style={{ display: "flex" }}>Prove the fix.</div>
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 32,
            fontSize: 26,
            color: "#94a3b8",
            width: 720,
          }}
        >
          Real static analysis, a real sandboxed exploit, a real proposed fix — not an LLM&apos;s opinion.
        </div>
      </div>
    ),
    { ...size },
  );
}
