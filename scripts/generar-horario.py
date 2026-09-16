#!/usr/bin/env python3
"""
Genera src/data/schedule.json a partir de la API de CTAN.

Descarga los horarios entre el núcleo de Cádiz y el del Campus Universitario
de Puerto Real y los normaliza al formato que usa la app.

Uso:
    python3 scripts/generar-horario.py              # descarga de la API
    python3 scripts/generar-horario.py --desde-volcado ctan-dump2

La segunda forma no toca la red: reutiliza un volcado ya descargado, que es
como se desarrolla cuando no hay acceso a api.ctan.es.

Solo necesita Python 3.8 o superior.
"""

from __future__ import annotations

import argparse
import glob
import datetime
import gzip
import io
import json
import re
import ssl
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://api.ctan.es/v1"
CONSORCIO = "2"
NUCLEO_CASA = "1"       # Cádiz
NUCLEO_CAMPUS = "41"    # Campus Universitario (Puerto Real)

SALIDA = Path("src/data/schedule.json")

# Los bloques de la API con el id que usa la app. Lo que no esté aquí se
# queda con un id derivado del nombre.
IDS = {
    "Telegrafía-Estadio": "telegrafia",
    "C. Educación/Facultad Ciencias": "casem",
    "Escuela Ingeniería": "esi",
}
NOMBRES_CORTOS = {
    "rio-s-pedro": "Río S. Pedro",
    "telegrafia": "Telegrafía",
    "casem": "CASEM",
    "esi": "ESI",
    "plaza-de-sevilla-estacion-de-cadiz": "Estación",
    "pz-asdrubal-s-sever": "Asdrúbal",
    "hospital-segunda-ag": "Hospital",
    "avda-las-cortes": "Las Cortes",
    "pz-espana": "Pz. España",
}

# El corredor que nos interesa, en orden de recorrido hacia el campus. Varias
# líneas vienen de Jerez, Rota o Chipiona y pasan por aquí de camino; su
# recorrido completo no nos sirve de nada, así que se recorta a este tramo.
CORREDOR = [
    "Pz. España",
    "Plaza de Sevilla-Estación de Cádiz",
    "Pz.Asdrúbal-S.Sever.",
    "Avda. Las Cortes",
    "Hospital-Segunda Ag.",
    "Telegrafía-Estadio",
    "F. Ciencias Empresariales",
    "Avda. de Huelva",
    "Río S. Pedro",
    "C. Educación/Facultad Ciencias",
    "Escuela Ingeniería",
]

# Minutos andando entre las dos paradas del campus.
ANDANDO_ESI_CASEM = 18

# Líneas que sabemos que existen y que deberían salir en el horario. Si alguna
# falta, el horario se genera igual pero avisando: es mejor decir que faltan
# buses que dejar que la app parezca completa cuando no lo está.
#
# horarios_origen_destino solo devuelve lo vigente el día que se consulta, así
# que una línea que arranca más adelante no aparece hasta que empieza.
LINEAS_ESPERADAS = {
    "M-035": "Cádiz-Escuela de Ingeniería, arranca a mitad de septiembre",
}

# Salvedades que no se pueden deducir de los datos y hay que escribir a mano.
# Se quitan cuando dejen de ser ciertas.
AVISOS_EXTRA = [
    "Las líneas M-037 y M-038 cambian el 21 de septiembre de 2026 y los "
    "horarios que hay aquí son los anteriores. Conviene regenerarlos a partir "
    "de esa fecha.",
]

# horarios_lineas devuelve el identificador interno de CTAN, no el código
# público, así que hace falta la correspondencia.
LINEAS_POR_CTAN = {
    "220": "M-035", "6": "M-030", "9": "M-031", "10": "M-032", "11": "M-033",
    "12": "M-034", "239": "M-036", "240": "M-037", "267": "M-038", "14": "M-041",
    "18": "M-052", "20": "M-061", "38": "M-904", "163": "M-960", "225": "M-967",
}

# Festivos de fecha fija en Andalucía. Los de fecha variable (Semana Santa) y
# los locales de Cádiz y Puerto Real NO están: hay que añadirlos a mano en
# src/data/festivos.json. La app avisa de esto en pantalla.
def festivos_fijos(anios: list[int]) -> list[str]:
    fijos = [(1, 1), (1, 6), (2, 28), (5, 1), (8, 15), (10, 12), (11, 1), (12, 6), (12, 8), (12, 25)]
    return [f"{a:04d}-{m:02d}-{d:02d}" for a in anios for m, d in fijos]


