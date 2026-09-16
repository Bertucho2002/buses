# Buses UCA

App para consultar de un vistazo los buses entre casa (Telegrafía Sin Hilos, Cádiz)
y el campus de Puerto Real (ESI y CASEM).

> **Estado: funcionando con los horarios reales del consorcio.**
> Quedan flecos, sobre todo los festivos locales y el cambio de horario en
> verano — ver [Pendiente](#pendiente).

## Por qué está hecho así

**Web app (PWA), no app nativa.** Se abre en el móvil, se añade a la pantalla de
inicio y queda como un icono más. Nada de tiendas ni de reinstalar el APK cada vez
que cambia un horario.

**Los horarios van dentro de la app, no se consultan en vivo.** Un script los
descarga del consorcio y los deja en `src/data/schedule.json`, que se empaqueta con
la app. Así carga al instante, **funciona sin cobertura** (que es justo lo que pasa
en una parada) y no depende de que la web del consorcio esté en pie.

Tiene dos pantallas. **Próximos** planifica el viaje y responde a "¿cómo llego
a clase?". **Horarios** enseña la tabla completa del día, una fila por salida,
para cuando lo que quieres es planificar en vez de salir corriendo. Las dos
comparten un selector de día, así que se puede consultar cualquier fecha y no
solo hoy.

**No es un "próximos buses de A a B".** El destino es una *zona* con dos paradas,
la ESI y el CASEM, separadas por 18 minutos andando. Como a la ESI llegan menos
buses, sobre todo por la tarde, muchas veces sale mejor bajarse en el CASEM y
seguir andando o coger la lanzadera. La app calcula las tres opciones y las ordena
por **hora de llegada**, que es lo que de verdad importa.

## Cómo se usa

```bash
npm install
npm run dev      # servidor de desarrollo
npm test         # tests del planificador
npm run build    # build estático en dist/
```

Se despliega solo en GitHub Pages al hacer push a `main`.

## Cómo está organizado

| Ruta | Qué hace |
| --- | --- |
| `src/model/types.ts` | Formato canónico interno. Todo se normaliza a esto. |
| `src/model/calendar.ts` | Qué expediciones circulan hoy, resolviendo las frecuencias de CTAN. |
| `src/planner/plan.ts` | Busca itinerarios: directo, con transbordo y andando. |
| `src/planner/plan.test.ts` | Tests del planificador. |
| `src/config.ts` | Paradas propias y minutos andando hasta cada una. |
| `src/main.ts` | Interfaz: las dos pantallas y el selector de día. |
| `src/ui/dates.ts` | Manejo de fechas del selector de día. |
| `scripts/descargar-ctan.py` | Reconocimiento de la API de CTAN. Se ejecuta a mano y vuelca todo en `ctan-dump/`. |
| `scripts/explore-ctan.ts` | Lo mismo, en TypeScript, para cuando haya acceso desde la sesión. |
| `scripts/generar-horario.py` | Descarga la API y genera `src/data/schedule.json`. |
| `scripts/descargar-ctan-3.py` | Vuelca los horarios por línea, con periodos de vigencia. |
| `scripts/make-sample-data.py` | Genera datos de ejemplo, por si hace falta desarrollar sin red. |
| `NOTAS-API.md` | Cómo funciona la API de CTAN y dónde están sus trampas. |

### El planificador

El grafo es diminuto: tres paradas y un enlace a pie. Explora en profundidad todas
las combinaciones dentro de una ventana de tiempo (máximo 3 tramos) y se queda con
las **no dominadas**: un itinerario sobra si otro sale igual o más tarde *y* llega
igual o antes. El resultado es una lista corta sin opciones que no aportan nada.

Sale más barato que un algoritmo de verdad y cabe en la cabeza.

## Datos

La fuente prevista es **`api.ctan.es`**, la API de datos abiertos de la Red de
Consorcios de Transporte de Andalucía ([catálogo en datos.gob.es][datos]). Publica
líneas, paradas, recorridos y horarios ya estructurados en calendarios, que es
exactamente lo que necesitamos. `siu.cmtbc.es` queda como contraste para verificar
que los horarios coinciden con los que se publican de cara al público.

[datos]: https://datos.gob.es/es/catalogo/a01002820-datos-de-la-red-de-consorcios-de-transporte-de-andalucia.xml

### Cómo se regeneran

```bash
python3 scripts/generar-horario.py                      # desde la API
python3 scripts/generar-horario.py --desde-volcado ctan-dump2   # sin red
```

Los horarios salen de `horarios_origen_destino` entre el núcleo de Cádiz (`1`)
y el del Campus Universitario (`41`). Ese endpoint devuelve la tabla completa
en los dos sentidos, con una columna por bloque de paso: **Telegrafía-Estadio**,
**C. Educación/Facultad Ciencias** y **Escuela Ingeniería** entre ellas. Los
detalles están en `NOTAS-API.md`.

### Lo que dicen los datos reales

De 84 salidas Cádiz → Campus, **las 84 paran en el CASEM y solo 17 llegan a la
ESI**. En sentido contrario, 86 y 18. Entre las 15:23 y las 20:10 no hay ni un
solo bus directo a la ESI, y entre las 15:50 y las 21:50 no sale ninguno de
ella. De ahí que la app tenga sentido.

Además, varias líneas hacen el salto CASEM → ESI en unos 5 minutos, así que
muchas veces sale mejor enlazar que andar los 18.

### Pendiente

- [ ] **Festivos.** Ahora solo están los de fecha fija. Faltan la Semana Santa
      y los locales de Cádiz y Puerto Real. Se añaden a mano en el campo
      `holidays` de `schedule.json` (o mejor, en el script que lo genera).
- [ ] **La línea M-035** (Cádiz - Escuela de Ingeniería), que arranca a mitad
      de septiembre y va directa a la ESI. No sale en `horarios_origen_destino`
      porque ese endpoint solo devuelve lo vigente el día que se consulta. Hay
      que sacarla de `horarios_lineas?linea=220`. Mientras tanto la app avisa
      en pantalla de que le faltan buses.
- [ ] **Periodos de vigencia.** `horarios_origen_destino` no dice a qué
      planificador pertenece cada horario, así que la app no distingue el
      horario de curso del de verano. Para arreglarlo hay que cruzar con
      `horarios_lineas?linea=...`, que sí devuelve `planificadores` con fecha
      de inicio y fin.
- [ ] **Contrastar con la web del consorcio** (`siu.cmtbc.es`) que los horarios
      coinciden con los que publican de cara al público.
- [ ] **Lanzaderas de la UCA.** Entre las 70 líneas del consorcio no hay
      ninguna que se llame lanzadera. Si existen como servicio interno de la
      universidad, hay que meter sus horarios a mano.
- [ ] Workflow que regenere los horarios cada cierto tiempo y abra un PR si
      cambian.

## Aviso

Los horarios son los **oficiales publicados**, orientativos. No es posición en
tiempo real del autobús.
