/**
 * Modelo de datos de la app.
 *
 * Este es el formato canonico interno: todo lo que venga de la API de CTAN
 * (o de donde sea) se normaliza a estas estructuras antes de guardarse en
 * src/data/schedule.json. La app no conoce ningun otro formato.
 */

/** Minutos desde medianoche. 8:30 -> 510. Puede pasar de 1440 si un viaje cruza la noche. */
export type Minutes = number;

export type StopId = string;
export type LineId = string;
export type CalendarId = string;
export type PeriodId = string;

/** Tipo de dia al que corresponde un horario. */
export type DayType = "laborable" | "sabado" | "domingo-festivo";

export interface Stop {
  id: StopId;
  /** Nombre corto para la interfaz. */
  name: string;
  /** Nombre tal y como lo publica el consorcio, para poder contrastar. */
  officialName: string;
  /** Identificador en la API de CTAN, cuando lo conocemos. */
  ctanId?: string;
}

export type LineKind = "bus" | "lanzadera";

export interface Line {
  id: LineId;
  /** Codigo publico de la linea, p. ej. "M-050". */
  code: string;
  name: string;
  kind: LineKind;
  operator?: string;
  ctanId?: string;
}

/**
 * Periodo de vigencia de un horario. El consorcio publica horarios distintos
 * en periodo lectivo y en verano, asi que un horario solo vale dentro de sus
 * fechas. Fechas en ISO (YYYY-MM-DD), ambas inclusive.
 */
export interface Period {
  id: PeriodId;
  name: string;
  from: string;
  to: string;
}

/** Un horario concreto = un periodo + un tipo de dia. */
export interface Calendar {
  id: CalendarId;
  periodId: PeriodId;
  dayType: DayType;
}

/** Paso de un viaje por una parada. */
export interface TripStop {
  stopId: StopId;
  time: Minutes;
}

/** Una expedicion concreta: un autobus que sale a una hora y para donde para. */
export interface Trip {
  lineId: LineId;
  calendarId: CalendarId;
  /** Paradas en orden de recorrido, con hora de paso. */
  stops: TripStop[];
}

/** Enlace a pie entre dos paradas. Se asume simetrico salvo que se declare al reves. */
export interface WalkLink {
  from: StopId;
  to: StopId;
  minutes: number;
}

export interface Schedule {
  /** Cuando se genero este fichero. */
  generatedAt: string;
  /** De donde salieron los datos. */
  source: string;
  /**
   * true mientras sean datos de ejemplo inventados para poder desarrollar.
   * La interfaz avisa en pantalla cuando esto esta puesto.
   */
  isSample: boolean;
  stops: Stop[];
  lines: Line[];
  periods: Period[];
  calendars: Calendar[];
  trips: Trip[];
  walkLinks: WalkLink[];
  /** Festivos en ISO (YYYY-MM-DD). Se tratan como domingo. */
  holidays: string[];
}
