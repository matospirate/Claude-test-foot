import CompareClient from "./CompareClient";

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ players?: string }>;
}) {
  const { players } = await searchParams;
  const initialIds = players ? players.split(",").map(Number).filter(Boolean) : [];
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Comparer des joueurs</h1>
      <p className="text-sm text-zinc-500">
        Statistiques ramenées à 90 minutes jouées, calculées à partir des données
        réelles StatsBomb (Coupe du Monde 2022, Euro 2024).
      </p>
      <CompareClient initialIds={initialIds} />
    </div>
  );
}
