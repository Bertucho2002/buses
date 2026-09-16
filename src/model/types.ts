/**
 * Modelo de datos de la app.
 *
 * Formato canonico interno: lo que viene de la API de CTAN se normaliza a
 * estas estructuras en src/data/schedule.json. La app no conoce otro formato.
 *
 * Las paradas se corresponden con los "bloques" de la API, que es como
 * agrupa las columnas de sus tablas de horarios. Coinciden con los nombres
 * que usa la web del consorcio de cara al público.
 */

/** Minutos desde medianoche. 8:30 -> 510. Puede pasar de 1440 si cruza la noche. */
export type Minutes = number;

export type StopId = string;
export type LineId = string;

export interface Stop {
  id: StopId;
  /** Nombre corto para la interfaz. */
  name: string;
  /** Nombre del bloque tal y como lo publica el consorcio. */
  officialName: string;
}

export interface Line {
  id: LineId;
  /** Codigo publico, p. ej. "M-030". */
  code: string;
  name: string;
  /** Identificador de la linea en la API de CTAN. */
  ctanId?: string;
}

/**
 * Acronimo de frecuencia de CTAN. Dice que dias circula una expedicion.
 *
 *   L-V    lunes a viernes laborables
 *   L-J    lunes a jueves laborables
 *   L-S    lunes a sabados laborables
 *   L-D    diario, festivos incluidos
 *   V      viernes laborables
 *   S      sabados laborables
 *   D      domingos y festivos
 *   D*     domingos y festivos de apertura comercial
 *   S-D-F  sabados, domingos y festivos
 *   -      dia suelto (sin fecha asociada: no se puede resolver)
 *
 * "Laborable" aqui significa que no es festivo. Un L-V no circula si el
 * martes cae festivo.
 */
export type FrequencyCode = string;

/**
 * Periodo de vigencia de un horario, lo que la API llama "planificador".
 * Fechas en ISO (YYYY-MM-DD), ambas inclusive.
 */
export interface Period {
  id: string;
  name: string;
  from: string;
  to: string;
}

export interface TripStop {
  stopId: StopId;
  time: Minutes;
}

/** Una expedicion: un autobus concreto, las paradas por las que pasa y cuando. */
export interface Trip {
  lineId: LineId;
  /** Que dias circula. */
  days: FrequencyCode;
  /** Periodo al que pertenece, si se conoce. */
  periodId?: string;
  /** Texto del consorcio ("SERVICIO ADAPTADO A PMR", etc.). */
  notes?: string;
  /** Paradas en orden de recorrido. Solo las que sirve de verdad. */
  stops: TripStop[];
}

/** Enlace a pie entre dos paradas. Hay que declarar los dos sentidos. */
export interface WalkLink {
  from: StopId;
  to: StopId;
  minutes: number;
}

export interface Schedule {
  generatedAt: string;
  source: string;
  /** true mientras sean datos inventados. La interfaz avisa en pantalla. */
  isSample: boolean;
  /**
   * Salvedades conocidas de estos datos, para enseñarlas en la interfaz en
   * vez de callarlas. Por ejemplo, que faltan los festivos locales.
   */
  warnings: string[];
  stops: Stop[];
  lines: Line[];
  /** Puede venir vacio si la fuente no da informacion de periodos. */
  periods: Period[];
  trips: Trip[];
  walkLinks: WalkLink[];
  /** Festivos en ISO (YYYY-MM-DD). */
  holidays: string[];
}