def cruzar_medianoche(paradas: list) -> list:
    """Arregla las expediciones que pasan de las doce.

    El último bus sale a las 23:43 y llega a las 00:06, y la API devuelve
    "00:06" a secas, que son 6 minutos. Tal cual, la expedición parece llegar
    antes de salir. Se resuelve sumando un día a partir de cada salto hacia
    atrás, que es lo mismo que hace la propia API con su horaCorte de las 4:00.
    """
    salida = []
    desfase = 0
    anterior = None
    for p in paradas:
        t = p["time"] + desfase
        if anterior is not None and t < anterior:
            desfase += 24 * 60
            t += 24 * 60
        salida.append({**p, "time": t})
        anterior = t
    return salida


def slug(nombre: str) -> str:
    s = unicodedata.normalize("NFD", nombre)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def parse_hora(s: str) -> int | None:
    m = re.match(r"^(\d{1,2}):(\d{2})$", (s or "").strip())
    if not m:
        return None
    h, mm = int(m.group(1)), int(m.group(2))
    return h * 60 + mm if mm < 60 else None


def descargar(origen: str, destino: str) -> dict:
    url = f"{BASE}/Consorcios/{CONSORCIO}/horarios_origen_destino?" + urllib.parse.urlencode(
        {"origen": origen, "destino": destino, "lang": "ES"}
    )
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "Accept-Encoding": "gzip",
                      "User-Agent": "buses-uca/0.1 (proyecto personal de estudiante)"}
    )
    with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as res:
        raw = res.read()
        if res.headers.get("Content-Encoding") == "gzip":
            raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return json.loads(raw)


def desde_volcado(carpeta: Path, origen: str, destino: str) -> dict:
    f = carpeta / f"Consorcios_{CONSORCIO}_horarios_origen_destino_origen_{origen}_destino_{destino}_lang_ES.json"
    if not f.exists():
        raise SystemExit(f"No encuentro {f}. ¿Es la carpeta del volcado correcta?")
    return json.loads(f.read_text(encoding="utf-8"))


