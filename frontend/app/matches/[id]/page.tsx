import Link from "next/link";
import { api } from "@/lib/api";
import ShotMap from "@/components/ShotMap";

function TeamStatsTable({ home, away }: {
  home: NonNullable<Awaited<ReturnType<typeof api.match>>["home_team"]["stats"]>;
  away: NonNullable<Awaited<ReturnType<typeof api.match>>["away_team"]["stats"]>;
}) {
  const rows: [string, number | string, number | string][] = [
    ["Tirs", home.shots, away.shots],
    ["Tirs cadrés", home.shots_on_target, away.shots_on_target],
    ["xG", home.xg.toFixed(2), away.xg.toFixed(2)],
    ["Possession", home.possession_pct ? `${home.possession_pct}%` : "-", away.possession_pct ? `${away.possession_pct}%` : "-"],
    ["Passes réussies", `${home.passes_completed}/${home.passes_attempted}`, `${away.passes_completed}/${away.passes_attempted}`],
    ["PPDA (pressing)", home.ppda ?? "-", away.ppda ?? "-"],
    ["Fautes", home.fouls, away.fouls],
  ];
  return (
    <table className="w-full text-sm">
      <tbody>
        {rows.map(([label, h, a]) => (
          <tr key={label} className="border-t border-black/5 dark:border-white/5">
            <td className="px-3 py-2 text-right font-medium w-1/3">{h}</td>
            <td className="px-3 py-2 text-center text-zinc-500">{label}</td>
            <td className="px-3 py-2 text-left font-medium w-1/3">{a}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default async function MatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const matchId = Number(id);
  const [match, shots] = await Promise.all([api.match(matchId), api.matchShots(matchId)]);

  return (
    <div className="space-y-8">
      <div className="text-center">
        <div className="text-xs text-zinc-500 mb-1">
          {match.competition.name} {match.competition.season} · {match.date} {match.stadium ? `· ${match.stadium}` : ""}
        </div>
        <div className="flex items-center justify-center gap-6 text-2xl font-bold">
          <Link href={`/teams/${match.home_team.id}`} className="hover:underline">{match.home_team.name}</Link>
          <span>{match.home_team.score} - {match.away_team.score}</span>
          <Link href={`/teams/${match.away_team.id}`} className="hover:underline">{match.away_team.name}</Link>
        </div>
        {match.goals.length > 0 && (
          <div className="mt-2 text-sm text-zinc-500 flex justify-center gap-4 flex-wrap">
            {match.goals.map((g, i) => (
              <span key={i}>⚽ {g.player} {g.minute}&apos;</span>
            ))}
          </div>
        )}
      </div>

      {match.home_team.stats && match.away_team.stats && (
        <section>
          <h2 className="text-lg font-semibold mb-2 text-center">Statistiques du match</h2>
          <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900">
            <TeamStatsTable home={match.home_team.stats} away={match.away_team.stats} />
          </div>
        </section>
      )}

      {shots.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-2">Carte des tirs (les deux équipes)</h2>
          <ShotMap
            shots={shots}
            teamColors={{ [match.home_team.id]: "#2563eb", [match.away_team.id]: "#dc2626" }}
          />
          <div className="flex justify-center gap-6 mt-2 text-xs">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-600 inline-block" /> {match.home_team.name}</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-600 inline-block" /> {match.away_team.name}</span>
          </div>
        </section>
      )}

      <section className="grid sm:grid-cols-2 gap-6">
        {[match.home_team, match.away_team].map((side) => (
          <div key={side.id}>
            <h3 className="font-semibold mb-2">{side.name}</h3>
            <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 divide-y divide-black/5 dark:divide-white/5">
              {side.lineup.map((l) => (
                <Link
                  key={l.player_id}
                  href={`/players/${l.player_id}`}
                  className="flex items-center justify-between px-3 py-1.5 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800"
                >
                  <span className={l.is_starter ? "font-medium" : "text-zinc-500"}>
                    {l.jersey_number ? `${l.jersey_number}. ` : ""}{l.name}
                  </span>
                  <span className="text-xs text-zinc-500">{l.position} · {l.minutes_played}&apos;</span>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
