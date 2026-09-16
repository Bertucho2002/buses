import "./styles.css";
import rawSchedule from "./data/schedule.json";
import type { Schedule, StopId, Trip } from "./model/types.ts";
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
import {
  addDays,
  describeDay,
  fromInputValue,
  inputValue,
  longDay,
  sameDay,
  startOfDay,
} from "./ui/dates.ts";

const schedule = rawSchedule as Schedule;

// Si la API trae frecuencias que no sabemos interpretar, esas expediciones se
// descartan. Mejor decirlo que esconder buses en silencio.
const frecuenciasRaras = unknownFrequencies(schedule);

type Vista = "proximos" | "horarios";
type Sentido = "ida" | "vuelta";
/** A donde vas (ida) o de donde sales (vuelta). */
type Campus = "esi" | "casem" | "cualquiera";

const state = {
  vista: "proximos" as Vista,
  /** Dia que se esta consultando. Arranca en hoy. */
  fecha: startOfDay(new Date()),
  sentido: "ida" as Sentido,
  campus: "esi" as Campus,
  /** Filtro de linea en la vista de horarios. "" = todas. */
  linea: "",
  /**
   * Por defecto la tabla solo enseña las paradas que nos importan. En un
   * movil no caben las diez del corredor, y las tres primeras son justo las
   * que dan igual, asi que sin esto lo util queda fuera de pantalla.
   */
  todasParadas: false,
};

const camposDe = (c: Campus): StopId[] =>
  c === "cualquiera" ? [ESI, CASEM] : c === "esi" ? [ESI] : [CASEM];

const esHoy = () => sameDay(state.fecha, new Date());

/** Desde que minuto buscar: la hora actual si es hoy, o el principio del dia. */
function desdeMinuto(): number {
  return esHoy() ? minutesOfDay(new Date()) : 0;
}

// ---------------------------------------------------------------- planificador

function calcular(): { itinerarios: Itinerary[]; sinDatos: boolean; sinServicio: boolean } {
  const fecha = state.fecha;
  if (outOfCoverage(schedule, fecha)) {
    return { itinerarios: [], sinDatos: true, sinServicio: false };
  }

  const desde = desdeMinuto();
  const campus = camposDe(state.campus);
  const sinServicio = tripsForDate(schedule, fecha).length === 0;
  // Mirando otro dia interesa el dia entero, no las proximas cuatro horas.
  const windowMinutes = esHoy() ? 240 : 1440;

  const comun = { schedule, date: fecha, minTransferMinutes: MARGEN_TRANSBORDO, windowMinutes };

  if (state.sentido === "ida") {
    return {
      sinDatos: false,
      sinServicio,
      itinerarios: plan({
        ...comun,
        origin: CASA,
        destinations: campus,
        earliestBoarding: desde + (ACCESO[CASA] ?? 0),
      }),
    };
  }

  // Vuelta: puede salir de la ESI o del CASEM, asi que se planifica desde
  // cada una y se juntan los resultados.
  const todos = campus.flatMap((origin) =>
    plan({ ...comun, origin, destinations: [CASA], earliestBoarding: desde + (ACCESO[origin] ?? 0) }),
  );
  todos.sort((a, b) => a.depart - b.depart || a.arrive - b.arrive);
  return { itinerarios: todos, sinDatos: false, sinServicio };
}

function optionCard(it: Itinerary, ahora: number, esElProximo: boolean): string {
  const salidaDe = it.legs[0]!.from;
  const acceso = ACCESO[salidaDe] ?? 0;
  const desde = state.sentido === "ida" ? "de casa" : `de ${salidaDe === ESI ? "la ESI" : "el CASEM"}`;

  return `
    <article class="option${esElProximo ? " next" : ""}">
      <div class="option-head">
        <span class="depart">${formatTime(it.depart)}</span>
        ${esHoy() ? `<span class="countdown">${relativeTo(ahora, it.depart)}</span>` : ""}
        <span class="tag">${summarize(schedule, it)}</span>
      </div>
      <div class="arrive">Llegas a las ${formatTime(it.arrive)} · ${it.arrive - it.depart} min de viaje</div>
      ${esElProximo && acceso > 0
        ? `<div class="leave-home">Sal ${desde} a las ${formatTime(it.depart - acceso)}</div>`
        : ""}
      ${it.legs.length > 1
        ? `<details class="legs"><summary>Ver el trayecto</summary><ul>${it.legs
            .map((l) => `<li>${describeLeg(schedule, l)}</li>`)
            .join("")}</ul></details>`
        : ""}
    </article>`;
}

