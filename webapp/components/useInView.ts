import { useCallback, useEffect, useState } from "react";

export function useInView<T extends HTMLElement>() {
  const [el, setEl] = useState<T | null>(null);
  const [inView, setInView] = useState(false);

  // A callback ref (not useRef) so the effect re-attaches whenever the DOM
  // node actually appears -- e.g. behind a conditional render, where a
  // plain useRef's mount-time effect would run before the node exists and
  // never observe anything.
  const ref = useCallback((node: T | null) => {
    setEl(node);
  }, []);

  useEffect(() => {
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [el]);

  return { ref, inView };
}
