import { test } from "node:test";
import assert from "node:assert/strict";
import { plan, paretoFilter, type Itinerary } from "./plan.ts";
import {
  formatTime,
  frequencyMatches,
  outOfCoverage,
  parseTime,
  tripsForDate,
} from "../model/calendar.ts";
import type { Schedule } from "../model/types.ts";

/** Martes, miércoles, sábado y domingo de una misma semana de 2026. */
const MARTES = new Date(2026, 8, 22);
const SABADO = new Date(2026, 8, 26);
const DOMINGO = new Date(2026, 8, 27);
/** Lunes 12 de octubre de 2026: festivo. */
const FESTIVO = new Date(2026, 9, 12);

/** Horario mínimo y controlado, para no depender de los datos reales. */
function makeSchedule(): Schedule {
  return {
    generatedAt: "2026-09-16T00:00:00Z",
    source: "test",
    isSample: true,
    warnings: [],
    missingLines: [],
    stops: [
      { id: "casa", name: "Casa", officialName: "Telegrafía-Estadio" },
      { id: "esi", name: "ESI", officialName: "Escuela Ingeniería" },
      { id: "casem", name: "CASEM", officialName: "C. Educación/Facultad Ciencias" },
    ],
    lines: [
      { id: "m030", code: "M-030", name: "M-030" },
      { id: "m967", code: "M-967", name: "M-967" },
    ],
    corridors: [
      { id: "ida", name: "Cádiz → Campus", stops: ["casa", "casem", "esi"] },
    ],
    periods: [],
    trips: [
      // Directo a la ESI, pero sale tarde.
      { lineId: "m030", days: "L-V", corridorId: "ida", stops: [
        { stopId: "casa", time: 600 }, { stopId: "casem", time: 625 }, { stopId: "esi", time: 632 } ] },
      // Solo hasta el CASEM, sale antes.
      { lineId: "m030", days: "L-V", corridorId: "ida", stops: [
        { stopId: "casa", time: 540 }, { stopId: "casem", time: 565 } ] },
      // Salto CASEM -> ESI que enlaza con el anterior.
      { lineId: "m967", days: "L-V", corridorId: "ida", stops: [
        { stopId: "casem", time: 575 }, { stopId: "esi", time: 581 } ] },
      // Un sábado cualquiera, para comprobar el filtrado por frecuencia.
      { lineId: "m030", days: "S", corridorId: "ida", stops: [
        { stopId: "casa", time: 600 }, { stopId: "casem", time: 625 } ] },
    ],
    walkLinks: [
      { from: "esi", to: "casem", minutes: 18 },
      { from: "casem", to: "esi", minutes: 18 },
    ],
    holidays: ["2026-10-12"],
  };
}

test("encuentra el bus directo a la ESI", () => {
  const r = plan({ schedule: makeSchedule(), date: MARTES, origin: "casa",
                   destinations: ["esi"], earliestBoarding: 595 });
  assert.equal(r.length, 1);
  assert.equal(r[0]!.legs.length, 1);
  assert.equal(r[0]!.arrive, 632);
});

test("prefiere el enlace CASEM-ESI cuando llega antes que el directo", () => {
  const r = plan({ schedule: makeSchedule(), date: MARTES, origin: "casa",
                   destinations: ["esi"], earliestBoarding: 480 });
  // 9:00 + salto a las 9:35 llega a las 9:41; el directo de las 10:00 llega a las 10:32.
  const best = r.reduce((a, b) => (a.arrive <= b.arrive ? a : b));
  assert.equal(best.arrive, 581);
  assert.equal(best.legs.length, 2);
  assert.equal(best.legs[1]!.kind, "ride");
});

test("ofrece llegar al CASEM y seguir andando", () => {
  const s = makeSchedule();
  s.trips = s.trips.filter((t) => t.lineId !== "m967"); // sin el salto en bus
  const r = plan({ schedule: s, date: MARTES, origin: "casa",
                   destinations: ["esi"], earliestBoarding: 480 });
  const andando = r.find((i) => i.legs.some((l) => l.kind === "walk"));
  assert.ok(andando, "debería proponer andar desde el CASEM");
  assert.equal(andando!.arrive, 565 + 18);
});

test("respeta el margen mínimo de transbordo", () => {
  // El salto sale 10 min después de llegar el bus; con 15 de margen no enlaza.
  const r = plan({ schedule: makeSchedule(), date: MARTES, origin: "casa",
                   destinations: ["esi"], earliestBoarding: 480, minTransferMinutes: 15 });
  assert.ok(!r.some((i) => i.legs.length === 2 && i.legs[1]!.kind === "ride"));
});

