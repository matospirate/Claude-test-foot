import Link from "next/link";
import { api } from "@/lib/api";

export default async function CompetitionsPage() {
  const competitions = await api.competitions();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Compétitions à données détaillées</h1>
      <div className="grid gap-3 sm:grid-cols-2">
        {competitions.map((c) => (
          <Link
            key={c.id}
            href={`/competitions/${c.id}`}
            className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-4 hover:shadow-md"
          >
            <div className="font-medium">{c.name} {c.season_name}</div>
            <div className="text-xs text-zinc-500 mt-1">{c.matches_ingested} matchs · {c.country}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
