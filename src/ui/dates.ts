import { isoDate } from "../model/calendar.ts";

export function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

export function addDays(d: Date, n: number): Date {
  const out = startOfDay(d);
  out.setDate(out.getDate() + n);
  return out;
}

export function sameDay(a: Date, b: Date): boolean {
  return isoDate(a) === isoDate(b);
}

/** "hoy", "mañana", "ayer" o el día de la semana con la fecha. */
export function describeDay(date: Date, today: Date): string {
  if (sameDay(date, today)) return "hoy";
  if (sameDay(date, addDays(today, 1))) return "mañana";
  if (sameDay(date, addDays(today, -1))) return "ayer";
  return date.toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" });
}

/** Etiqueta larga para la cabecera: "martes, 22 de septiembre". */
export function longDay(date: Date): string {
  return date.toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" });
}

/** El valor que espera un <input type="date">. */
export function inputValue(date: Date): string {
  return isoDate(date);
}

/** Lee un <input type="date"> sin que el huso horario lo desplace un día. */
export function fromInputValue(value: string): Date | undefined {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!m) return undefined;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return Number.isNaN(d.getTime()) ? undefined : d;
}
