# Notas sobre la API de CTAN

Lo aprendido leyendo el primer volcado (`ctan-dump/`). Sirve para no tener que
volver a deducirlo.

## Lo básico

- Base: `https://api.ctan.es/v1`
- Consorcio Bahía de Cádiz: **`2`**
- Documentación completa: `/doc/api_data.json` (60 endpoints, generada con
  apidocjs). Es el fichero más útil de todos: trae parámetros y **ejemplos de
  respuesta** de cada endpoint.
- No hay autenticación ni API key.

Ojo: en la documentación los parámetros se llaman `idLinea`, `idFrecuencia`,
`idNucleoOrigen`..., pero **en la URL real van sin el prefijo `id`**:
`linea`, `frecuencia`, `dia`, `mes`, `origen`, `destino`, `lang`.
Se ve en las URLs de ejemplo de la propia documentación.

## Nuestras paradas

| id | Nombre en la API | Núcleo | Zona |
| --- | --- | --- | --- |
| `7` | Telegrafía Sin Hilos | 1 (Cádiz) | A |
| `79` | Campus-C. Educación | 41 (Campus Universitario) | F |
| `81` | Campus-Ciencias | 41 | F |
| `262` | Escuela Ingeniería | 41 | F |
| `264` | Escuela Ingeniería (Interior) | 41 | F |

Núcleos útiles: Cádiz `1`, Campus Universitario `41`, Puerto Real `6`.

Lo que llamamos "la parada del CASEM" son en realidad **dos paradas
distintas** en la API: `79` (C. Educación) y `81` (Ciencias). Hay que decidir
si se tratan como una sola o por separado.

## Dónde están los horarios

No están bajo `/lineas/:id/horarios` — eso da 404. Los endpoints buenos son:

```
/Consorcios/2/horarios_lineas?linea=6&frecuencia=&dia=&mes=&lang=ES
/Consorcios/2/horarios_origen_destino?origen=1&destino=41&lang=ES
/Consorcios/2/horarios_corredor?corredor=4&lang=ES
```

### Forma de la respuesta de `horarios_lineas`

```jsonc
{
  "planificadores": [
    { "fechaInicio": "2013-09-16", "fechaFin": "2016-09-16", "muestraFechaFin": "0" }
  ],
  "bloquesIda": [
    { "nombre": "Estación de Jaén", "color": "#00c222", "tipo": "0" },
    { "nombre": "Frecuencia",       "color": "#ffffff", "tipo": "1" },
    { "nombre": "Observaciones",    "color": "#ffffff", "tipo": "2" }
  ],
  "horarioIda": [
    { "horas": ["14:00", "14:05", "14:15"], "frecuencia": "L-V", "observaciones": "OBS 1" }
  ],
  "bloquesVuelta": [ /* ... */ ],
  "horarioVuelta": [ /* ... */ ],
  "frecuencias": [ { "idfrecuencia": "1", "acronimo": "L-V", "nombre": "Lunes a Viernes" } ]
}
```

Tres cosas importantes:

1. **`planificadores` son los periodos de vigencia.** Cada uno trae
   `fechaInicio` y `fechaFin`, que es justo lo que el modelo llama `Period`.
   Aquí es donde se verá el cambio entre curso y verano.

2. **La tabla es por bloques, no por paradas.** Las columnas (`bloquesIda`)
   son agrupaciones con nombre, y `horas[]` va alineado con ellas. `tipo` dice
   qué es cada columna: `0` un bloque de paso, `1` la frecuencia, `2` las
   observaciones. Un `"--"` en `horas` significa que esa salida no pasa por
   ahí.

   **Esto es el riesgo principal del proyecto:** si un bloque es "Campus
   Universitario" en vez de "Escuela Ingeniería" y "C. Educación" por
   separado, la API no distingue las dos paradas y toda la lógica de
   ESI vs CASEM se queda sin datos. Hay que comprobarlo con
   `/corredores/:idLinea/bloques`.

3. **`frecuencia` viene como acrónimo** (`"L-V"`, `"L-S"`, `"Sab"`), no como
   id. Se cruza con la lista `frecuencias` de la propia respuesta.

