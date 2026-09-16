# Buses UCA

App para consultar de un vistazo los buses entre casa (Telegrafía Sin Hilos, Cádiz)
y el campus de Puerto Real (ESI y CASEM).

> **Estado: esqueleto funcional con datos de ejemplo.**
> Los horarios que muestra ahora mismo están **inventados**. Falta descargar los
> reales de la API del consorcio — ver [Datos](#datos) más abajo.

## Por qué está hecho así

**Web app (PWA), no app nativa.** Se abre en el móvil, se añade a la pantalla de
inicio y queda como un icono más. Nada de tiendas ni de reinstalar el APK cada vez
que cambia un horario.

**Los horarios van dentro de la app, no se consultan en vivo.** Un script los
descarga del consorcio y los deja en `src/data/schedule.json`, que se empaqueta con
la app. Así carga al instante, **funciona sin cobertura** (que es justo lo que pasa
en una parada) y no depende de que la web del consorcio esté en pie.

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
| `src/model/calendar.ts` | Qué horario toca hoy: periodo (lectivo/verano) × tipo de día. |
| `src/planner/plan.ts` | Busca itinerarios: directo, con transbordo y andando. |
| `src/planner/plan.test.ts` | Tests del planificador. |
| `src/config.ts` | Paradas propias y minutos andando hasta cada una. |
| `src/main.ts` | Interfaz. |
| `scripts/explore-ctan.ts` | Sondea la API de CTAN para ver la forma real de los datos. |
| `scripts/make-sample-data.py` | Genera los datos de ejemplo de mientras. |

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

### Pendiente

- [ ] Confirmar los endpoints reales de la API y que los datos están al día.
- [ ] Escribir el normalizador API → `schedule.json` y sustituir los datos de ejemplo.
- [ ] Averiguar si las **lanzaderas ESI↔CASEM** están en el consorcio o son un
      servicio interno de la UCA. Si son internas, hay que meterlas a mano.
- [ ] Comprobar que los periodos lectivo/verano de la API cuadran con los reales.
- [ ] Workflow semanal que vuelva a descargar los horarios y abra un PR si cambian.

## Aviso

Los horarios son los **oficiales publicados**, orientativos. No es posición en
tiempo real del autobús.
