#!/usr/bin/env python3
"""
Cuarta ronda: la semana completa del horario nuevo, con periodos.

Lo aprendido en la ronda 3:

  - El horario NO está en el nivel de arriba de la respuesta, sino dentro de
    cada elemento de "planificadores" (bloquesIda, horarioIda, bloquesVuelta,
    horarioVuelta). Ahí estaba el despiste de la ronda anterior.
  - Los parámetros dia/mes no filtran solo por periodo: filtran también por
    día de la semana. Preguntando por un lunes te devuelve los servicios que
    circulan en lunes. Por eso hay que sondear un día de cada tipo para
    reconstruir la semana entera.
  - El 21 de septiembre de 2026 entra un horario nuevo: arrancan la M-035
    (directa a la Escuela de Ingeniería), la M-037 y la M-038.

Esta ronda pide, para cada línea, un día de cada tipo dentro del horario
nuevo, más dos días de verano para capturar ese periodo.

Uso:
    python3 scripts/descargar-ctan-4.py

No necesita instalar nada: solo Python 3.8 o superior.
Deja todo en ctan-dump4/ y un resumen legible en ctan-dump4/RESUMEN.md
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
OUT = Path("ctan-dump4")
TIMEOUT = 30
PAUSA = 0.3

LINEAS = {
    "220": "M-035", "6": "M-030", "9": "M-031", "10": "M-032", "11": "M-033",
    "12": "M-034", "239": "M-036", "240": "M-037", "267": "M-038", "14": "M-041",
    "18": "M-052", "20": "M-061", "38": "M-904", "163": "M-960", "225": "M-967",
}

# Un día de cada tipo dentro del horario que entra el 21 de septiembre de 2026,
# para que salgan todas las frecuencias (L-V, L-J, V, S, D, S-D-F, L-D...).
# Y dos de agosto, para el periodo de verano.
FECHAS = [
    (21, 9, "lunes"),
    (25, 9, "viernes"),
    (26, 9, "sábado"),
    (27, 9, "domingo"),
    (12, 8, "verano, miércoles"),
    (15, 8, "verano, sábado"),
]

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
        return None


def main() -> int:
    OUT.mkdir(exist_ok=True)
    c = f"/Consorcios/{CONSORCIO}"
    log("# Cuarta ronda: la semana completa del horario nuevo\n")

    total = 0
    for idl, codigo in LINEAS.items():
        log(f"\n### {codigo} (línea {idl})")
        for dia, mes, etiqueta in FECHAS:
            d = get(f"{c}/horarios_lineas",
                    {"linea": idl, "frecuencia": "", "dia": str(dia), "mes": str(mes), "lang": "ES"})
            if not isinstance(d, dict):
                log(f"  {dia:02d}/{mes:02d} ({etiqueta}): sin respuesta")
                continue
            pls = d.get("planificadores") or []
            if not pls:
                log(f"  {dia:02d}/{mes:02d} ({etiqueta}): no circula")
                continue
            for pl in pls:
                ida = pl.get("horarioIda") or []
                vta = pl.get("horarioVuelta") or []
                total += len(ida) + len(vta)
                frecs = sorted({f.get("frecuencia", "?") for f in list(ida) + list(vta)})
                log(f"  {dia:02d}/{mes:02d} ({etiqueta}): periodo "
                    f"{pl.get('fechaInicio')} -> {pl.get('fechaFin') or '(abierto)'} · "
                    f"{len(ida)} ida, {len(vta)} vuelta · frecuencias {frecs}")

    # El corredor entero, como contraste. Ojo: este endpoint no acepta fecha,
    # así que devuelve lo vigente HOY. Antes del 21 no traerá las líneas nuevas.
    log("\n\n## Corredor Cádiz <-> Campus (lo vigente hoy, para contrastar)\n")
    for origen, destino, etiqueta in (("1", "41", "Cádiz -> Campus"), ("41", "1", "Campus -> Cádiz")):
        d = get(f"{c}/horarios_origen_destino", {"origen": origen, "destino": destino, "lang": "ES"})
        if isinstance(d, dict):
            filas = d.get("horario", [])
            codigos: dict[str, int] = {}
            for f in filas:
                codigos[f.get("codigo", "?")] = codigos.get(f.get("codigo", "?"), 0) + 1
            log(f"  {etiqueta}: {len(filas)} salidas · {codigos}")
            log(f"    ¿está ya la M-035? {'SÍ' if 'M-035' in codigos else 'todavía no'}")

    (OUT / "RESUMEN.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    print(f"\nHecho. {total} salidas recogidas en {len(list(OUT.iterdir()))} ficheros.")
    print(f"Resumen legible en {OUT / 'RESUMEN.md'}")
    print("\nSube la carpeta al repo:")
    print("  git add ctan-dump4")
    print("  git commit -m \"Volcado 4 de la API\"")
    print("  git push")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(1)
