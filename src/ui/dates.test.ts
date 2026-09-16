import { test } from "node:test";
import assert from "node:assert/strict";
import { addDays, describeDay, fromInputValue, inputValue, sameDay, startOfDay } from "./dates.ts";

const MARTES = new Date(2026, 8, 22, 16, 30);

test("startOfDay quita la hora sin cambiar de día", () => {
  const d = startOfDay(MARTES);
  assert.equal(d.getHours(), 0);
  assert.equal(inputValue(d), "2026-09-22");
});

test("addDays cruza bien el fin de mes", () => {
  assert.equal(inputValue(addDays(new Date(2026, 8, 30), 1)), "2026-10-01");
  assert.equal(inputValue(addDays(new Date(2026, 0, 1), -1)), "2025-12-31");
  // Y el cambio de hora de octubre, que es donde suelen aparecer los sustos.
  assert.equal(inputValue(addDays(new Date(2026, 9, 24), 1)), "2026-10-25");
  assert.equal(inputValue(addDays(new Date(2026, 9, 25), 1)), "2026-10-26");
});

test("fromInputValue no desplaza el día por el huso horario", () => {
  const d = fromInputValue("2026-09-22");
  assert.ok(d);
  assert.equal(inputValue(d), "2026-09-22");
  assert.ok(sameDay(d, MARTES));
  assert.equal(fromInputValue("no es fecha"), undefined);
  assert.equal(fromInputValue(""), undefined);
});

test("describeDay usa palabras para los días cercanos", () => {
  const hoy = startOfDay(MARTES);
  assert.equal(describeDay(hoy, hoy), "hoy");
  assert.equal(describeDay(addDays(hoy, 1), hoy), "mañana");
  assert.equal(describeDay(addDays(hoy, -1), hoy), "ayer");
  assert.match(describeDay(addDays(hoy, 5), hoy), /domingo/);
});
