#!/usr/bin/env python3
"""
Segunda ronda de descarga de la API de CTAN.

La primera ronda sirvió para leer la documentación y localizar las paradas.
Ahora ya sabemos exactamente qué endpoints hay y qué devuelven, así que esta
ronda va directa a lo que falta:

  1. Qué líneas paran en la ESI y en el CASEM (la primera ronda no lo pilló
     porque /paradas/:id/servicios solo lista los próximos servicios del día,
     y se ejecutó de noche).
  2. Los horarios de verdad, que están en /horarios_lineas y no bajo
     /lineas/:id/horarios como habíamos supuesto.
  3. Los "bloques" de cada línea, que son las columnas de la tabla de
     horarios, para poder saber qué hora corresponde a qué parada.
  4. Los periodos (lectivo, verano...), que la API llama "planificadores" y
     trae con fecha de inicio y fin.

Uso:
    python3 scripts/descargar-ctan-2.py

No necesita instalar nada: solo Python 3.8 o superior.
Deja todo en ctan-dump2/ y un resumen legible en ctan-dump2/RESUMEN.md
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
CONSORCIO = "2"  # Bahía de Cádiz
OUT = Path("ctan-dump2")
TIMEOUT = 30
PAUSA = 0.3  # un respiro entre peticiones, por educación

# Paradas que nos importan, confirmadas en la primera ronda.
PARADAS = {
    "7": "Telegrafía Sin Hilos (casa)",
    "79": "Campus-C. Educación",
    "81": "Campus-Ciencias",
    "262": "Escuela Ingeniería",
    "264": "Escuela Ingeniería (Interior)",
}
NUCLEO_CADIZ = "1"
NUCLEO_CAMPUS = "41"
NUCLEO_PUERTO_REAL = "6"

# Dos fechas de sondeo para ver si cambia el horario entre curso y verano.
FECHAS = [(15, 10), (15, 8)]

resumen: list[str] = []


def log(linea: str = "") -> None:
    print(linea)
    resumen.append(linea)


def slug(path: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_") or "root"


def get(path: str, params: dict | None = None):
    """GET a la API. Guarda la respuesta y devuelve el JSON si lo es."""
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "User-Agent": "buses-uca/0.1 (proyecto personal de estudiante)",
        },
    )
    etiqueta = path + ("?" + urllib.parse.urlencode(params) if params else "")
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

    destino = OUT / f"{slug(etiqueta)}.json"
    destino.write_bytes(raw)
    if status != 200:
        log(f"  {status}   {etiqueta}")
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log(f"  ok    {etiqueta}  (no es JSON, {len(raw):,} bytes)")
        return None
    log(f"  ok    {etiqueta}  -> {destino.name}")
    return data


def main() -> int:
    OUT.mkdir(exist_ok=True)
    c = f"/Consorcios/{CONSORCIO}"
    log("# Segunda ronda: horarios reales\n")

    # ----------------------------------------------------------------
    log("## Qué líneas paran en cada una de nuestras paradas\n")
    lineas_relevantes: dict[str, dict] = {}
    por_parada: dict[str, list] = {}
    for idp, nombre in PARADAS.items():
        log(f"\n  --- {nombre} (parada {idp}) ---")
        data = get(f"{c}/lineasPorParadas/{idp}")
        encontradas = data if isinstance(data, list) else []
        por_parada[idp] = encontradas
        for l in encontradas:
            if isinstance(l, dict) and "idLinea" in l:
                lineas_relevantes[str(l["idLinea"])] = l
                log(f"      {l.get('codigo','?'):>8}  {str(l.get('nombre',''))[:62]}")
        if not encontradas:
            log("      (ninguna)")

    log(f"\n  En total {len(lineas_relevantes)} líneas distintas tocan alguna parada nuestra.\n")

    # Las que de verdad nos sirven: tocan casa Y algún sitio del campus.
    campus = {"79", "81", "262", "264"}
    ids_casa = {str(l["idLinea"]) for l in por_parada.get("7", []) if isinstance(l, dict)}
    ids_campus = {
        str(l["idLinea"])
        for p in campus
        for l in por_parada.get(p, [])
        if isinstance(l, dict)
    }
    utiles = ids_casa & ids_campus
    log("## Líneas que conectan casa con el campus\n")
    for idl in sorted(utiles, key=int):
        l = lineas_relevantes[idl]
        log(f"  {idl:>4} {l.get('codigo','?'):>8}  {str(l.get('nombre',''))[:66]}")
    if not utiles:
        log("  Ninguna directa. Habrá que mirar transbordos.")
    log()

    # ----------------------------------------------------------------
    log("## Horarios entre núcleos (Cádiz <-> Campus Universitario)\n")
    for origen, destino, etiqueta in (
        (NUCLEO_CADIZ, NUCLEO_CAMPUS, "Cádiz -> Campus"),
        (NUCLEO_CAMPUS, NUCLEO_CADIZ, "Campus -> Cádiz"),
        (NUCLEO_CADIZ, NUCLEO_PUERTO_REAL, "Cádiz -> Puerto Real"),
        (NUCLEO_PUERTO_REAL, NUCLEO_CADIZ, "Puerto Real -> Cádiz"),
    ):
        log(f"\n  --- {etiqueta} ---")
        d = get(f"{c}/horarios_origen_destino", {"origen": origen, "destino": destino, "lang": "ES"})
        if isinstance(d, dict):
            bloques = [b.get("nombre") for b in d.get("bloques", []) if isinstance(b, dict)]
            log(f"      columnas: {bloques}")
            log(f"      {len(d.get('horario', []))} filas de horario")
            for fila in d.get("horario", [])[:4]:
                log(f"        {fila}")
    log()

    # ----------------------------------------------------------------
    # Todas las líneas que tocan el campus, aunque no pasen por casa: nos
    # interesan para los enlaces ESI <-> CASEM.
    a_consultar = sorted(utiles | ids_campus, key=int)
    log(f"## Paradas y bloques de {len(a_consultar)} líneas\n")
    for idl in a_consultar:
        l = lineas_relevantes.get(idl, {})
        log(f"\n  --- línea {idl} ({l.get('codigo','?')}) ---")
        ps = get(f"{c}/lineas/{idl}/paradas")
        if isinstance(ps, dict):
            nuestras = [
                f"{p.get('idParada')}:{p.get('nombre')}"
                for p in ps.get("paradas", [])
                if str(p.get("idParada")) in PARADAS
            ]
            log(f"      {len(ps.get('paradas', []))} paradas; nuestras: {nuestras or 'ninguna'}")
        get(f"{c}/corredores/{idl}/bloques")

    log()

    # ----------------------------------------------------------------
    log("## Horarios de línea (lo que de verdad necesitamos)\n")
    log("  Se piden sin filtros (devuelve todos los planificadores y frecuencias)")
    log("  y luego con dos fechas, para ver si el horario cambia en verano.\n")
    for idl in a_consultar:
        l = lineas_relevantes.get(idl, {})
        log(f"\n  --- línea {idl} ({l.get('codigo','?')}) ---")
        d = get(f"{c}/horarios_lineas", {"linea": idl, "frecuencia": "", "dia": "", "mes": "", "lang": "ES"})
        if isinstance(d, dict):
            for pl in d.get("planificadores", []):
                if isinstance(pl, dict):
                    log(f"      planificador {pl.get('fechaInicio')} -> {pl.get('fechaFin')}")
            bl = [b.get("nombre") for b in d.get("bloquesIda", []) if isinstance(b, dict)]
            log(f"      bloquesIda: {bl}")
            log(f"      {len(d.get('horarioIda', []))} salidas ida, {len(d.get('horarioVuelta', []))} vuelta")
            for fila in d.get("horarioIda", [])[:3]:
                log(f"        {fila}")
            log(f"      frecuencias de la línea: {d.get('frecuencias')}")
        for dia, mes in FECHAS:
            get(f"{c}/horarios_lineas",
                {"linea": idl, "frecuencia": "", "dia": str(dia), "mes": str(mes), "lang": "ES"})

    # ----------------------------------------------------------------
    (OUT / "RESUMEN.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    n = len(list(OUT.iterdir()))
    print(f"\nHecho. {n} ficheros en {OUT}/")
    print(f"Resumen legible en {OUT / 'RESUMEN.md'}")
    print("\nSube la carpeta ctan-dump2/ al repo:")
    print("  git add ctan-dump2/ && git commit -m 'Volcado 2 de la API' && git push")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(1)
