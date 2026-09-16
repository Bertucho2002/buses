import type { LineId, Minutes, Schedule, StopId, Trip } from "../model/types.ts";
import { tripsForDate } from "../model/calendar.ts";

export interface RideLeg {
  kind: "ride";
  lineId: LineId;
  from: StopId;
  to: StopId;
  depart: Minutes;
  arrive: Minutes;
}

export interface WalkLeg {
  kind: "walk";
  from: StopId;
  to: StopId;
  depart: Minutes;
  arrive: Minutes;
}

export type Leg = RideLeg | WalkLeg;

export interface Itinerary {
  legs: Leg[];
  /** Hora a la que hay que estar en la primera parada. */
  depart: Minutes;
  arrive: Minutes;
  destination: StopId;
}

export interface PlanOptions {
  schedule: Schedule;
  /** Fecha del viaje: decide que expediciones circulan. */
  date: Date;
  origin: StopId;
  /** Vale cualquiera de estas. Para ir a clase: la ESI, o el CASEM y andar. */
  destinations: readonly StopId[];
  /** No se consideran salidas antes de esta hora. */
  earliestBoarding: Minutes;
  /** Margen minimo para enlazar entre dos autobuses en la misma parada. */
  minTransferMinutes?: number;
  /** Cuanto tiempo hacia delante mirar. */
  windowMinutes?: number;
  /** Tope de tramos (un tramo = un bus o un tramo andando). */
  maxLegs?: number;
}

const DEFAULTS = { minTransferMinutes: 3, windowMinutes: 240, maxLegs: 3 };

/** Segmentos viajables de una expedicion: de cada parada a cada parada posterior. */
function ridesFromStop(trip: Trip, stopId: StopId): RideLeg[] {
  const i = trip.stops.findIndex((s) => s.stopId === stopId);
  if (i === -1) return [];
  const board = trip.stops[i]!;
  const out: RideLeg[] = [];
  for (let j = i + 1; j < trip.stops.length; j++) {
    const alight = trip.stops[j]!;
    out.push({
      kind: "ride",
      lineId: trip.lineId,
      from: stopId,
      to: alight.stopId,
      depart: board.time,
      arrive: alight.time,
    });
  }
  return out;
}

/**
 * Busca itinerarios de `origin` a cualquiera de `destinations`.
 *
 * El grafo es diminuto (tres o cuatro paradas), asi que explora en
 * profundidad todas las combinaciones dentro de la ventana y luego se queda
 * con las no dominadas: un itinerario sobra si otro sale igual o mas tarde y
 * ademas llega igual o antes.
 */
export function plan(options: PlanOptions): Itinerary[] {
  const { schedule, date, origin, destinations, earliestBoarding } = options;
  const minTransfer = options.minTransferMinutes ?? DEFAULTS.minTransferMinutes;
  const window = options.windowMinutes ?? DEFAULTS.windowMinutes;
  const maxLegs = options.maxLegs ?? DEFAULTS.maxLegs;

  const targets = new Set(destinations);
  const trips = tripsForDate(schedule, date);
  const horizon = earliestBoarding + window;
  const found: Itinerary[] = [];

  const visit = (stopId: StopId, time: Minutes, legs: Leg[]) => {
    if (legs.length > 0 && targets.has(stopId)) {
      const ajustados = tighten(legs);
      found.push({
        legs: ajustados,
        depart: ajustados[0]!.depart,
        arrive: time,
        destination: stopId,
      });
      // Llegar al destino cierra el itinerario: no seguimos encadenando tramos.
      return;
    }
    if (legs.length >= maxLegs) return;

    const last = legs[legs.length - 1];
    const readyToBoard = last?.kind === "ride" ? time + minTransfer : time;

    for (const trip of trips) {
      for (const ride of ridesFromStop(trip, stopId)) {
        if (ride.depart < readyToBoard || ride.depart > horizon) continue;
        // Volver a la parada de la que acabamos de salir nunca ayuda.
        if (legs.some((l) => l.from === ride.to)) continue;
        legs.push(ride);
        visit(ride.to, ride.arrive, legs);
        legs.pop();
      }
    }

    // Dos tramos andando seguidos no tienen sentido.
    if (last?.kind === "walk") return;
    for (const link of schedule.walkLinks) {
      if (link.from !== stopId) continue;
      if (legs.some((l) => l.from === link.to)) continue;
      const walk: WalkLeg = {
        kind: "walk",
        from: link.from,
        to: link.to,
        depart: time,
        arrive: time + link.minutes,
      };
      legs.push(walk);
      visit(link.to, walk.arrive, legs);
      legs.pop();
    }
  };

  visit(origin, earliestBoarding, []);
  return paretoFilter(found);
}

/**
 * Retrasa los tramos a pie todo lo posible sin perder el enlace.
 *
 * La busqueda supone que andas nada mas empezar, pero si luego esperas
 * veinte minutos en la parada, lo que quieres saber es a que hora salir de
 * verdad. Sin esto, ademas, todos los itinerarios que empiezan andando salen
 * a la misma hora y el filtro de Pareto se queda solo con uno.
 *
 * El ultimo tramo, si es a pie, se deja como esta: ahi si interesa llegar
 * cuanto antes.
 */
function tighten(legs: readonly Leg[]): Leg[] {
  const out: Leg[] = legs.map((l) => ({ ...l }));
  let limite: number | undefined;
  for (let i = out.length - 1; i >= 0; i--) {
    const leg = out[i]!;
    if (leg.kind === "walk" && limite !== undefined) {
      const duracion = leg.arrive - leg.depart;
      leg.arrive = limite;
      leg.depart = limite - duracion;
    }
    limite = leg.depart;
  }
  return out;
}

/**
 * Quita los itinerarios que no aportan nada: si otro sale igual o mas tarde
 * (menos espera) y llega igual o antes, este sobra. A igualdad de horas se
 * prefiere el que tiene menos tramos.
 */
export function paretoFilter(itineraries: readonly Itinerary[]): Itinerary[] {
  const sorted = [...itineraries].sort(
    (a, b) => a.arrive - b.arrive || b.depart - a.depart || a.legs.length - b.legs.length,
  );
  const kept: Itinerary[] = [];
  for (const cand of sorted) {
    const dominated = kept.some(
      (k) =>
        k.depart >= cand.depart &&
        k.arrive <= cand.arrive &&
        k.legs.length <= cand.legs.length,
    );
    if (!dominated) kept.push(cand);
  }
  return kept.sort((a, b) => a.depart - b.depart || a.arrive - b.arrive);
}
