import Link from "next/link";
import { api } from "@/lib/api";

export default async function Home() {
  const [leagues, competitions] = await Promise.all([api.leagues(), api.competitions()]);

  return (
    <div className="space-y-10">
      <section className="text-center py-8">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-3">
          Statistiques football, données réelles
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
          Classements et résultats réels des 5 grands championnats, et statistiques
          événementielles détaillées (xG, passes, actions défensives) pour les
          compétitions couvertes par StatsBomb open-data.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">Championnats (classements réels)</h2>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {leagues.map((l) => (
            <Link
              key={l.code}
              href={`/leagues/${l.code}`}
              className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-4 text-center hover:shadow-md transition-shadow"
            >
              <div className="font-medium">{l.name}</div>
              <div className="text-xs text-zinc-500 mt-1">{l.seasons[0]}</div>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">Compétitions avec données détaillées (xG, passes, tirs...)</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {competitions.map((c) => (
            <Link
              key={c.id}
              href={`/competitions/${c.id}`}
              className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-4 hover:shadow-md transition-shadow flex justify-between items-center"
            >
              <div>
                <div className="font-medium">{c.name} {c.season_name}</div>
                <div className="text-xs text-zinc-500 mt-1">{c.matches_ingested} matchs analysés</div>
              </div>
              <span className="text-blue-600 dark:text-blue-400 text-sm">Explorer →</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-zinc-900 p-4">
        <h2 className="text-lg font-semibold mb-2">À propos des données</h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Cette application utilise exclusivement des sources de données ouvertes et
          gratuites : <strong>openfootball</strong> pour les résultats/classements des
          5 grands championnats, et <strong>StatsBomb open-data</strong> pour les
          statistiques événementielles réelles (xG, passes, tirs, actions défensives)
          sur la Coupe du Monde 2022 et l&apos;Euro 2024. Aucune donnée n&apos;est
          inventée ; les métriques indisponibles gratuitement (contrats, valeur
          marchande, historique médical, tracking physique) ne sont pas affichées.
        </p>
      </section>
    </div>
  );
}
