import Link from "next/link";
import { api } from "@/lib/api";

export default async function LeaguePage({
  params, searchParams,
}: {
  params: Promise<{ code: string }>;
  searchParams: Promise<{ season?: string }>;
}) {
  const { code } = await params;
  const { season = "2025-26" } = await searchParams;

  const [leagues, standings] = await Promise.all([
    api.leagues(),
    api.standings(code, season),
  ]);
  const league = leagues.find((l) => l.code === code);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{league?.name ?? code}</h1>
        <div className="flex gap-2">
          {league?.seasons.map((s) => (
            <Link
              key={s}
              href={`/leagues/${code}?season=${s}`}
              className={`px-3 py-1 rounded-full text-sm border ${
                s === season
                  ? "bg-blue-600 text-white border-blue-600"
                  : "border-black/10 dark:border-white/15 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              }`}
            >
              {s}
            </Link>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900">
        <table className="w-full text-sm">
          <thead className="bg-zinc-50 dark:bg-zinc-800 text-left text-zinc-500">
            <tr>
              <th className="px-3 py-2">#</th>
              <th className="px-3 py-2">Équipe</th>
              <th className="px-3 py-2 text-center">MJ</th>
              <th className="px-3 py-2 text-center">V</th>
              <th className="px-3 py-2 text-center">N</th>
              <th className="px-3 py-2 text-center">D</th>
              <th className="px-3 py-2 text-center">BP</th>
              <th className="px-3 py-2 text-center">BC</th>
              <th className="px-3 py-2 text-center">Diff</th>
              <th className="px-3 py-2 text-center font-semibold">Pts</th>
            </tr>
          </thead>
          <tbody>
            {standings.map((s, i) => (
              <tr
                key={s.team_name}
                className={`border-t border-black/5 dark:border-white/5 ${
                  i < 4 ? "bg-blue-50/50 dark:bg-blue-950/20" : i >= standings.length - 3 ? "bg-red-50/50 dark:bg-red-950/20" : ""
                }`}
              >
                <td className="px-3 py-2">{s.position}</td>
                <td className="px-3 py-2 font-medium">{s.team_name}</td>
                <td className="px-3 py-2 text-center">{s.played}</td>
                <td className="px-3 py-2 text-center">{s.won}</td>
                <td className="px-3 py-2 text-center">{s.drawn}</td>
                <td className="px-3 py-2 text-center">{s.lost}</td>
                <td className="px-3 py-2 text-center">{s.goals_for}</td>
                <td className="px-3 py-2 text-center">{s.goals_against}</td>
                <td className="px-3 py-2 text-center">{s.goal_diff > 0 ? `+${s.goal_diff}` : s.goal_diff}</td>
                <td className="px-3 py-2 text-center font-semibold">{s.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-zinc-500">
        Source : openfootball (résultats réels). Certains matchs récents peuvent
        ne pas encore être remontés dans la source et sont exclus du classement.
      </p>
    </div>
  );
}
