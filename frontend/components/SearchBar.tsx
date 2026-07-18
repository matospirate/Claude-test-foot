"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { SearchResult } from "@/lib/api";

export default function SearchBar() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult | null>(null);
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (q.trim().length < 2) {
      setResults(null);
      return;
    }
    const t = setTimeout(async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/search?q=${encodeURIComponent(q)}`);
      if (res.ok) setResults(await res.json());
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("click", onClickOutside);
    return () => document.removeEventListener("click", onClickOutside);
  }, []);

  return (
    <div className="relative w-56 sm:w-72" ref={boxRef}>
      <input
        value={q}
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        placeholder="Rechercher joueur, équipe..."
        className="w-full rounded-full border border-black/10 dark:border-white/15 bg-zinc-50 dark:bg-zinc-900 px-4 py-1.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
      />
      {open && results && (results.players.length > 0 || results.teams.length > 0) && (
        <div className="absolute mt-1 w-full rounded-lg border border-black/10 dark:border-white/15 bg-white dark:bg-zinc-900 shadow-lg overflow-hidden text-sm z-30">
          {results.players.map((p) => (
            <button
              key={`p-${p.id}`}
              className="w-full text-left px-3 py-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 flex justify-between"
              onClick={() => { router.push(`/players/${p.id}`); setOpen(false); setQ(""); }}
            >
              <span>{p.name}</span>
              <span className="text-zinc-400 text-xs">Joueur</span>
            </button>
          ))}
          {results.teams.map((t) => (
            <button
              key={`t-${t.id}`}
              className="w-full text-left px-3 py-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 flex justify-between"
              onClick={() => { router.push(`/teams/${t.id}`); setOpen(false); setQ(""); }}
            >
              <span>{t.name}</span>
              <span className="text-zinc-400 text-xs">Équipe</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
