import Link from "next/link";
import { api } from "@/lib/api";
import ShotMap from "@/components/ShotMap";

function StatBox({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-3 text-center">
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs text-zinc-500 mt-0.5">{label}</div>
    </div>
  );
}

export default async function PlayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const playerId = Number(id);

  const [player, matches, shots] = await Promise.all([
    api.player(playerId),
    api.playerMatches(playerId),
    api.playerShots(playerId),
  ]);

  const t = player.career_totals;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">{player.known_name || player.name}</h1>
        <p className="text-zinc-500 text-sm mt-1">
          {player.teams_competitions.map((tc) => `${tc.team} · ${tc.competition} ${tc.season}`).join(" — ")}
        </p>
      </div>

      <section className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        <StatBox label="Matchs" value={t.matches} />
        <StatBox label="Minutes" value={t.minutes_played} />
        <StatBox label="Buts" value={t.goals} />
        <StatBox label="Passes D." value={t.assists} />
        <StatBox label="xG" value={t.xg.toFixed(2)} />
        <StatBox label="xA" value={t.xa.toFixed(2)} />
        <StatBox label="Tirs" value={t.shots} />
        <StatBox label="Tirs cadrés" value={t.shots_on_target} />
        <StatBox label="Passes réussies" value={`${t.passes_completed}/${t.passes_attempted}`} />
        <StatBox label="Passes progr." value={t.progressive_passes} />
        <StatBox label="Dribbles réussis" value={`${t.dribbles_completed}/${t.dribbles_attempted}`} />
        <StatBox label="Tacles" value={t.tackles} />
      </section>

      {shots.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-2">Carte des tirs</h2>
          <ShotMap shots={shots} />
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-2">Matchs</h2>
        <div className="overflow-x-auto rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 dark:bg-zinc-800 text-left text-zinc-500">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Adversaire</th>
                <th className="px-3 py-2">Score</th>
                <th className="px-3 py-2 text-center">Min</th>
                <th className="px-3 py-2 text-center">Buts</th>
                <th className="px-3 py-2 text-center">Passes D.</th>
                <th className="px-3 py-2 text-center">xG</th>
                <th className="px-3 py-2 text-center">Tirs</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((mt) => (
                <tr key={mt.match_id} className="border-t border-black/5 dark:border-white/5">
                  <td className="px-3 py-2">
                    <Link href={`/matches/${mt.match_id}`} className="hover:underline">{mt.date}</Link>
                  </td>
                  <td className="px-3 py-2">{mt.opponent}</td>
                  <td className="px-3 py-2">{mt.score}</td>
                  <td className="px-3 py-2 text-center">{mt.minutes_played}</td>
                  <td className="px-3 py-2 text-center">{mt.goals}</td>
                  <td className="px-3 py-2 text-center">{mt.assists}</td>
                  <td className="px-3 py-2 text-center">{mt.xg.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center">{mt.shots}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <Link
        href={`/compare?players=${playerId}`}
        className="inline-block px-4 py-2 rounded-full bg-blue-600 text-white text-sm hover:bg-blue-700"
      >
        Comparer ce joueur →
      </Link>
    </div>
  );
}
