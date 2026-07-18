import Link from "next/link";
import { api } from "@/lib/api";

const LEADER_STATS: { key: string; label: string }[] = [
  { key: "goals", label: "Buts" },
  { key: "assists", label: "Passes décisives" },
  { key: "xg", label: "xG" },
  { key: "xa", label: "xA" },
  { key: "key_passes", label: "Passes clés" },
  { key: "tackles", label: "Tacles" },
];

export default async function CompetitionPage({
  params, searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ stat?: string }>;
}) {
  const { id } = await params;
  const competitionId = Number(id);
  const { stat = "goals" } = await searchParams;

  const [competitions, matches, standings, leaders] = await Promise.all([
    api.competitions(),
    api.competitionMatches(competitionId),
    api.competitionStandings(competitionId),
    api.competitionLeaders(competitionId, stat, 10),
  ]);
  const competition = competitions.find((c) => c.id === competitionId);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">{competition?.name} {competition?.season_name}</h1>

      <section>
        <h2 className="text-lg font-semibold mb-2">Classement (calculé à partir des résultats réels)</h2>
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
                <th className="px-3 py-2 text-center">Diff</th>
                <th className="px-3 py-2 text-center font-semibold">Pts</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((s) => (
                <tr key={s.team} className="border-t border-black/5 dark:border-white/5">
                  <td className="px-3 py-2">{s.position}</td>
                  <td className="px-3 py-2 font-medium">{s.team}</td>
                  <td className="px-3 py-2 text-center">{s.played}</td>
                  <td className="px-3 py-2 text-center">{s.won}</td>
                  <td className="px-3 py-2 text-center">{s.drawn}</td>
                  <td className="px-3 py-2 text-center">{s.lost}</td>
                  <td className="px-3 py-2 text-center">{s.goal_diff}</td>
                  <td className="px-3 py-2 text-center font-semibold">{s.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-zinc-500 mt-1">
          Pour un tournoi à élimination directe, ce tableau reflète l&apos;ensemble des matchs joués
          (phase de groupes + phases finales) et non un vrai classement de championnat.
        </p>
      </section>

      <section>
        <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
          <h2 className="text-lg font-semibold">Meilleurs joueurs</h2>
          <div className="flex gap-1 flex-wrap">
            {LEADER_STATS.map((s) => (
              <Link
                key={s.key}
                href={`/competitions/${id}?stat=${s.key}`}
                className={`px-3 py-1 rounded-full text-xs border ${
                  s.key === stat
                    ? "bg-blue-600 text-white border-blue-600"
                    : "border-black/10 dark:border-white/15 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                }`}
              >
                {s.label}
              </Link>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 divide-y divide-black/5 dark:divide-white/5">
          {leaders.map((l, i) => (
            <Link
              key={l.player_id}
              href={`/players/${l.player_id}`}
              className="flex items-center justify-between px-4 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800"
            >
              <span className="flex items-center gap-3">
                <span className="text-zinc-400 w-4">{i + 1}</span>
                <span className="font-medium">{l.player_name}</span>
                <span className="text-zinc-500 text-xs">{l.team_name}</span>
              </span>
              <span className="font-semibold">{l.value}</span>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Matchs</h2>
        <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 divide-y divide-black/5 dark:divide-white/5">
          {matches.map((mt) => (
            <Link
              key={mt.id}
              href={`/matches/${mt.id}`}
              className="flex items-center justify-between px-4 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800"
            >
              <span className="text-zinc-500 w-24">{mt.match_date}</span>
              <span className="flex-1 text-right pr-3">{mt.home_team.name}</span>
              <span className="font-semibold w-16 text-center">
                {mt.home_score ?? "-"} : {mt.away_score ?? "-"}
              </span>
              <span className="flex-1 pl-3">{mt.away_team.name}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
