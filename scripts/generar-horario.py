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
    "telegrafia": "Telegrafía",
    "casem": "CASEM",
    "esi": "ESI",
}

# Minutos andando entre las dos paradas del campus.
ANDANDO_ESI_CASEM = 18

# Festivos de fecha fija en Andalucía. Los de fecha variable (Semana Santa) y
# los locales de Cádiz y Puerto Real NO están: hay que añadirlos a mano en
# src/data/festivos.json. La app avisa de esto en pantalla.
def festivos_fijos(anios: list[int]) -> list[str]:
    fijos = [(1, 1), (1, 6), (2, 28), (5, 1), (8, 15), (10, 12), (11, 1), (12, 6), (12, 8), (12, 25)]
    return [f"{a:04d}-{m:02d}-{d:02d}" for a in anios for m, d in fijos]


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


def normalizar(tabla: dict, stops: dict, lines: dict, trips: list) -> int:
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

        codigo = fila.get("codigo", "?")
        idl = slug(codigo)
        lines.setdefault(idl, {"id": idl, "code": codigo, "name": codigo, "ctanId": str(fila.get("idlinea", ""))})

        viaje = {"lineId": idl, "days": fila.get("dias", "").strip(), "stops": paradas}
        obs = (fila.get("observaciones") or "").strip()
        if obs:
            viaje["notes"] = obs
        trips.append(viaje)
        añadidas += 1
    return añadidas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--desde-volcado", metavar="CARPETA",
                    help="lee de un volcado local en vez de la API")
    args = ap.parse_args()

    leer = (lambda o, d: desde_volcado(Path(args.desde_volcado), o, d)) if args.desde_volcado else descargar
    fuente = f"volcado local {args.desde_volcado}" if args.desde_volcado else "api.ctan.es"
    print(f"Leyendo de {fuente}...")

    ida = leer(NUCLEO_CASA, NUCLEO_CAMPUS)
    vuelta = leer(NUCLEO_CAMPUS, NUCLEO_CASA)

    stops: dict = {}
    lines: dict = {}
    trips: list = []
    n_ida = normalizar(ida, stops, lines, trips)
    n_vuelta = normalizar(vuelta, stops, lines, trips)
    print(f"  {n_ida} expediciones de ida, {n_vuelta} de vuelta")

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
    # La API no da los periodos de vigencia por este endpoint, así que no
    # sabemos si esto es el horario de curso o el de verano.
    avisos.append(
        "Estos datos no traen periodo de vigencia, así que la app no puede "
        "distinguir el horario de curso del de verano. Conviene regenerarlos "
        "al empezar el curso y al empezar el verano."
    )

    schedule = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source": f"api.ctan.es · Consorcio {CONSORCIO} (Bahía de Cádiz) · "
                  f"horarios_origen_destino {NUCLEO_CASA}<->{NUCLEO_CAMPUS}",
        "isSample": False,
        "warnings": avisos,
        "stops": sorted(stops.values(), key=lambda s: s["id"]),
        "lines": sorted(lines.values(), key=lambda l: l["code"]),
        "periods": [],
        "trips": trips,
        "walkLinks": [
            {"from": "esi", "to": "casem", "minutes": ANDANDO_ESI_CASEM},
            {"from": "casem", "to": "esi", "minutes": ANDANDO_ESI_CASEM},
        ],
        "holidays": sorted(festivos_fijos(anios)),
    }

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
