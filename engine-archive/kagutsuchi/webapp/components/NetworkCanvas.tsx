"use client";

import { useEffect, useRef } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  state: "idle" | "flagged" | "attacking" | "verified";
  timer: number;
}

const COLORS = {
  idle: "rgba(180, 190, 200, 0.55)",
  flagged: "rgba(255, 61, 118, 0.9)",
  attacking: "rgba(255, 176, 32, 0.95)",
  verified: "rgba(120, 230, 140, 0.95)",
};

// Live animated node network standing in for the whole site's hero --
// not a typographic/poster composition, an actual real-time simulation
// of what the product does: nodes (files/functions) drift, occasionally
// get "flagged," get "attacked," then turn "verified." This is meant to
// read as a live system dashboard, not a designed page.
export function NetworkCanvas({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    function resize() {
      const canvas = canvasRef.current;
      if (!canvas) return;
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);

    const NODE_COUNT = Math.round((window.innerWidth * window.innerHeight) / 18000);
    const nodes: Node[] = Array.from({ length: Math.min(Math.max(NODE_COUNT, 30), 90) }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.28,
      vy: (Math.random() - 0.5) * 0.28,
      state: "idle",
      timer: 0,
    }));

    const mouse = { x: -9999, y: -9999 };
    function onMove(e: MouseEvent) {
      const rect = canvas!.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    }
    window.addEventListener("mousemove", onMove, { passive: true });

    let frame: number;
    let lastFlag = 0;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function tick(t: number) {
      if (!ctx || !canvasRef.current) return;
      ctx.clearRect(0, 0, width, height);

      // occasionally promote a random idle node into the
      // flagged -> attacking -> verified -> idle lifecycle
      if (t - lastFlag > 900 && Math.random() < 0.6) {
        lastFlag = t;
        const idle = nodes.filter((n) => n.state === "idle");
        if (idle.length) {
          const n = idle[Math.floor(Math.random() * idle.length)];
          n.state = "flagged";
          n.timer = t;
        }
      }

      for (const n of nodes) {
        if (!reduceMotion) {
          n.x += n.vx;
          n.y += n.vy;
          if (n.x < 0 || n.x > width) n.vx *= -1;
          if (n.y < 0 || n.y > height) n.vy *= -1;
          const dx = n.x - mouse.x;
          const dy = n.y - mouse.y;
          const dist = Math.hypot(dx, dy);
          if (dist < 90) {
            n.x += (dx / (dist || 1)) * 0.6;
            n.y += (dy / (dist || 1)) * 0.6;
          }
        }

        const elapsed = t - n.timer;
        if (n.state === "flagged" && elapsed > 500) {
          n.state = "attacking";
          n.timer = t;
        } else if (n.state === "attacking" && elapsed > 700) {
          n.state = "verified";
          n.timer = t;
        } else if (n.state === "verified" && elapsed > 1600) {
          n.state = "idle";
          n.timer = t;
        }
      }

      // connective lines between nearby nodes
      ctx.lineWidth = 1;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const d = Math.hypot(a.x - b.x, a.y - b.y);
          if (d < 140) {
            const alpha = (1 - d / 140) * 0.18;
            ctx.strokeStyle = `rgba(200, 210, 220, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      for (const n of nodes) {
        const radius = n.state === "idle" ? 2 : 3.6;
        ctx.beginPath();
        ctx.fillStyle = COLORS[n.state];
        ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
        ctx.fill();
        if (n.state !== "idle") {
          ctx.beginPath();
          ctx.strokeStyle = COLORS[n.state];
          ctx.globalAlpha = 0.4;
          ctx.arc(n.x, n.y, radius + 5, 0, Math.PI * 2);
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }

      frame = requestAnimationFrame(tick);
    }
    frame = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(frame);
    };
  }, []);

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />;
}
