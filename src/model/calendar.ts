import type { Calendar, DayType, Period, Schedule } from "./types.ts";

/** Fecha local (no UTC) en formato YYYY-MM-DD. */
export function isoDate(d: Date): string {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function minutesOfDay(d: Date): number {
  return d.getHours() * 60 + d.getMinutes();
}

export function formatTime(m: number): string {
  const wrapped = ((m % 1440) + 1440) % 1440;
  const h = Math.floor(wrapped / 60);
  return `${String(h).padStart(2, "0")}:${String(wrapped % 60).padStart(2, "0")}`;
}

/** Que tipo de dia es una fecha, teniendo en cuenta los festivos declarados. */
export function dayTypeFor(date: Date, holidays: readonly string[]): DayType {
  if (holidays.includes(isoDate(date))) return "domingo-festivo";
  const dow = date.getDay(); // 0 domingo ... 6 sabado
  if (dow === 0) return "domingo-festivo";
  if (dow === 6) return "sabado";
  return "laborable";
}

export function periodFor(date: Date, periods: readonly Period[]): Period | undefined {
  const iso = isoDate(date);
  return periods.find((p) => p.from <= iso && iso <= p.to);
}

/**
 * El horario vigente en una fecha dada.
 *
 * Devuelve undefined si la fecha cae fuera de todos los periodos conocidos,
 * que es justo lo que pasa cuando los datos se han quedado viejos. Quien
 * llama debe distinguir ese caso de "hoy no hay servicio" y avisar al usuario,
 * porque no es lo mismo no tener bus que no tener datos.
 */
export function calendarFor(date: Date, schedule: Schedule): Calendar | undefined {
  const period = periodFor(date, schedule.periods);
  if (!period) return undefined;
  const dayType = dayTypeFor(date, schedule.holidays);
  return schedule.calendars.find((c) => c.periodId === period.id && c.dayType === dayType);
}
