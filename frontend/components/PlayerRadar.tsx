"use client";

import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Legend, Tooltip,
} from "recharts";
import type { CompareResult } from "@/lib/api";

const METRIC_LABELS: Record<string, string> = {
  goals: "Buts",
  assists: "Passes D.",
  xg: "xG",
  xa: "xA",
  shots: "Tirs",
  key_passes: "Passes clés",
  passes_completed: "Passes réussies",
  progressive_passes: "Passes progr.",
  progressive_carries: "Courses progr.",
  dribbles_completed: "Dribbles",
  tackles: "Tacles",
  interceptions: "Interceptions",
  pressures: "Pressings",
  ball_recoveries: "Récupérations",
};

const COLORS = ["#2563eb", "#dc2626", "#16a34a", "#a855f7", "#f59e0b", "#0891b2"];

export default function PlayerRadar({ data }: { data: CompareResult }) {
  if (!data.players.length) return null;

  // normalize each metric to 0-100 scale across the compared players so the
  // radar is readable even though metrics have very different units (per-90)
  const maxByMetric: Record<string, number> = {};
  for (const metric of data.metrics) {
    maxByMetric[metric] = Math.max(0.001, ...data.players.map((p) => p.per_90[metric] || 0));
  }

  const chartData = data.metrics.map((metric) => {
    const row: Record<string, number | string> = { metric: METRIC_LABELS[metric] || metric };
    for (const p of data.players) {
      row[p.name] = Math.round(((p.per_90[metric] || 0) / maxByMetric[metric]) * 100);
    }
    return row;
  });

  return (
    <div className="w-full h-[420px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={chartData} outerRadius="75%">
          <PolarGrid />
          <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} />
          {data.players.map((p, i) => (
            <Radar
              key={p.player_id}
              name={p.name}
              dataKey={p.name}
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length]}
              fillOpacity={0.2}
            />
          ))}
          <Legend />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
