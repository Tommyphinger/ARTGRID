// src/lib/api.ts
export type Artwork = {
  id: number;
  title: string;
  file_url: string | null;
  thumbnail_url: string | null;
  submission_date?: string | null;
};

export type PageResp = {
  page: number;
  per_page: number;
  total: number;
  items: Artwork[];
};

const BASE = ""; // mismo origen (lo sirve Flask). Si usas otro, pon URL completa.

export async function fetchArtworks(page = 1, perPage = 24): Promise<PageResp> {
  const res = await fetch(`${BASE}/api/artworks?page=${page}&per_page=${perPage}`);
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
  return res.json();
}
