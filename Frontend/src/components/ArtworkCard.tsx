// src/components/ArtworkCard.tsx
import React from "react";
import type { Artwork } from "../lib/api";

type Props = { item: Artwork };

export default function ArtworkCard({ item }: Props) {
  const thumb = item.thumbnail_url ?? item.file_url ?? "";
  const original = item.file_url ?? thumb;

  return (
    <button
      className="group w-full text-left"
      onClick={() => window.open(original, "_blank")}
      title={item.title}
    >
      <div className="aspect-square overflow-hidden rounded-2xl shadow-sm">
        <img
          src={thumb}
          alt={item.title}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
      </div>
      <div className="mt-2 text-sm font-medium line-clamp-1">{item.title}</div>
    </button>
  );
}
