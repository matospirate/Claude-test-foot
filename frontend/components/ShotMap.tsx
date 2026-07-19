"use client";

import { useState } from "react";
import type { Shot } from "@/lib/api";

// StatsBomb pitch is 120 (x) x 80 (y). We render a half-pitch (attacking third+)
// shot map since almost all shots happen in the attacking half.
const PITCH_LENGTH = 120;
const PITCH_WIDTH = 80;

function colorFor(outcome: string | null) {
  if (outcome === "Goal") return "#16a34a";
  if (outcome === "Saved" || outcome === "Saved to Post") return "#2563eb";
  if (outcome === "Blocked") return "#f59e0b";
  return "#9ca3af"; // off target / post / wayward
}

export default function ShotMap({ shots, teamColors }: {
  shots: (Shot & { teamLabel?: string })[];
  teamColors?: Record<number, string>;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  const withLoc = shots.filter((s) => s.x != null && s.y != null);

  return (
    <div className="w-full">
      <svg viewBox="0 0 120 80" className="w-full h-auto bg-green-700/90 rounded-lg">
        {/* pitch markings (half pitch, attacking towards x=120) */}
        <rect x="0" y="0" width="120" height="80" fill="none" stroke="white" strokeWidth="0.4" />
        <rect x="102" y="18" width="18" height="44" fill="none" stroke="white" strokeWidth="0.3" />
        <rect x="114" y="30" width="6" height="20" fill="none" stroke="white" strokeWidth="0.3" />
        <circle cx="108" cy="40" r="0.6" fill="white" />
        <path d="M 96 30 A 10 10 0 0 1 96 50" fill="none" stroke="white" strokeWidth="0.3" />

        {withLoc.map((s, i) => {
          const r = 1 + Math.sqrt(Math.max(s.xg, 0.01)) * 4.5;
          const fill = teamColors && s.team_id ? teamColors[s.team_id] : colorFor(s.outcome);
          return (
            <circle
              key={i}
              cx={s.x!}
              cy={s.y!}
              r={r}
              fill={s.outcome === "Goal" ? fill : "none"}
              stroke={fill}
              strokeWidth="0.5"
              opacity={hovered === null || hovered === i ? 0.9 : 0.25}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
            />
          );
        })}
      </svg>
      {hovered !== null && withLoc[hovered] && (
        <div className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          {withLoc[hovered].player_name && <span className="font-medium">{withLoc[hovered].player_name} · </span>}
          {withLoc[hovered].minute}&apos; · xG {withLoc[hovered].xg.toFixed(2)} · {withLoc[hovered].outcome}
          {withLoc[hovered].body_part && ` · ${withLoc[hovered].body_part}`}
        </div>
      )}
      <div className="flex gap-4 mt-2 text-xs text-zinc-500">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-600 inline-block" /> But</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full border border-blue-600 inline-block" /> Arrêté</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full border border-amber-500 inline-block" /> Contré</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full border border-gray-400 inline-block" /> Non cadré</span>
        <span className="ml-auto">taille = xG</span>
      </div>
    </div>
  );
}