function vistaProximos(): string {
  const { itinerarios, sinDatos, sinServicio } = calcular();
  const ahora = minutesOfDay(new Date());

  return `
    <div class="chips" aria-label="${state.sentido === "ida" ? "¿A dónde vas?" : "¿De dónde sales?"}">
      <button data-campus="esi" aria-pressed="${state.campus === "esi"}">ESI</button>
      <button data-campus="casem" aria-pressed="${state.campus === "casem"}">CASEM</button>
      <button data-campus="cualquiera" aria-pressed="${state.campus === "cualquiera"}">Me da igual</button>
    </div>

    ${sinDatos
      ? `<div class="banner"><strong>Sin horario para el ${isoDate(state.fecha)}.</strong> Los datos no cubren esa fecha: hay que volver a descargarlos del consorcio.</div>`
      : ""}

    ${sinServicio
      ? `<div class="banner"><strong>Ese día no circula ninguna línea</strong> según los horarios descargados. Si eso no cuadra, los datos pueden estar desfasados.</div>`
      : ""}

    ${itinerarios.length === 0 && !sinDatos && !sinServicio
      ? `<p class="empty">${esHoy() ? "No quedan salidas hoy." : "Ninguna salida ese día."}</p>`
      : itinerarios.map((it, i) => optionCard(it, ahora, i === 0 && esHoy())).join("")}
  `;
}

// -------------------------------------------------------------------- horarios

/** Expediciones de un sentido en la fecha elegida, ordenadas por salida. */
function expediciones(corridorId: string): Trip[] {
  return tripsForDate(schedule, state.fecha)
    .filter((t) => t.corridorId === corridorId)
    .filter((t) => state.linea === "" || t.lineId === state.linea)
    .sort((a, b) => (a.stops[0]?.time ?? 0) - (b.stops[0]?.time ?? 0));
}

function vistaHorarios(): string {
  const corridorId = state.sentido;
  const corridor = schedule.corridors.find((c) => c.id === corridorId);
  if (!corridor) return `<p class="empty">No hay datos de ese sentido.</p>`;

  const viajes = expediciones(corridorId);
  // Solo se ofrecen como filtro las lineas que de verdad circulan ese dia.
  const lineasDelDia = [
    ...new Set(
      tripsForDate(schedule, state.fecha)
        .filter((t) => t.corridorId === corridorId)
        .map((t) => t.lineId),
    ),
  ]
    .map((id) => schedule.lines.find((l) => l.id === id)!)
    .filter(Boolean)
    .sort((a, b) => a.code.localeCompare(b.code));

  const nombre = (id: StopId) => schedule.stops.find((s) => s.id === id)?.name ?? id;
  const esClave = (id: StopId) => id === CASA || id === ESI || id === CASEM;
  const columnas = state.todasParadas ? corridor.stops : corridor.stops.filter(esClave);

  const filas = viajes
    .map((t) => {
      const porParada = new Map(t.stops.map((p) => [p.stopId, p.time]));
      const celdas = columnas
        .map((id) => {
          const hora = porParada.get(id);
          const clave = esClave(id) ? " clave" : "";
          return hora === undefined
            ? `<td class="vacia${clave}">·</td>`
            : `<td class="${clave.trim()}">${formatTime(hora)}</td>`;
        })
        .join("");
      const linea = schedule.lines.find((l) => l.id === t.lineId);
      return `<tr><th scope="row">${linea?.code ?? t.lineId}</th>${celdas}<td class="freq">${t.days}</td></tr>`;
    })
    .join("");

  return `
    <div class="chips" aria-label="Filtrar por línea">
      <button data-linea="" aria-pressed="${state.linea === ""}">Todas</button>
      ${lineasDelDia
        .map(
          (l) =>
            `<button data-linea="${l.id}" aria-pressed="${state.linea === l.id}">${l.code}</button>`,
        )
        .join("")}
    </div>

    <div class="chips">
      <button data-paradas aria-pressed="${state.todasParadas}">
        ${state.todasParadas ? "Solo mis paradas" : "Ver todas las paradas"}
      </button>
    </div>

    ${viajes.length === 0
      ? `<p class="empty">Ninguna salida ese día.</p>`
      : `<p class="count">${viajes.length} salidas · ${corridor.name}</p>
         <div class="tablewrap">
           <table class="horario">
             <thead><tr><th scope="col">Línea</th>${columnas
               .map((id) => `<th scope="col"${esClave(id) ? ' class="clave"' : ""}>${nombre(id)}</th>`)
               .join("")}<th scope="col">Días</th></tr></thead>
             <tbody>${filas}</tbody>
           </table>
         </div>
         <p class="leyenda">Un punto significa que esa salida no para ahí. La última columna es la frecuencia: <code>L-V</code> lunes a viernes laborables, <code>S</code> sábados, <code>D</code> domingos y festivos, <code>L-S</code> lunes a sábados, <code>L-D</code> diario.</p>`}
  `;
}

