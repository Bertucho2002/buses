import "./styles.css";
import rawSchedule from "./data/schedule.json";
import type { Schedule, StopId } from "./model/types.ts";
import {
  formatTime,
  isoDate,
  minutesOfDay,
  outOfCoverage,
  tripsForDate,
  unknownFrequencies,
} from "./model/calendar.ts";
import { plan, type Itinerary } from "./planner/plan.ts";
import { ACCESO, CASA, CASEM, ESI, MARGEN_TRANSBORDO } from "./config.ts";
import { describeLeg, relativeTo, summarize } from "./ui/format.ts";

const schedule = rawSchedule as Schedule;

// Si la API trae frecuencias que no sabemos interpretar, esas expediciones se
// descartan. Mejor decirlo que esconder buses en silencio.
const frecuenciasRaras = unknownFrequencies(schedule);

type Sentido = "ida" | "vuelta";
/** A donde vas (ida) o de donde sales (vuelta). "cualquiera" acepta las dos paradas del campus. */
type Campus = "esi" | "casem" | "cualquiera";

const state = {
  sentido: "ida" as Sentido,
  campus: "esi" as Campus,
};

const camposDe = (c: Campus): StopId[] =>
  c === "cualquiera" ? [ESI, CASEM] : c === "esi" ? [ESI] : [CASEM];

function calcular(now: Date): { itinerarios: Itinerary[]; sinDatos: boolean; sinServicio: boolean } {
  if (outOfCoverage(schedule, now)) {
    return { itinerarios: [], sinDatos: true, sinServicio: false };
  }

  const ahora = minutesOfDay(now);
  const campus = camposDe(state.campus);
  const sinServicio = tripsForDate(schedule, now).length === 0;

  if (state.sentido === "ida") {
    return {
      sinDatos: false,
      sinServicio,
      itinerarios: plan({
        schedule,
        date: now,
        origin: CASA,
        destinations: campus,
        earliestBoarding: ahora + (ACCESO[CASA] ?? 0),
        minTransferMinutes: MARGEN_TRANSBORDO,
      }),
    };
  }

  // Vuelta: puede salir de la ESI o del CASEM, asi que se planifica desde
  // cada una y se juntan los resultados.
  const todos = campus.flatMap((origin) =>
    plan({
      schedule,
      date: now,
      origin,
      destinations: [CASA],
      earliestBoarding: ahora + (ACCESO[origin] ?? 0),
      minTransferMinutes: MARGEN_TRANSBORDO,
    }),
  );
  todos.sort((a, b) => a.depart - b.depart || a.arrive - b.arrive);
  return { itinerarios: todos, sinDatos: false, sinServicio };
}

function optionCard(it: Itinerary, ahora: number, esElProximo: boolean): string {
  const salidaDe = it.legs[0]!.from;
  const acceso = ACCESO[salidaDe] ?? 0;
  const salirA = it.depart - acceso;
  const desde = state.sentido === "ida" ? "de casa" : `de ${salidaDe === ESI ? "la ESI" : "el CASEM"}`;

  return `
    <article class="option${esElProximo ? " next" : ""}">
      <div class="option-head">
        <span class="depart">${formatTime(it.depart)}</span>
        <span class="countdown">${relativeTo(ahora, it.depart)}</span>
        <span class="tag">${summarize(schedule, it)}</span>
      </div>
      <div class="arrive">Llegas a las ${formatTime(it.arrive)} · ${it.arrive - it.depart} min de viaje</div>
      ${esElProximo && acceso > 0 ? `<div class="leave-home">Sal ${desde} a las ${formatTime(salirA)}</div>` : ""}
      ${it.legs.length > 1
        ? `<details class="legs"><summary>Ver el trayecto</summary><ul>${it.legs
            .map((l) => `<li>${describeLeg(schedule, l)}</li>`)
            .join("")}</ul></details>`
        : ""}
    </article>`;
}

function render(): void {
  const now = new Date();
  const ahora = minutesOfDay(now);
  const { itinerarios, sinDatos, sinServicio } = calcular(now);

  const dia = now.toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" });
  const etiquetaCampus = state.sentido === "ida" ? "¿A dónde vas?" : "¿De dónde sales?";

  const app = document.getElementById("app")!;
  app.innerHTML = `
    <h1>Buses UCA <span class="when">· ${dia}</span></h1>

    <div class="segmented">
      <button data-sentido="ida" aria-pressed="${state.sentido === "ida"}">A la uni</button>
      <button data-sentido="vuelta" aria-pressed="${state.sentido === "vuelta"}">A casa</button>
    </div>

    <div class="chips" aria-label="${etiquetaCampus}">
      <button data-campus="esi" aria-pressed="${state.campus === "esi"}">ESI</button>
      <button data-campus="casem" aria-pressed="${state.campus === "casem"}">CASEM</button>
      <button data-campus="cualquiera" aria-pressed="${state.campus === "cualquiera"}">Me da igual</button>
    </div>

    ${schedule.isSample
      ? `<div class="banner"><strong>Datos de ejemplo.</strong> Estos horarios están inventados para poder desarrollar la app. Todavía no son los del consorcio.</div>`
      : ""}

    ${frecuenciasRaras.length > 0
      ? `<div class="banner">No se muestran las salidas con frecuencia ${frecuenciasRaras.map((f) => `<code>${f}</code>`).join(", ")}, que no sabemos a qué días corresponden.</div>`
      : ""}

    ${sinServicio
      ? `<div class="banner"><strong>Hoy no circula ninguna línea</strong> según los horarios descargados. Si eso no cuadra, los datos pueden estar desfasados.</div>`
      : ""}

    ${sinDatos
      ? `<div class="banner"><strong>Sin horario para hoy (${isoDate(now)}).</strong> Los datos no cubren esta fecha: hay que volver a descargarlos del consorcio.</div>`
      : ""}

    ${itinerarios.length === 0 && !sinDatos
      ? `<p class="empty">No quedan salidas hoy.</p>`
      : itinerarios.map((it, i) => optionCard(it, ahora, i === 0)).join("")}

    <footer>
      ${schedule.warnings.map((w) => `<p>${w}</p>`).join("")}
      <p>Datos del ${new Date(schedule.generatedAt).toLocaleDateString("es-ES")}.</p>
    </footer>
  `;

  for (const b of app.querySelectorAll<HTMLButtonElement>("[data-sentido]")) {
    b.onclick = () => {
      state.sentido = b.dataset.sentido as Sentido;
      render();
    };
  }
  for (const b of app.querySelectorAll<HTMLButtonElement>("[data-campus]")) {
    b.onclick = () => {
      state.campus = b.dataset.campus as Campus;
      render();
    };
  }
}

render();
// Los "en X min" se quedan viejos enseguida si el movil se queda abierto.
setInterval(render, 30_000);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) render();
});

// Service worker: hace que la app funcione sin cobertura.
if ("serviceWorker" in navigator && location.protocol !== "file:") {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`).catch(() => {
      // Sin service worker la app sigue funcionando, solo que sin offline.
    });
  });
}
