// src/pages/Gallery.tsx
import React, { useCallback, useEffect, useState } from "react";
import { fetchArtworks, type Artwork } from "../lib/api";
import ArtworkCard from "../components/ArtworkCard";
import { useInfiniteScroll } from "../hooks/useInfiniteScroll";

const PER_PAGE = 24;

export default function Gallery() {
  const [items, setItems] = useState<Artwork[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState<string | null>(null);

  const hasMore = total === null || items.length < total;

  const load = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchArtworks(page, PER_PAGE);
      setItems((prev) => [...prev, ...data.items]);
      setTotal(data.total);
      setPage((p) => p + 1);
    } catch (e: any) {
      setError(e?.message ?? "Load error");
    } finally {
      setLoading(false);
    }
  }, [page, loading, hasMore]);

  const { sentinelRef, setEnabled } = useInfiniteScroll(load);

  useEffect(() => { setEnabled(true); }, [setEnabled]);
  useEffect(() => { load(); }, []); // primera página

  return (
    <div className="mx-auto max-w-7xl p-4">
      <h1 className="mb-4 text-2xl font-semibold">Gallery</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        {items.map((it) => <ArtworkCard key={it.id} item={it} />)}
      </div>

      {error && <div className="mt-4 text-sm text-red-600">{error}</div>}

      <div ref={sentinelRef} className="h-10" />

      <div className="py-6 text-center text-sm text-neutral-500">
        {loading ? "Loading..." : !hasMore ? "No more items" : null}
      </div>
    </div>
  );
}
