import { formatTime } from "../model/calendar.ts";
import type { Itinerary, Leg } from "../planner/plan.ts";
import type { Schedule } from "../model/types.ts";

export function stopName(schedule: Schedule, id: string): string {
  return schedule.stops.find((s) => s.id === id)?.name ?? id;
}

export function lineCode(schedule: Schedule, id: string): string {
  return schedule.lines.find((l) => l.id === id)?.code ?? id;
}

export function isLanzadera(schedule: Schedule, id: string): boolean {
  return schedule.lines.find((l) => l.id === id)?.kind === "lanzadera";
}

/** Etiqueta corta que resume en que consiste el itinerario. */
export function summarize(schedule: Schedule, it: Itinerary): string {
  if (it.legs.length === 1 && it.legs[0]!.kind === "ride") return "directo";
  const parts = it.legs.map((leg: Leg) => {
    if (leg.kind === "walk") return `${leg.arrive - leg.depart} min andando`;
    return isLanzadera(schedule, leg.lineId) ? "lanzadera" : lineCode(schedule, leg.lineId);
  });
  return parts.join(" + ");
}

export function describeLeg(schedule: Schedule, leg: Leg): string {
  const from = stopName(schedule, leg.from);
  const to = stopName(schedule, leg.to);
  if (leg.kind === "walk") {
    return `Andando ${from} → ${to} · ${leg.arrive - leg.depart} min`;
  }
  const kind = isLanzadera(schedule, leg.lineId) ? "Lanzadera" : `Línea ${lineCode(schedule, leg.lineId)}`;
  return `${kind} · ${from} ${formatTime(leg.depart)} → ${to} ${formatTime(leg.arrive)}`;
}

/** "en 12 min", "sale ya", "hace 3 min". */
export function relativeTo(now: number, when: number): string {
  const d = when - now;
  if (d <= 0) return "ahora";
  if (d < 60) return `en ${d} min`;
  const h = Math.floor(d / 60);
  const m = d % 60;
  return m === 0 ? `en ${h} h` : `en ${h} h ${m} min`;
}
