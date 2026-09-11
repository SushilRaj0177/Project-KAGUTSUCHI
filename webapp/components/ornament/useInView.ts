"use client";

import { useEffect, useRef, useState } from "react";

// Minimal IntersectionObserver hook backing ScrollReveal.tsx -- fires
// once an element crosses into the viewport, so content can animate in
// on scroll instead of just sitting fully rendered at load. `once`
// (default true) stops observing after the first reveal, since a
// reveal-on-scroll effect firing again on scroll-back-up reads as a
// glitch in the wrong sense.
export function useInView<T extends HTMLElement>(options?: IntersectionObserverInit & { once?: boolean }) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const once = options?.once ?? true;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          if (once) observer.disconnect();
        } else if (!once) {
          setInView(false);
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -10% 0px", ...options },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [options]);

  return { ref, inView };
}
