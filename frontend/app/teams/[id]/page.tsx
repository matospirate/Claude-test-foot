import Link from "next/link";
import { api } from "@/lib/api";

export default async function TeamPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const teamId = Number(id);
  const [team, matchStats] = await Promise.all([api.team(teamId), api.teamMatchStats(teamId)]);

  const avgPpda = matchStats.filter((m) => m.ppda != null);
  const avgPossession = matchStats.filter((m) => m.possession_pct != null);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">{team.name}</h1>

      {matchStats.length > 0 && (
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-3 text-center">
            <div className="text-xl font-bold">
              {(matchStats.reduce((s, m) => s + m.xg, 0) / matchStats.length).toFixed(2)}
            </div>
            <div className="text-xs text-zinc-500">xG moyen / match</div>
          </div>
          <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-3 text-center">
            <div className="text-xl font-bold">
              {avgPossession.length
                ? (avgPossession.reduce((s, m) => s + (m.possession_pct || 0), 0) / avgPossession.length).toFixed(1)
                : "-"}%
            </div>
            <div className="text-xs text-zinc-500">Possession moyenne</div>
          </div>
          <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-3 text-center">
            <div className="text-xl font-bold">
              {avgPpda.length ? (avgPpda.reduce((s, m) => s + (m.ppda || 0), 0) / avgPpda.length).toFixed(1) : "-"}
            </div>
            <div className="text-xs text-zinc-500">PPDA moyen (pressing)</div>
          </div>
          <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-3 text-center">
            <div className="text-xl font-bold">
              {(matchStats.reduce((s, m) => s + m.shots, 0) / matchStats.length).toFixed(1)}
            </div>
            <div className="text-xs text-zinc-500">Tirs / match</div>
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-2">Effectif observé</h2>
        <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 divide-y divide-black/5 dark:divide-white/5">
          {team.squad.map((p) => (
            <Link
              key={p.player_id}
              href={`/players/${p.player_id}`}
              className="flex items-center justify-between px-4 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800"
            >
              <span className="font-medium">{p.name}</span>
              <span className="text-zinc-500">{p.appearances} matchs · {p.minutes} min</span>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Matchs</h2>
        <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 divide-y divide-black/5 dark:divide-white/5">
          {team.matches.map((mt) => (
            <Link
              key={mt.match_id}
              href={`/matches/${mt.match_id}`}
              className="flex items-center justify-between px-4 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800"
            >
              <span className="text-zinc-500 w-24">{mt.date}</span>
              <span className="flex-1 text-right pr-3">{mt.home_team}</span>
              <span className="font-semibold w-16 text-center">{mt.home_score ?? "-"} : {mt.away_score ?? "-"}</span>
              <span className="flex-1 pl-3">{mt.away_team}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
