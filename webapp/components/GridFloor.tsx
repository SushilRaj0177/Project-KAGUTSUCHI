export function GridFloor() {
  return (
    <div
      className="pointer-events-none absolute right-0 bottom-0 left-0 z-0 h-64 overflow-hidden"
      style={{ perspective: "300px" }}
      aria-hidden="true"
    >
      <div
        className="absolute inset-0"
        style={{
          transform: "rotateX(75deg)",
          transformOrigin: "bottom",
          backgroundImage:
            "linear-gradient(rgba(42,245,255,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(42,245,255,0.35) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "linear-gradient(to top, black, transparent)",
          WebkitMaskImage: "linear-gradient(to top, black, transparent)",
        }}
      />
    </div>
  );
}
