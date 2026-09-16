import { test } from "node:test";
import assert from "node:assert/strict";
import { plan, paretoFilter, type Itinerary } from "./plan.ts";
import { calendarFor, dayTypeFor, formatTime } from "../model/calendar.ts";
import type { Schedule } from "../model/types.ts";

/** Horario minimo y controlado, para que las pruebas no dependan de los datos reales. */
function makeSchedule(): Schedule {
  return {
    generatedAt: "2026-09-16T00:00:00Z",
    source: "test",
    isSample: true,
    stops: [
      { id: "casa", name: "Casa", officialName: "Telegrafía Sin Hilos" },
      { id: "esi", name: "ESI", officialName: "Escuela Ingeniería" },
      { id: "casem", name: "CASEM", officialName: "C. Educación/Facultad Ciencias" },
    ],
    lines: [
      { id: "bus", code: "B", name: "Bus", kind: "bus" },
      { id: "lanz", code: "L", name: "Lanzadera", kind: "lanzadera" },
    ],
    periods: [{ id: "lectivo", name: "Lectivo", from: "2026-09-01", to: "2027-06-30" }],
    calendars: [
      { id: "cal", periodId: "lectivo", dayType: "laborable" },
      { id: "cal-sab", periodId: "lectivo", dayType: "sabado" },
    ],
    trips: [
      // Directo a la ESI, tarde.
      { lineId: "bus", calendarId: "cal", stops: [
        { stopId: "casa", time: 600 }, { stopId: "casem", time: 625 }, { stopId: "esi", time: 632 } ] },
      // Solo hasta el CASEM, pero sale antes.
      { lineId: "bus", calendarId: "cal", stops: [
        { stopId: "casa", time: 540 }, { stopId: "casem", time: 565 } ] },
      // Lanzadera que enlaza con el anterior.
      { lineId: "lanz", calendarId: "cal", stops: [
        { stopId: "casem", time: 575 }, { stopId: "esi", time: 581 } ] },
    ],
    walkLinks: [
      { from: "esi", to: "casem", minutes: 18 },
      { from: "casem", to: "esi", minutes: 18 },
    ],
    holidays: ["2026-12-25"],
  };
}

test("encuentra el bus directo a la ESI", () => {
  const s = makeSchedule();
  const r = plan({ schedule: s, calendarId: "cal", origin: "casa", destinations: ["esi"], earliestBoarding: 595 });
  assert.equal(r.length, 1);
  assert.equal(r[0]!.legs.length, 1);
  assert.equal(r[0]!.arrive, 632);
});

test("prefiere el enlace con lanzadera cuando llega antes que el directo", () => {
  const s = makeSchedule();
  const r = plan({ schedule: s, calendarId: "cal", origin: "casa", destinations: ["esi"], earliestBoarding: 480 });
  // El de las 9:00 + lanzadera llega a las 9:41; el directo de las 10:00 llega a las 10:32.
  const best = r.reduce((a, b) => (a.arrive <= b.arrive ? a : b));
  assert.equal(best.arrive, 581);
  assert.equal(best.legs.length, 2);
  assert.equal(best.legs[1]!.kind, "ride");
});

test("ofrece llegar al CASEM y seguir andando", () => {
  const s = makeSchedule();
  s.trips = s.trips.filter((t) => t.lineId !== "lanz"); // sin lanzadera
  const r = plan({ schedule: s, calendarId: "cal", origin: "casa", destinations: ["esi"], earliestBoarding: 480 });
  const andando = r.find((i) => i.legs.some((l) => l.kind === "walk"));
  assert.ok(andando, "deberia proponer andar desde el CASEM");
  assert.equal(andando!.arrive, 565 + 18);
});

test("respeta el margen minimo de transbordo", () => {
  const s = makeSchedule();
  // La lanzadera sale 10 min despues de llegar el bus; con 15 de margen ya no enlaza.
  const r = plan({ schedule: s, calendarId: "cal", origin: "casa", destinations: ["esi"],
                   earliestBoarding: 480, minTransferMinutes: 15 });
  assert.ok(!r.some((i) => i.legs.length === 2 && i.legs[1]!.kind === "ride"));
});

test("no devuelve nada si no sale ningun bus en la ventana", () => {
  const s = makeSchedule();
  const r = plan({ schedule: s, calendarId: "cal", origin: "casa", destinations: ["esi"],
                   earliestBoarding: 700, windowMinutes: 60 });
  assert.deepEqual(r, []);
});

test("la vuelta desde la ESI puede empezar andando al CASEM", () => {
  const s = makeSchedule();
  s.trips = [
    { lineId: "bus", calendarId: "cal", stops: [{ stopId: "casem", time: 1000 }, { stopId: "casa", time: 1025 }] },
  ];
  const r = plan({ schedule: s, calendarId: "cal", origin: "esi", destinations: ["casa"], earliestBoarding: 960 });
  assert.equal(r.length, 1);
  assert.equal(r[0]!.legs[0]!.kind, "walk");
  assert.equal(r[0]!.arrive, 1025);
});

test("paretoFilter descarta lo que sale antes y llega despues", () => {
  const peor: Itinerary = { legs: [], depart: 500, arrive: 600, destination: "esi" };
  const mejor: Itinerary = { legs: [], depart: 520, arrive: 590, destination: "esi" };
  assert.deepEqual(paretoFilter([peor, mejor]), [mejor]);
});

test("los festivos cuentan como domingo", () => {
  const s = makeSchedule();
  // 2026-12-25 es viernes, pero esta declarado festivo.
  assert.equal(dayTypeFor(new Date(2026, 11, 25), s.holidays), "domingo-festivo");
  assert.equal(dayTypeFor(new Date(2026, 11, 24), s.holidays), "laborable");
});

test("una fecha fuera de todo periodo no devuelve horario", () => {
  const s = makeSchedule();
  assert.equal(calendarFor(new Date(2030, 0, 15), s), undefined);
  assert.equal(calendarFor(new Date(2026, 8, 16), s)?.id, "cal");
});

test("formatTime", () => {
  assert.equal(formatTime(632), "10:32");
  assert.equal(formatTime(0), "00:00");
});
