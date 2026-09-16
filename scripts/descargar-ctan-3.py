#!/usr/bin/env python3
"""
Tercera ronda: horarios por línea, con periodos de vigencia.

Las dos primeras rondas usaron horarios_origen_destino, que devuelve la tabla
del corredor Cádiz <-> Campus pero NO dice a qué periodo pertenece cada
horario. Eso deja fuera dos cosas:

  1. La M-035 (Cádiz - Escuela de Ingeniería), que arranca el día 21 y por eso
     no aparecía en un volcado hecho el 16.
  2. El horario de verano, que no se puede distinguir del de curso.

Las dos se arreglan con horarios_lineas, que además de las horas devuelve los
"planificadores": los periodos con fecha de inicio y fin.

Uso:
    python3 scripts/descargar-ctan-3.py

No necesita instalar nada: solo Python 3.8 o superior.
Deja todo en ctan-dump3/ y un resumen legible en ctan-dump3/RESUMEN.md
"""

from __future__ import annotations

import gzip
import io
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://api.ctan.es/v1"
CONSORCIO = "2"
OUT = Path("ctan-dump3")
TIMEOUT = 30
PAUSA = 0.3

# Las líneas que nos interesan, con su código para poder leer el resumen.
LINEAS = {
    "220": "M-035  Cádiz-Escuela de Ingeniería",   # la que falta
    "6":   "M-030  Cádiz-Campus-Puerto Real-Hospital",
    "9":   "M-031  Cádiz-Campus-Puerto Real",
    "10":  "M-032  Cádiz-Río San Pedro-Puerto Real",
    "11":  "M-033  Cádiz-Puerto Real (directo)",
    "12":  "M-034  Cádiz-Hospital (por autovía)",
    "239": "M-036  Cádiz-Puerto Real (por CA-35)",
    "240": "M-037  Cádiz-Campus (por CA-35)",
    "267": "M-038  Cádiz-Puerto Real (Av. Constitución y CA-35)",
    "14":  "M-041  Cádiz-El Puerto (por Campus)",
    "18":  "M-052  Cádiz-Jerez (por Campus)",
    "20":  "M-061  Cádiz-El Puerto-Rota (por Campus)",
    "38":  "M-904  ",
    "163": "M-960  Chipiona-Sanlúcar-Cádiz (por Campus)",
    "225": "M-967  Chipiona-Sanlúcar-Cádiz (por Campus)",
}

# Fechas de sondeo: antes del 21, el propio 21, ya metidos en curso, y verano.
# Sirven para ver qué planificador está vigente en cada momento.
FECHAS = [(20, 9), (21, 9), (15, 10), (15, 8)]

resumen: list[str] = []


def log(t: str = "") -> None:
    print(t)
    resumen.append(t)


def slug(p: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", p).strip("_") or "root"


def get(path: str, params: dict | None = None):
    url = f"{BASE}{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    etiqueta = path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "Accept-Encoding": "gzip",
        "User-Agent": "buses-uca/0.1 (proyecto personal de estudiante)"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as res:
            raw = res.read()
            if res.headers.get("Content-Encoding") == "gzip":
                raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            status = res.status
    except urllib.error.HTTPError as e:
        raw, status = e.read(), e.code
    except Exception as e:
        log(f"  ERROR {etiqueta}: {e}")
        return None
    finally:
        time.sleep(PAUSA)

    (OUT / f"{slug(etiqueta)}.json").write_bytes(raw)
    if status != 200:
        log(f"  {status}   {etiqueta}")
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log(f"  ok    {etiqueta} (no es JSON)")
        return None


def resumir_horario(d: dict) -> None:
    """Imprime lo esencial de una respuesta de horarios_lineas."""
    for pl in d.get("planificadores", []):
        if isinstance(pl, dict):
            log(f"      PERIODO {pl.get('fechaInicio')} -> {pl.get('fechaFin')} "
                f"(muestraFechaFin={pl.get('muestraFechaFin')})")
    for sentido in ("Ida", "Vuelta"):
        bloques = [b.get("nombre") for b in d.get(f"bloques{sentido}", []) if isinstance(b, dict)]
        filas = d.get(f"horario{sentido}", [])
        if not bloques and not filas:
            continue
        log(f"      {sentido}: {len(filas)} salidas · columnas {bloques}")
        for fila in filas[:3]:
            log(f"        {fila}")
    if d.get("frecuencias"):
        log(f"      frecuencias: {d['frecuencias']}")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    c = f"/Consorcios/{CONSORCIO}"
    log("# Tercera ronda: horarios por línea\n")

    # 1. Lo primero, la M-035, que es el motivo de esta ronda.
    log("## M-035 (Cádiz - Escuela de Ingeniería), línea 220\n")
    log("  Recorrido y paradas:")
    ps = get(f"{c}/lineas/220/paradas")
    if isinstance(ps, dict):
        for p in ps.get("paradas", []):
            log(f"      {p.get('idParada'):>4}  {p.get('nombre')}")
    get(f"{c}/corredores/220/bloques")
    log()

    # 2. Horarios de cada línea en cada fecha de sondeo.
    log("## Horarios por línea y fecha\n")
    for idl, nombre in LINEAS.items():
        log(f"\n### {nombre}  (línea {idl})")
        # Sin fecha: devuelve lo que la API considere vigente ahora.
        log("\n  -- sin fecha --")
        d = get(f"{c}/horarios_lineas", {"linea": idl, "frecuencia": "", "dia": "", "mes": "", "lang": "ES"})
        if isinstance(d, dict):
            resumir_horario(d)
        for dia, mes in FECHAS:
            log(f"\n  -- {dia:02d}/{mes:02d} --")
            d = get(f"{c}/horarios_lineas",
                    {"linea": idl, "frecuencia": "", "dia": str(dia), "mes": str(mes), "lang": "ES"})
            if isinstance(d, dict):
                resumir_horario(d)

    # 3. El corredor otra vez: si hoy ya es 21 o más, debería traer la M-035.
    log("\n\n## Corredor Cádiz <-> Campus (para comparar con el volcado anterior)\n")
    for origen, destino, etiqueta in (("1", "41", "Cádiz -> Campus"), ("41", "1", "Campus -> Cádiz")):
        log(f"\n  --- {etiqueta} ---")
        d = get(f"{c}/horarios_origen_destino", {"origen": origen, "destino": destino, "lang": "ES"})
        if isinstance(d, dict):
            filas = d.get("horario", [])
            codigos: dict[str, int] = {}
            for f in filas:
                codigos[f.get("codigo", "?")] = codigos.get(f.get("codigo", "?"), 0) + 1
            log(f"      {len(filas)} salidas · líneas: {codigos}")
            log(f"      ¿aparece la M-035? {'SÍ' if any(f.get('codigo') == 'M-035' for f in filas) else 'no'}")

    # 4. De paso, el endpoint que falló en la ronda 2, por si era la forma de la URL.
    log("\n\n## lineasPorParadas (falló en la ronda 2, probando variantes)\n")
    for variante in ("/lineasPorParadas/7", "/lineasPorParadas/7,79", "/lineasPorParadas/262",
                     "/infoParadas/7", "/paradas/7"):
        get(f"{c}{variante}")

    (OUT / "RESUMEN.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    print(f"\nHecho. {len(list(OUT.iterdir()))} ficheros en {OUT}/")
    print(f"Resumen legible en {OUT / 'RESUMEN.md'}")
    print("\nSube la carpeta al repo:")
    print("  git add ctan-dump3/ && git commit -m 'Volcado 3 de la API' && git push")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(1)
