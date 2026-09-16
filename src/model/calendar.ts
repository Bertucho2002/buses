import type { FrequencyCode, Period, Schedule, Trip } from "./types.ts";

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

/** "08:23" -> 503. Devuelve undefined para "--" y demas basura. */
export function parseTime(s: string): number | undefined {
  const m = /^(\d{1,2}):(\d{2})$/.exec(s.trim());
  if (!m) return undefined;
  const h = Number(m[1]);
  const min = Number(m[2]);
  if (min > 59) return undefined;
  return h * 60 + min;
}

/**
 * Si una expedicion con esta frecuencia circula en una fecha dada.
 *
 * Las frecuencias de CTAN se solapan a proposito: un martes lectivo encaja a
 * la vez en L-V, L-J, L-S y L-D, asi que el horario de un dia es la union de
 * todas las que casen.
 *
 * Devuelve false para las que no se pueden resolver (el "dia suelto", que no
 * lleva fecha asociada): mejor no enseñar un bus que puede no existir.
 */
export function frequencyMatches(
  code: FrequencyCode,
  date: Date,
  holidays: readonly string[],
): boolean {
  const dow = date.getDay(); // 0 domingo ... 6 sabado
  const festivo = holidays.includes(isoDate(date)) || dow === 0;
  const laborable = !festivo && dow !== 0;

  switch (code.trim().toUpperCase()) {
    case "L-V":
      return laborable && dow >= 1 && dow <= 5;
    case "L-J":
      return laborable && dow >= 1 && dow <= 4;
    case "V":
      return laborable && dow === 5;
    case "L":
      return laborable && dow === 1;
    case "L-S":
      return laborable && dow >= 1 && dow <= 6;
    case "S":
      return laborable && dow === 6;
    case "D":
    case "D*":
      return festivo;
    case "S-D-F":
      return festivo || (laborable && dow === 6);
    case "L-D":
      return true;
    default:
      // "-" (día suelto) y cualquier código que no conozcamos.
      return false;
  }
}

/** Códigos de frecuencia que no sabemos resolver, para poder avisar. */
export function unknownFrequencies(schedule: Schedule): string[] {
  const conocidos = new Set(["L-V", "L-J", "V", "L", "L-S", "S", "D", "D*", "S-D-F", "L-D"]);
  const raros = new Set<string>();
  for (const t of schedule.trips) {
    const c = t.days.trim().toUpperCase();
    if (!conocidos.has(c)) raros.add(t.days);
  }
  return [...raros];
}

export function periodFor(date: Date, periods: readonly Period[]): Period | undefined {
  const iso = isoDate(date);
  return periods.find((p) => p.from <= iso && iso <= p.to);
}

/**
 * Las expediciones que circulan en una fecha.
 *
 * Una expedicion con periodo solo circula dentro de sus fechas: asi una linea
 * que arranca a mitad de curso no aparece antes de tiempo. Las que no traen
 * periodo se dan por vigentes siempre, porque la fuente no siempre lo dice y
 * es preferible enseñar el horario que se tiene, avisando, a no enseñar nada.
 */
export function tripsForDate(schedule: Schedule, date: Date): Trip[] {
  const iso = isoDate(date);
  const periodos = new Map(schedule.periods.map((p) => [p.id, p]));
  return schedule.trips.filter((t) => {
    if (t.periodId) {
      const p = periodos.get(t.periodId);
      if (!p || iso < p.from || iso > p.to) return false;
    }
    return frequencyMatches(t.days, date, schedule.holidays);
  });
}

/**
 * true si los datos no cubren esa fecha, es decir, se han quedado viejos.
 *
 * Solo se puede afirmar cuando TODAS las expediciones estan atadas a un
 * periodo. Si alguna no lo esta, esa sigue valiendo para cualquier fecha y el
 * horario no esta caducado, por mucho que los periodos declarados no lleguen
 * a ese dia: es justo lo que pasa cuando se mezcla una fuente que trae
 * periodos con otra que no.
 */
export function outOfCoverage(schedule: Schedule, date: Date): boolean {
  if (schedule.periods.length === 0) return false;
  if (schedule.trips.some((t) => !t.periodId)) return false;
  return periodFor(date, schedule.periods) === undefined;
}
