// Deterministic (seeded) so server/client render identically -- floating
// data motes drifting upward, cyan/pink, varied size/speed/delay.
const PARTICLES: [number, number, number, number, "cyan" | "pink"][] = [
  [24.8, 4.35, 8.96, 4, "pink"],
  [62.1, 0.52, 6.11, 3, "pink"],
  [54.9, 1.53, 11.74, 4, "pink"],
  [40.1, 6.89, 7.86, 2, "pink"],
  [73.2, 5.37, 6.51, 4, "cyan"],
  [30.9, 0.25, 12.92, 3, "pink"],
  [70.6, 7.37, 9.16, 4, "pink"],
  [94.6, 1.07, 8.92, 2, "cyan"],
  [49.5, 2.06, 11.38, 3, "pink"],
  [50.7, 3.09, 8.81, 4, "pink"],
  [58.1, 7.23, 11.46, 2, "pink"],
  [97.1, 5.37, 7.3, 3, "cyan"],
  [70.5, 1.69, 12.65, 4, "pink"],
  [29.4, 0.51, 12.83, 3, "cyan"],
  [35.0, 0.53, 13.18, 2, "pink"],
  [43.0, 3.32, 6.95, 4, "cyan"],
  [38.3, 4.69, 10.41, 3, "cyan"],
  [97.9, 2.48, 6.62, 4, "cyan"],
  [93.1, 7.77, 8.33, 3, "cyan"],
  [68.2, 7.84, 8.72, 3, "cyan"],
];

export function Particles() {
  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden" aria-hidden="true">
      {PARTICLES.map(([left, delay, duration, size, color], i) => (
        <span
          key={i}
          className="absolute bottom-0 rounded-full"
          style={{
            left: `${left}%`,
            width: size,
            height: size,
            background: color === "cyan" ? "var(--neon-cyan)" : "var(--neon-pink)",
            boxShadow: `0 0 ${size * 2}px ${color === "cyan" ? "var(--neon-cyan)" : "var(--neon-pink)"}`,
            animation: `float-up ${duration}s linear ${delay}s infinite`,
            opacity: 0,
          }}
        />
      ))}
    </div>
  );
}
