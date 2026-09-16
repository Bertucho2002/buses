import type { StopId } from "./model/types.ts";

/** Parada de casa. */
export const CASA: StopId = "telegrafia";
export const ESI: StopId = "esi";
export const CASEM: StopId = "casem";

/**
 * Minutos andando desde el portal / la facultad hasta cada parada.
 * Sirve para decir "sal ya" en vez de solo la hora del autobus.
 */
export const ACCESO: Record<StopId, number> = {
  telegrafia: 1,
  esi: 1,
  casem: 2,
};

export const MARGEN_TRANSBORDO = 4;