### Frecuencias del consorcio (`/Consorcios/2/frecuencias`)

Son bastante más finas que el `laborable / sábado / domingo-festivo` que
tiene ahora `src/model/types.ts`, así que **el modelo hay que cambiarlo**:

| id | código | nombre |
| --- | --- | --- |
| 1 | L-V | Lunes a viernes laborables |
| 2 | S-D-F | Sábados, domingos y festivos |
| 3 | L-S | Lunes a sábados laborables |
| 4 | D | Domingos y festivos |
| 5 | S | Sábados laborables |
| 6 | - | Día suelto |
| 7 | L-D | Diario, incluido festivos |
| 8 | L-J | Lunes a jueves laborables |
| 9 | L-V | Lunes a viernes |
| 10 | V | Viernes laborables |
| 11 | D* | Dom. y fest. abiertos comercio |
| 12 | L | (lunes) |

Varias frecuencias pueden aplicar al mismo día (un martes lectivo encaja en
L-V, L-S, L-D y L-J a la vez), así que el horario de un día es la **unión** de
todas las salidas cuya frecuencia case con esa fecha.

### La tabla va DENTRO del planificador

El detalle que más tiempo costó: en `horarios_lineas` el horario **no está en
el nivel de arriba** de la respuesta. Ahí solo hay `planificadores`,
`frecuencias`, `horaCorte` y `observacionesModoTransporte`. Las tablas
(`bloquesIda`, `horarioIda`, `bloquesVuelta`, `horarioVuelta`) van **dentro de
cada elemento de `planificadores`**, junto con su `idPlani` y sus fechas.

### `dia` y `mes` filtran también por día de la semana

No seleccionan solo el periodo vigente: devuelven **los servicios que circulan
esa fecha concreta**. Preguntar por un lunes da los de lunes. Para reconstruir
la semana entera hay que sondear un día de cada tipo (un laborable, un
viernes, un sábado y un domingo), porque si no se pierden las frecuencias que
solo aplican a algunos días.

Una línea que aún no ha arrancado devuelve `planificadores: []`.

## Trampas encontradas

- **`/paradas/:id/servicios` no lista las líneas de la parada**, lista los
  **próximos servicios** del momento en que preguntas. En el primer volcado,
  hecho sobre las 22:05, las paradas de la ESI daban 0 servicios y parecía que
  no tenían línea ninguna. Para saber qué líneas paran en un sitio hay que usar
  `/lineasPorParadas/:idParadas`.
- `/v1/Consorcios` (la lista de consorcios) da **404**. El endpoint real es
  `/Consorcios/:idConsorcio/consorcios`, que necesita ya un id.
- `/lineas/:id` devuelve sobre todo la **polilínea** para pintar el mapa, que
  puede ser de cientos de puntos. No hace falta para nada de lo nuestro.

## Líneas candidatas

Pasan por Telegrafía y por el campus (confirmado en el primer volcado):

| id | código | nombre |
| --- | --- | --- |
| 6 | M-030 | Cádiz-Río San Pedro-Campus Universitario-Puerto Real-Hospital |
| 9 | M-031 | Cádiz-Río San Pedro-Campus Universitario-Puerto Real |

Mencionan el campus en el nombre y están sin comprobar:

`240` M-037 (Cádiz-Campus por CA-35), `14` M-041, `18` M-052, `20` M-061,
`163` M-960, `225` M-967.

### Periodos reales encontrados

| Línea | Periodo |
| --- | --- |
| M-035, M-037, M-038 | desde `2026-09-21`, sin fecha de fin |
| M-031, M-032, M-960, M-967 | desde `2026-09-01` |
| M-030 | desde `2025-01-07` |
| M-031 (verano) | `2026-08-01` → `2026-08-31` |
| M-960 (verano) | `2026-07-01` → `2026-08-31` |

O sea que los periodos existen y son por línea, no globales del consorcio.

**No hay ninguna línea con "lanzadera" en el nombre** entre las 70 del
consorcio. Es un indicio de que las lanzaderas ESI↔CASEM son un servicio
interno de la UCA y no están en la API, pero no es concluyente: podrían
llamarse de otra forma.
