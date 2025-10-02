// src/hooks/useInfiniteScroll.ts
import { useEffect, useRef, useState } from "react";

export function useInfiniteScroll(onLoadMore: () => void) {
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (!enabled || !sentinelRef.current) return;
    const el = sentinelRef.current;

    const io = new IntersectionObserver((entries) => {
      const e = entries[0];
      if (e.isIntersecting) onLoadMore();
    }, { rootMargin: "800px 0px" }); // pre-carga antes de llegar al fondo

    io.observe(el);
    return () => io.disconnect();
  }, [enabled, onLoadMore]);

  return { sentinelRef, setEnabled };
}