test("no devuelve nada si no sale nada en la ventana", () => {
  const r = plan({ schedule: makeSchedule(), date: MARTES, origin: "casa",
                   destinations: ["esi"], earliestBoarding: 700, windowMinutes: 60 });
  assert.deepEqual(r, []);
});

test("la vuelta desde la ESI puede empezar andando al CASEM", () => {
  const s = makeSchedule();
  s.trips = [
    { lineId: "m030", days: "L-V", corridorId: "ida", stops: [
      { stopId: "casem", time: 1000 }, { stopId: "casa", time: 1025 } ] },
  ];
  const r = plan({ schedule: s, date: MARTES, origin: "esi",
                   destinations: ["casa"], earliestBoarding: 960 });
  assert.equal(r.length, 1);
  assert.equal(r[0]!.legs[0]!.kind, "walk");
  assert.equal(r[0]!.arrive, 1025);
});

test("un sábado no salen los buses de L-V", () => {
  const s = makeSchedule();
  const sabado = tripsForDate(s, SABADO);
  assert.equal(sabado.length, 1);
  assert.equal(sabado[0]!.days, "S");
  assert.equal(tripsForDate(s, MARTES).length, 3);
});

test("un festivo entre semana no es laborable", () => {
  const s = makeSchedule();
  // El 12 de octubre de 2026 cae en lunes, pero es festivo: no hay L-V ni S.
  assert.deepEqual(tripsForDate(s, FESTIVO), []);
});

test("las frecuencias de CTAN se resuelven bien", () => {
  const h = ["2026-10-12"];
  assert.equal(frequencyMatches("L-V", MARTES, h), true);
  assert.equal(frequencyMatches("L-V", SABADO, h), false);
  assert.equal(frequencyMatches("L-S", SABADO, h), true);
  assert.equal(frequencyMatches("S", SABADO, h), true);
  assert.equal(frequencyMatches("D", DOMINGO, h), true);
  assert.equal(frequencyMatches("D", SABADO, h), false);
  assert.equal(frequencyMatches("S-D-F", SABADO, h), true);
  assert.equal(frequencyMatches("S-D-F", DOMINGO, h), true);
  assert.equal(frequencyMatches("S-D-F", MARTES, h), false);
  assert.equal(frequencyMatches("L-D", DOMINGO, h), true);
  assert.equal(frequencyMatches("L-J", new Date(2026, 8, 25), h), false); // viernes
  assert.equal(frequencyMatches("V", new Date(2026, 8, 25), h), true);
  // Un festivo entre semana: cae el L-V, entran los de festivo.
  assert.equal(frequencyMatches("L-V", FESTIVO, h), false);
  assert.equal(frequencyMatches("D", FESTIVO, h), true);
  assert.equal(frequencyMatches("S-D-F", FESTIVO, h), true);
  // "Día suelto" no se puede resolver: no se enseña.
  assert.equal(frequencyMatches("-", MARTES, h), false);
});

test("fuera de cobertura solo cuando todas las expediciones tienen periodo", () => {
  const s = makeSchedule();
  assert.equal(outOfCoverage(s, new Date(2030, 0, 1)), false);

  // Con un periodo declarado pero expediciones sin periodo, el horario sigue
  // valiendo: es el caso de mezclar una fuente que trae periodos con otra que
  // no, y darlo por caducado dejaría la app en blanco.
  s.periods = [{ id: "p", name: "Curso", from: "2026-09-01", to: "2027-06-30" }];
  assert.equal(outOfCoverage(s, new Date(2030, 0, 1)), false);

  // En cuanto todas lo tienen, sí se puede afirmar.
  for (const t of s.trips) t.periodId = "p";
  assert.equal(outOfCoverage(s, new Date(2030, 0, 1)), true);
  assert.equal(outOfCoverage(s, MARTES), false);
});

test("paretoFilter descarta lo que sale antes y llega después", () => {
  const peor: Itinerary = { legs: [], depart: 500, arrive: 600, destination: "esi" };
  const mejor: Itinerary = { legs: [], depart: 520, arrive: 590, destination: "esi" };
  assert.deepEqual(paretoFilter([peor, mejor]), [mejor]);
});

test("parseTime y formatTime", () => {
  assert.equal(parseTime("08:23"), 503);
  assert.equal(parseTime("--"), undefined);
  assert.equal(parseTime(""), undefined);
  assert.equal(formatTime(632), "10:32");
});

