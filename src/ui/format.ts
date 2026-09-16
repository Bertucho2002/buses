import { formatTime } from "../model/calendar.ts";
import type { Itinerary, Leg } from "../planner/plan.ts";
import type { Schedule } from "../model/types.ts";

export function stopName(schedule: Schedule, id: string): string {
  return schedule.stops.find((s) => s.id === id)?.name ?? id;
}

export function lineCode(schedule: Schedule, id: string): string {
  return schedule.lines.find((l) => l.id === id)?.code ?? id;
}

/** Etiqueta corta que resume en qué consiste el itinerario. */
export function summarize(schedule: Schedule, it: Itinerary): string {
  if (it.legs.length === 1 && it.legs[0]!.kind === "ride") {
    return `directo · ${lineCode(schedule, (it.legs[0] as { lineId: string }).lineId)}`;
  }
  return it.legs
    .map((leg: Leg) =>
      leg.kind === "walk"
        ? `${leg.arrive - leg.depart} min andando`
        : lineCode(schedule, leg.lineId),
    )
    .join(" + ");
}

export function describeLeg(schedule: Schedule, leg: Leg): string {
  const from = stopName(schedule, leg.from);
  const to = stopName(schedule, leg.to);
  if (leg.kind === "walk") {
    return `Andando ${from} → ${to} · ${leg.arrive - leg.depart} min`;
  }
  return `Línea ${lineCode(schedule, leg.lineId)} · ${from} ${formatTime(leg.depart)} → ${to} ${formatTime(leg.arrive)}`;
}

/** "en 12 min", "en 1 h 5 min", "ahora". */
export function relativeTo(now: number, when: number): string {
  const d = when - now;
  if (d <= 0) return "ahora";
  if (d < 60) return `en ${d} min`;
  const h = Math.floor(d / 60);
  const m = d % 60;
  return m === 0 ? `en ${h} h` : `en ${h} h ${m} min`;
}