// ----------------------------------------------------------------------- marco

function render(): void {
  const hoy = startOfDay(new Date());
  const etiquetaDia = describeDay(state.fecha, hoy);
  const sentidoIda = state.vista === "proximos" ? "A la uni" : "Cádiz → Campus";
  const sentidoVuelta = state.vista === "proximos" ? "A casa" : "Campus → Cádiz";

  const app = document.getElementById("app")!;
  app.innerHTML = `
    <header>
      <h1>Buses UCA</h1>
      <nav class="tabs">
        <button data-vista="proximos" aria-pressed="${state.vista === "proximos"}">Próximos</button>
        <button data-vista="horarios" aria-pressed="${state.vista === "horarios"}">Horarios</button>
      </nav>
    </header>

    <div class="datebar">
      <button data-dia="-1" aria-label="Día anterior">‹</button>
      <label class="datefield">
        <input type="date" value="${inputValue(state.fecha)}" aria-label="Fecha" />
        <span>${longDay(state.fecha)}</span>
      </label>
      <button data-dia="1" aria-label="Día siguiente">›</button>
    </div>
    <p class="daynote">
      ${etiquetaDia === longDay(state.fecha) ? "" : `<strong>${etiquetaDia}</strong>`}
      ${!sameDay(state.fecha, hoy) ? `<button class="link" data-hoy>volver a hoy</button>` : ""}
    </p>

    <div class="segmented">
      <button data-sentido="ida" aria-pressed="${state.sentido === "ida"}">${sentidoIda}</button>
      <button data-sentido="vuelta" aria-pressed="${state.sentido === "vuelta"}">${sentidoVuelta}</button>
    </div>

    ${schedule.isSample
      ? `<div class="banner"><strong>Datos de ejemplo.</strong> Estos horarios están inventados para poder desarrollar la app. Todavía no son los del consorcio.</div>`
      : ""}

    ${frecuenciasRaras.length > 0
      ? `<div class="banner">No se muestran las salidas con frecuencia ${frecuenciasRaras
          .map((f) => `<code>${f}</code>`)
          .join(", ")}, que no sabemos a qué días corresponden.</div>`
      : ""}

    ${state.vista === "proximos" ? vistaProximos() : vistaHorarios()}

    <footer>
      ${schedule.warnings.map((w) => `<p>${w}</p>`).join("")}
      <p>Datos del ${new Date(schedule.generatedAt).toLocaleDateString("es-ES")}.</p>
    </footer>
  `;

  const on = <T extends HTMLElement>(sel: string, fn: (el: T) => void) => {
    for (const el of app.querySelectorAll<T>(sel)) fn(el);
  };

  on<HTMLButtonElement>("[data-vista]", (b) => {
    b.onclick = () => {
      state.vista = b.dataset.vista as Vista;
      render();
    };
  });
  on<HTMLButtonElement>("[data-sentido]", (b) => {
    b.onclick = () => {
      state.sentido = b.dataset.sentido as Sentido;
      render();
    };
  });
  on<HTMLButtonElement>("[data-campus]", (b) => {
    b.onclick = () => {
      state.campus = b.dataset.campus as Campus;
      render();
    };
  });
  on<HTMLButtonElement>("[data-linea]", (b) => {
    b.onclick = () => {
      state.linea = b.dataset.linea ?? "";
      render();
    };
  });
  on<HTMLButtonElement>("[data-paradas]", (b) => {
    b.onclick = () => {
      state.todasParadas = !state.todasParadas;
      render();
    };
  });
  on<HTMLButtonElement>("[data-dia]", (b) => {
    b.onclick = () => {
      state.fecha = addDays(state.fecha, Number(b.dataset.dia));
      render();
    };
  });
  on<HTMLButtonElement>("[data-hoy]", (b) => {
    b.onclick = () => {
      state.fecha = startOfDay(new Date());
      render();
    };
  });
  on<HTMLInputElement>('input[type="date"]', (input) => {
    input.onchange = () => {
      const d = fromInputValue(input.value);
      if (d) {
        state.fecha = d;
        render();
      }
    };
  });
}

render();
// Los "en X min" se quedan viejos enseguida si el movil se queda abierto.
setInterval(() => {
  if (state.vista === "proximos" && esHoy()) render();
}, 30_000);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) render();
});