test("los tramos a pie se retrasan hasta justo antes del enlace", () => {
  const s = makeSchedule();
  s.trips = [
    { lineId: "m030", days: "L-V", corridorId: "ida", stops: [
      { stopId: "casem", time: 1000 }, { stopId: "casa", time: 1025 } ] },
    { lineId: "m030", days: "L-V", corridorId: "ida", stops: [
      { stopId: "casem", time: 1060 }, { stopId: "casa", time: 1085 } ] },
  ];
  const r = plan({ schedule: s, date: MARTES, origin: "esi",
                   destinations: ["casa"], earliestBoarding: 900 });
  // Dos opciones distintas, no una: andar a las 982 para el bus de las 1000,
  // o andar a las 1042 para el de las 1060.
  assert.equal(r.length, 2);
  assert.deepEqual(r.map((i) => i.depart), [1000 - 18, 1060 - 18]);
  assert.deepEqual(r.map((i) => i.arrive), [1025, 1085]);
  // El tramo a pie sigue durando lo mismo.
  for (const it of r) {
    const w = it.legs[0]!;
    assert.equal(w.kind, "walk");
    assert.equal(w.arrive - w.depart, 18);
  }
});

test("un tramo a pie final no se retrasa: interesa llegar cuanto antes", () => {
  const s = makeSchedule();
  s.trips = [
    { lineId: "m030", days: "L-V", corridorId: "ida", stops: [
      { stopId: "casa", time: 540 }, { stopId: "casem", time: 565 } ] },
  ];
  const r = plan({ schedule: s, date: MARTES, origin: "casa",
                   destinations: ["esi"], earliestBoarding: 480 });
  assert.equal(r.length, 1);
  assert.equal(r[0]!.arrive, 565 + 18);
});

test("un día entero se resuelve rápido y da una lista útil", () => {
  const s = makeSchedule();
  // 120 expediciones repartidas por todo el día, como el horario real.
  s.trips = [];
  for (let t = 6 * 60; t < 23 * 60; t += 20) {
    s.trips.push({ lineId: "m030", days: "L-V", corridorId: "ida", stops: [
      { stopId: "casa", time: t }, { stopId: "casem", time: t + 25 } ] });
    if (t % 60 === 0) {
      s.trips.push({ lineId: "m967", days: "L-V", corridorId: "ida", stops: [
        { stopId: "casem", time: t + 30 }, { stopId: "esi", time: t + 35 } ] });
    }
  }
  const t0 = Date.now();
  const r = plan({ schedule: s, date: MARTES, origin: "casa", destinations: ["esi"],
                   earliestBoarding: 0, windowMinutes: 1440 });
  const ms = Date.now() - t0;
  assert.ok(r.length > 10, `deberia haber muchas opciones, hay ${r.length}`);
  assert.ok(ms < 1000, `ha tardado ${ms} ms`);
  // Siguen saliendo ordenadas y sin dominadas.
  for (let i = 1; i < r.length; i++) {
    assert.ok(r[i]!.depart >= r[i - 1]!.depart);
    assert.ok(r[i]!.arrive > r[i - 1]!.arrive);
  }
});

test("una línea con periodo no circula antes de su fecha de arranque", () => {
  const s = makeSchedule();
  s.periods = [{ id: "nuevo", name: "Desde el 21", from: "2026-09-21", to: "9999-12-31" }];
  s.trips = [
    // La de siempre, sin periodo: circula cualquier laborable.
    { lineId: "m030", days: "L-V", corridorId: "vuelta", stops: [
      { stopId: "esi", time: 900 }, { stopId: "casa", time: 940 } ] },
    // La nueva, que no existe hasta el 21.
    { lineId: "m967", days: "L-J", corridorId: "vuelta", periodId: "nuevo", stops: [
      { stopId: "esi", time: 1210 }, { stopId: "casa", time: 1225 } ] },
  ];
  const codigos = (d: Date) => tripsForDate(s, d).map((t) => t.lineId).sort();
  // Viernes 18 de septiembre: aún no ha arrancado.
  assert.deepEqual(codigos(new Date(2026, 8, 18)), ["m030"]);
  // Lunes 21: ya circula.
  assert.deepEqual(codigos(new Date(2026, 8, 21)), ["m030", "m967"]);
  // Viernes 25: la nueva es L-J, así que ese día no sale.
  assert.deepEqual(codigos(new Date(2026, 8, 25)), ["m030"]);
});
