"use client";

/**
 * A material-style click ripple, applied imperatively via onPointerDown
 * rather than as a wrapping component - so it can attach to an existing
 * <button>/<a> without changing what it renders as. The element it's
 * attached to needs `.ripple-host` (position: relative + overflow: hidden)
 * in CSS. No-ops under prefers-reduced-motion.
 */
export function spawnRipple(e: React.PointerEvent<HTMLElement>) {
  if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const target = e.currentTarget;
  const rect = target.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height) * 1.8;
  const span = document.createElement("span");
  span.className = "ripple";
  span.style.width = `${size}px`;
  span.style.height = `${size}px`;
  span.style.left = `${e.clientX - rect.left - size / 2}px`;
  span.style.top = `${e.clientY - rect.top - size / 2}px`;
  target.appendChild(span);
  span.addEventListener("animationend", () => span.remove());
}
