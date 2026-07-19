"use client";

import { useEffect, useState } from "react";
import type { CompareResult, SearchResult } from "@/lib/api";
import PlayerRadar from "@/components/PlayerRadar";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CompareClient({ initialIds }: { initialIds: number[] }) {
  const [ids, setIds] = useState<number[]>(initialIds);
  const [names, setNames] = useState<Record<number, string>>({});
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult | null>(null);
  const [data, setData] = useState<CompareResult | null>(null);

  useEffect(() => {
    if (q.trim().length < 2) { setResults(null); return; }
    const t = setTimeout(async () => {
      const res = await fetch(`${API_URL}/api/search?q=${encodeURIComponent(q)}`);
      if (res.ok) setResults(await res.json());
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    if (ids.length === 0) { setData(null); return; }
    fetch(`${API_URL}/api/compare?player_ids=${ids.join(",")}`)
      .then((r) => r.json())
      .then((d: CompareResult) => {
        setData(d);
        const newNames = { ...names };
        d.players.forEach((p) => { newNames[p.player_id] = p.name; });
        setNames(newNames);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids.join(",")]);

  function addPlayer(id: number, name: string) {
    if (ids.includes(id) || ids.length >= 6) return;
    setIds([...ids, id]);
    setNames({ ...names, [id]: name });
    setQ("");
    setResults(null);
  }

  function removePlayer(id: number) {
    setIds(ids.filter((i) => i !== id));
  }

  return (
    <div className="space-y-6">
      <div className="relative max-w-md">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ajouter un joueur à comparer..."
          className="w-full rounded-full border border-black/10 dark:border-white/15 bg-white dark:bg-zinc-900 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
        />
        {results && results.players.length > 0 && (
          <div className="absolute mt-1 w-full rounded-lg border border-black/10 dark:border-white/15 bg-white dark:bg-zinc-900 shadow-lg overflow-hidden text-sm z-10">
            {results.players.map((p) => (
              <button
                key={p.id}
                onClick={() => addPlayer(p.id, p.name)}
                className="w-full text-left px-3 py-2 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              >
                {p.name}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-2 flex-wrap">
        {ids.map((pid) => (
          <span
            key={pid}
            className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/40 text-sm"
          >
            {names[pid] || pid}
            <button onClick={() => removePlayer(pid)} className="text-zinc-500 hover:text-red-600">✕</button>
          </span>
        ))}
      </div>

      {data && data.players.length > 0 && (
        <>
          <PlayerRadar data={data} />
          <div className="overflow-x-auto rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900">
            <table className="w-full text-sm">
              <thead className="bg-zinc-50 dark:bg-zinc-800 text-left text-zinc-500">
                <tr>
                  <th className="px-3 py-2">Métrique (par 90&apos;)</th>
                  {data.players.map((p) => <th key={p.player_id} className="px-3 py-2 text-center">{p.name}</th>)}
                </tr>
              </thead>
              <tbody>
                {data.metrics.map((metric) => (
                  <tr key={metric} className="border-t border-black/5 dark:border-white/5">
                    <td className="px-3 py-2 text-zinc-500">{metric}</td>
                    {data.players.map((p) => (
                      <td key={p.player_id} className="px-3 py-2 text-center">{p.per_90[metric]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
