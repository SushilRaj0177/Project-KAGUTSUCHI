"use client";

import { useRef, type ButtonHTMLAttributes } from "react";

export function MagneticButton({
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  const ref = useRef<HTMLButtonElement>(null);

  function onMouseMove(e: React.MouseEvent<HTMLButtonElement>) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    el.style.transform = `translate(${x * 0.25}px, ${y * 0.35}px)`;
  }

  function onMouseLeave() {
    if (ref.current) ref.current.style.transform = "translate(0, 0)";
  }

  return (
    <button
      ref={ref}
      data-cursor="hover"
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      className={`magnetic-btn ${className ?? ""}`}
      {...props}
    >
      {children}
    </button>
  );
}