def normalizar_lineas(carpeta: Path, stops: dict, lines: dict, trips: list,
                      periods: dict, solo: set | None = None) -> int:
    """Lee las respuestas de horarios_lineas de un volcado.

    A diferencia de horarios_origen_destino, aquí el horario va dentro de cada
    "planificador", que es el periodo de vigencia. Eso permite saber desde qué
    fecha circula cada expedición, y es lo que hace falta para una línea que
    arranca a mitad de curso.

    Las respuestas de varias fechas se solapan a propósito (dia/mes filtra
    también por día de la semana), así que hay que quitar duplicados.
    """
    vistas: set = set()
    añadidas = 0
    for fichero in sorted(glob.glob(str(carpeta / "*horarios_lineas*"))):
        m = re.search(r"linea_(\d+)_", fichero)
        if not m:
            continue
        ctan_id = m.group(1)
        if solo is not None and LINEAS_POR_CTAN.get(ctan_id) not in solo:
            continue
        try:
            data = json.loads(Path(fichero).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for pl in (data.get("planificadores") or []):
            periodo_id = f"plan-{pl.get('idPlani')}"
            if periodo_id not in periods:
                periods[periodo_id] = {
                    "id": periodo_id,
                    "name": f"Desde el {pl.get('fechaInicio')}",
                    "from": pl.get("fechaInicio") or "0000-01-01",
                    # Un planificador sin fecha de fin sigue vigente.
                    "to": pl.get("fechaFin") or "9999-12-31",
                }
            for sentido, corredor in (("Ida", "ida"), ("Vuelta", "vuelta")):
                bloques = pl.get(f"bloques{sentido}") or []
                # tipo "0" son paradas; "1" es la frecuencia y "2" las observaciones.
                columnas = [b.get("nombre") for b in bloques if str(b.get("tipo")) == "0"]
                ids = [IDS.get(c, slug(c)) for c in columnas]
                for idp, nombre in zip(ids, columnas):
                    stops.setdefault(idp, {"id": idp, "name": NOMBRES_CORTOS.get(idp, nombre),
                                           "officialName": nombre})
                for fila in (pl.get(f"horario{sentido}") or []):
                    horas = fila.get("horas", [])
                    if len(horas) != len(ids):
                        continue  # fila que no cuadra con la cabecera: se descarta
                    paradas = [{"stopId": i, "time": parse_hora(h)}
                               for i, h in zip(ids, horas) if parse_hora(h) is not None]
                    if len(paradas) < 2:
                        continue
                    paradas = cruzar_medianoche(paradas)
                    dias = (fila.get("frecuencia") or fila.get("dias") or "").strip()
                    firma = (ctan_id, periodo_id, corredor, dias,
                             tuple((p["stopId"], p["time"]) for p in paradas))
                    if firma in vistas:
                        continue
                    vistas.add(firma)
                    codigo = LINEAS_POR_CTAN.get(ctan_id, f"linea-{ctan_id}")
                    idl = slug(codigo)
                    lines.setdefault(idl, {"id": idl, "code": codigo, "name": codigo,
                                           "ctanId": ctan_id})
                    viaje = {"lineId": idl, "days": dias, "corridorId": corredor,
                             "periodId": periodo_id, "stops": paradas}
                    obs = (fila.get("observaciones") or "").strip()
                    if obs:
                        viaje["notes"] = obs
                    trips.append(viaje)
                    añadidas += 1
    return añadidas


def normalizar(tabla: dict, stops: dict, lines: dict, trips: list,
               corredor_id: str, corredor_nombre: str, corredores: list) -> int:
    """Convierte una tabla de horarios (ida o vuelta) en expediciones."""
    bloques = [b["nombre"] for b in tabla.get("bloques", [])]
    # La primera columna es "Lineas" y las dos últimas Frecuencia y
    # Observaciones; las de en medio son los bloques de paso.
    columnas = bloques[1:-2]
    filas = tabla.get("horario", [])
    if filas and len(filas[0].get("horas", [])) != len(columnas):
        raise SystemExit(
            f"La tabla no cuadra: {len(columnas)} columnas pero "
            f"{len(filas[0]['horas'])} horas por fila. La API ha cambiado de formato."
        )

    ids = [IDS.get(c, slug(c)) for c in columnas]
    for idp, nombre in zip(ids, columnas):
        stops.setdefault(idp, {"id": idp, "name": NOMBRES_CORTOS.get(idp, nombre), "officialName": nombre})

    # Solo entran en el corredor las paradas por las que para algo: la API
    # deja columnas a cero que solo estorbarían en la tabla.
    servidas = {
        idp
        for fila in filas
        for idp, hora in zip(ids, fila.get("horas", []))
        if parse_hora(hora) is not None
    }
    corredores.append({
        "id": corredor_id,
        "name": corredor_nombre,
        "stops": [i for i in ids if i in servidas],
    })

    añadidas = 0
    for fila in filas:
        paradas = []
        for idp, hora in zip(ids, fila.get("horas", [])):
            t = parse_hora(hora)
            if t is not None:
                paradas.append({"stopId": idp, "time": t})
        # Una expedición que solo toca una parada no lleva a ningún sitio.
        if len(paradas) < 2:
            continue
        paradas = cruzar_medianoche(paradas)

        codigo = fila.get("codigo", "?")
        idl = slug(codigo)
        lines.setdefault(idl, {"id": idl, "code": codigo, "name": codigo, "ctanId": str(fila.get("idlinea", ""))})

        viaje = {"lineId": idl, "days": fila.get("dias", "").strip(),
                 "corridorId": corredor_id, "stops": paradas}
        obs = (fila.get("observaciones") or "").strip()
        if obs:
            viaje["notes"] = obs
        trips.append(viaje)
        añadidas += 1
    return añadidas


def recortar_al_corredor(trips: list) -> tuple:
    """Deja en cada expedición solo las paradas del corredor que nos importa
    y le asigna el sentido que lleva DE VERDAD.

    El "Ida" y "Vuelta" de la API van referidos al sentido propio de cada
    línea, no al nuestro: para la M-967, que hace Chipiona-Sanlúcar-Cádiz, su
    ida baja hacia Cádiz, o sea nuestra vuelta. Fiarse de esa etiqueta metía
    viajes de vuelta en la tabla de ida, con las horas decreciendo. El sentido
    se deduce de si la expedición avanza hacia el campus o hacia Cádiz.

    Devuelve (descartadas, recolocadas).
    """
    orden = {IDS.get(n, slug(n)): i for i, n in enumerate(CORREDOR)}
    antes = len(trips)
    recolocadas = 0
    for t in trips:
        t["stops"] = [p for p in t["stops"] if p["stopId"] in orden]
        if len(t["stops"]) < 2:
            continue
        sentido = "ida" if orden[t["stops"][-1]["stopId"]] > orden[t["stops"][0]["stopId"]] else "vuelta"
        if sentido != t["corridorId"]:
            t["corridorId"] = sentido
            recolocadas += 1
    trips[:] = [t for t in trips if len(t["stops"]) >= 2]
    return antes - len(trips), recolocadas


def corredores_del_tramo(trips: list) -> list:
    """Las columnas de la tabla de horarios, en orden de recorrido."""
    orden = [IDS.get(n, slug(n)) for n in CORREDOR]
    salida = []
    for corredor_id, nombre, secuencia in (
        ("ida", "Cádiz → Campus", orden),
        ("vuelta", "Campus → Cádiz", list(reversed(orden))),
    ):
        usadas = {p["stopId"] for t in trips if t["corridorId"] == corredor_id for p in t["stops"]}
        salida.append({"id": corredor_id, "name": nombre,
                       "stops": [i for i in secuencia if i in usadas]})
    return salida


def validar(trips: list, corredores: list) -> list:
    """Comprueba lo que tiene que cumplirse sí o sí, y devuelve los problemas.

    Un horario mal no avisa: simplemente hace perder un autobús. Así que estas
    comprobaciones van en el generador, no en los tests de la app.
    """
    problemas = []
    orden = {c["id"]: {p: i for i, p in enumerate(c["stops"])} for c in corredores}
    for n, t in enumerate(trips):
        horas = [p["time"] for p in t["stops"]]
        if horas != sorted(horas):
            problemas.append(f"expedición {n} ({t['lineId']}, {t['days']}): las horas "
                             f"no van en orden: {horas}")
    return problemas


def avisos_de_orden(trips: list, corredores: list) -> list:
    """Expediciones cuyas paradas no siguen el orden de las columnas.

    No es un error: cada línea atraviesa Cádiz por donde le conviene y ninguna
    secuencia lineal de paradas vale para todas. Solo afecta a cómo se ven en
    la tabla, no a los cálculos, que van por horas.
    """
    orden = {c["id"]: {p: i for i, p in enumerate(c["stops"])} for c in corredores}
    raros = []
    for t in trips:
        pos = [orden.get(t["corridorId"], {}).get(p["stopId"]) for p in t["stops"]]
        pos = [x for x in pos if x is not None]
        if pos != sorted(pos):
            raros.append(f"{t['lineId']} [{t['days']}] {t['corridorId']}")
    return raros


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--desde-volcado", metavar="CARPETA",
                    help="lee el corredor de un volcado local en vez de la API")
    ap.add_argument("--lineas-desde", metavar="CARPETA", action="append", default=[],
                    help="añade horarios por línea desde un volcado de horarios_lineas "
                         "(se puede repetir)")
    ap.add_argument("--solo", metavar="CODIGOS",
                    help="al leer horarios por línea, quedarse solo con estos códigos, "
                         "separados por comas. Sus expediciones sustituyen a las que "
                         "venían del corredor, para no duplicarlas.")
    args = ap.parse_args()

    stops: dict = {}
    lines: dict = {}
    trips: list = []
    corredores: list = []
    periodos: dict = {}
    solo = {c.strip() for c in args.solo.split(",")} if args.solo else None

    # La tabla del corredor solo se usa si se pide: los horarios por línea son
    # mejor fuente, porque traen el periodo de vigencia de cada expedición.
    if args.desde_volcado or not args.lineas_desde:
        leer = (lambda o, d: desde_volcado(Path(args.desde_volcado), o, d)) if args.desde_volcado else descargar
        fuente = f"volcado local {args.desde_volcado}" if args.desde_volcado else "api.ctan.es"
        print(f"Leyendo el corredor de {fuente}...")
        n_ida = normalizar(leer(NUCLEO_CASA, NUCLEO_CAMPUS), stops, lines, trips,
                           "ida", "Cádiz → Campus", corredores)
        n_vuelta = normalizar(leer(NUCLEO_CAMPUS, NUCLEO_CASA), stops, lines, trips,
                              "vuelta", "Campus → Cádiz", corredores)
        print(f"  {n_ida} expediciones de ida, {n_vuelta} de vuelta")
        if solo:
            # Lo que venga del volcado por línea manda sobre la tabla del corredor.
            ids_fuera = {l["id"] for l in lines.values() if l["code"] in solo}
            antes = len(trips)
            trips[:] = [t for t in trips if t["lineId"] not in ids_fuera]
            if antes != len(trips):
                print(f"  {antes - len(trips)} del corredor sustituidas ({', '.join(sorted(solo))})")

    for carpeta in args.lineas_desde:
        print(f"Leyendo los horarios por línea de {carpeta}...")
        n = normalizar_lineas(Path(carpeta), stops, lines, trips, periodos, solo)
        print(f"  {n} expediciones")

    if not corredores:
        descartadas, recolocadas = recortar_al_corredor(trips)
        corredores = corredores_del_tramo(trips)
        print(f"  recortado al corredor Cádiz–Campus: {descartadas} descartadas por no "
              f"servir dos paradas del tramo, {recolocadas} con el sentido corregido")

    # Solo nos quedamos con las paradas por las que pasa algo.
    usadas = {p["stopId"] for t in trips for p in t["stops"]}
    stops = {k: v for k, v in stops.items() if k in usadas}
    print(f"  {len(stops)} paradas, {len(lines)} líneas")

    for clave in ("telegrafia", "casem", "esi"):
        if clave not in stops:
            raise SystemExit(f"No aparece la parada '{clave}'. Los nombres de bloque han cambiado.")

    hoy = datetime.date.today()
    anios = [hoy.year, hoy.year + 1]

    avisos = [
        "Los horarios son los oficiales publicados. No es posición en tiempo real.",
        "Faltan los festivos de fecha variable (Semana Santa) y los locales de "
        "Cádiz y Puerto Real. En esos días el horario mostrado puede no valer.",
    ]
    # horarios_origen_destino no dice a qué planificador pertenece cada
    # horario; horarios_lineas sí. Según de dónde vengan los datos, el aviso
    # es uno u otro, y decir los dos a la vez sería contradecirse.
    if any("periodId" not in t for t in trips):
        avisos.append(
            "Estos datos no traen periodo de vigencia, así que la app no puede "
            "distinguir el horario de curso del de verano. Conviene regenerarlos "
            "al empezar el curso y al empezar el verano."
        )
        avisos.extend(AVISOS_EXTRA)
    else:
        avisos.append(
            "Cada expedición sabe desde cuándo circula, así que la app "
            "distingue el horario de curso del de verano."
        )

    presentes = {l["code"] for l in lines.values()}
    faltan = [
        {"code": c, "note": m}
        for c, m in sorted(LINEAS_ESPERADAS.items())
        if c not in presentes
    ]
    for l in faltan:
        print(f"  AVISO: falta la línea {l['code']} ({l['note']})")

    schedule = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source": f"api.ctan.es · Consorcio {CONSORCIO} (Bahía de Cádiz) · " + (
            f"horarios_lineas (por línea, con periodos de vigencia)"
            if all("periodId" in t for t in trips)
            else f"horarios_origen_destino {NUCLEO_CASA}<->{NUCLEO_CAMPUS}"),
        "isSample": False,
        "warnings": avisos,
        "missingLines": faltan,
        "stops": sorted(stops.values(), key=lambda s: s["id"]),
        "lines": sorted(lines.values(), key=lambda l: l["code"]),
        "corridors": corredores,
        "periods": sorted(periodos.values(), key=lambda p: p["from"]),
        "trips": trips,
        "walkLinks": [
            {"from": "esi", "to": "casem", "minutes": ANDANDO_ESI_CASEM},
            {"from": "casem", "to": "esi", "minutes": ANDANDO_ESI_CASEM},
        ],
        "holidays": sorted(festivos_fijos(anios)),
    }

    raros = avisos_de_orden(trips, corredores)
    if raros:
        print(f"  {len(raros)} expediciones no siguen el orden de columnas "
              f"(rutas distintas por Cádiz): {', '.join(sorted(set(raros)))}")

    problemas = validar(trips, corredores)
    if problemas:
        print(f"\n{len(problemas)} problemas en los datos:")
        for p in problemas[:10]:
            print(f"  - {p}")
        raise SystemExit("No escribo un horario con estos problemas.")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(schedule, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nEscrito {SALIDA} ({SALIDA.stat().st_size:,} bytes)")

    frec: dict[str, int] = {}
    for t in trips:
        frec[t["days"]] = frec.get(t["days"], 0) + 1
    print(f"  frecuencias: {frec}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
