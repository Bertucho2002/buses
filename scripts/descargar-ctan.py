#!/usr/bin/env python3
"""
Reconocimiento de la API de CTAN (Consorcios de Transporte de Andalucía).

Este script NO genera todavía el horario final de la app. Lo que hace es
descargar y volcar todo lo que la API responde, para poder ver la forma real
de los datos antes de escribir el conversor. Se ejecuta una vez, se sube el
resultado al repo y a partir de ahí se escribe el normalizador de verdad.

Uso:
    python3 scripts/descargar-ctan.py

No necesita instalar nada: solo Python 3.8 o superior.
Deja todo en ctan-dump/ y un resumen legible en ctan-dump/RESUMEN.md
"""

from __future__ import annotations

import gzip
import io
import json
import re
import ssl
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.ctan.es"
OUT = Path("ctan-dump")
TIMEOUT = 30
MAX_BYTES = 12 * 1024 * 1024  # no guardamos ficheros absurdamente grandes

# Trozos de nombre de las paradas que nos interesan. Se busca sin acentos y en
# minusculas, asi que da igual como los escriban ellos.
PARADAS_BUSCADAS = [
    "telegrafia",
    "escuela ingenieria",
    "ingenieria",
    "educacion",
    "facultad ciencias",
]

resumen: list[str] = []
descargados: dict[str, object] = {}


def log(linea: str = "") -> None:
    print(linea)
    resumen.append(linea)


def norm(s: str) -> str:
    """Minusculas y sin acentos, para comparar nombres sin sufrir."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()


def get(path: str) -> tuple[int, bytes, str]:
    """GET a la API. Devuelve (status, cuerpo, content-type)."""
    url = path if path.startswith("http") else f"{BASE}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, text/html;q=0.8, */*;q=0.5",
            "Accept-Encoding": "gzip",
            "User-Agent": "buses-uca/0.1 (proyecto personal de estudiante)",
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as res:
            raw = res.read(MAX_BYTES)
            if res.headers.get("Content-Encoding") == "gzip":
                raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            return res.status, raw, res.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(MAX_BYTES), e.headers.get("Content-Type", "")
    except Exception as e:  # red caida, DNS, TLS...
        print(f"  ERROR  {path}: {e}")
        return 0, b"", ""


def slug(path: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_")
    return s or "root"


def fetch(path: str, etiqueta: str = "") -> object | None:
    """Descarga, guarda en disco y devuelve el JSON si lo es."""
    status, body, ctype = get(path)
    if not body:
        return None

    es_json = "json" in ctype or body.lstrip()[:1] in (b"{", b"[")
    ext = "json" if es_json else ("html" if "html" in ctype else "txt")
    destino = OUT / f"{slug(path)}.{ext}"
    destino.write_bytes(body)

    if status != 200:
        log(f"  {status}   {path}")
        return None

    if not es_json:
        log(f"  ok    {path}  ({len(body):,} bytes, {ext}) -> {destino}")
        return None

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        log(f"  ok    {path}  (JSON ilegible: {e}) -> {destino}")
        return None

    log(f"  ok    {path}  ({describe(data)}) -> {destino}")
    descargados[path] = data
    return data


def describe(data: object) -> str:
    if isinstance(data, list):
        return f"lista de {len(data)}"
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                return f"dict con '{k}' de {len(v)}"
        return f"dict con claves {list(data)[:6]}"
    return type(data).__name__


def objetos(data: object):
    """Recorre recursivamente todos los dicts que haya dentro."""
    if isinstance(data, list):
        for x in data:
            yield from objetos(x)
    elif isinstance(data, dict):
        yield data
        for v in data.values():
            yield from objetos(v)


def texto_de(obj: dict) -> str:
    return norm(" ".join(str(v) for v in obj.values() if isinstance(v, (str, int))))


# --------------------------------------------------------------------------

def main() -> int:
    OUT.mkdir(exist_ok=True)
    log("# Reconocimiento de api.ctan.es\n")
    log(f"Base: {BASE}\n")

    # 1. La documentacion. Esta generada con apidocjs, que deja un fichero con
    #    TODOS los endpoints descritos. Si lo pillamos, nos ahorra adivinar.
    log("## Documentación de la API\n")
    doc = None
    for p in ("/doc/api_data.json", "/doc/api_project.json", "/doc/", "/doc/index.html"):
        got = fetch(p)
        if p == "/doc/api_data.json" and got:
            doc = got
    if doc and isinstance(doc, list):
        log(f"\n  La documentación describe {len(doc)} endpoints:")
        for ep in doc:
            if isinstance(ep, dict):
                log(f"    {ep.get('type', '?').upper():6} {ep.get('url', '?')}   {ep.get('title', '')}")
    log()

    # 2. Los consorcios, para localizar el de la Bahia de Cadiz.
    log("## Consorcios\n")
    consorcios = fetch("/v1/Consorcios")
    id_consorcio = None
    for obj in objetos(consorcios):
        t = texto_de(obj)
        if "cadiz" in t or "bahia" in t:
            log(f"\n  Candidato: {json.dumps(obj, ensure_ascii=False)}")
            for clave in ("idConsorcio", "id", "codigo"):
                if clave in obj and id_consorcio is None:
                    id_consorcio = str(obj[clave])
    if id_consorcio is None:
        id_consorcio = "2"
        log("\n  No he sabido deducir el id. Pruebo con 2, que suele ser Bahía de Cádiz.")
    log(f"\n  Consorcio elegido: {id_consorcio}\n")

    # 3. Los recursos del consorcio. Estas rutas son CANDIDATAS: si la
    #    documentacion del paso 1 dice otra cosa, manda la documentacion.
    log("## Recursos del consorcio\n")
    c = f"/v1/Consorcios/{id_consorcio}"
    rutas = [
        c,
        f"{c}/municipios",
        f"{c}/nucleos",
        f"{c}/zonas",
        f"{c}/modos",
        f"{c}/operadores",
        f"{c}/lineas",
        f"{c}/paradas",
        f"{c}/frecuencias",
        f"{c}/noticias",
        f"{c}/tarifas",
    ]
    paradas_data = None
    lineas_data = None
    for r in rutas:
        got = fetch(r)
        if r.endswith("/paradas"):
            paradas_data = got
        if r.endswith("/lineas"):
            lineas_data = got
    log()

    # 4. Localizar nuestras paradas por nombre.
    log("## Nuestras paradas\n")
    encontradas: list[dict] = []
    vistos = set()
    for obj in objetos(paradas_data):
        t = texto_de(obj)
        if any(n in t for n in PARADAS_BUSCADAS):
            firma = json.dumps(obj, sort_keys=True, ensure_ascii=False)
            if firma not in vistos:
                vistos.add(firma)
                encontradas.append(obj)
    if encontradas:
        log(f"  {len(encontradas)} coincidencias:\n")
        for obj in encontradas[:40]:
            log(f"    {json.dumps(obj, ensure_ascii=False)}")
    else:
        log("  Ninguna. Puede que las paradas cuelguen de cada línea en vez de")
        log("  ir en una lista global, o que el endpoint sea otro.")
    log()

    # 5. Para cada parada encontrada, que lineas pasan por ella.
    log("## Líneas que pasan por esas paradas\n")
    ids_parada = []
    for obj in encontradas:
        for clave in ("idParada", "idNodo", "id", "codigo"):
            if clave in obj:
                ids_parada.append(str(obj[clave]))
                break
    for idp in ids_parada[:12]:
        fetch(f"{c}/paradas/{idp}")
        fetch(f"{c}/paradas/{idp}/servicios")
    log()

    # 6. Horarios de unas cuantas lineas, que es lo que de verdad necesitamos.
    log("## Horarios (muestra)\n")
    ids_linea = []
    for obj in objetos(lineas_data):
        for clave in ("idLinea", "id", "codigo"):
            if clave in obj and isinstance(obj.get(clave), (str, int)):
                ids_linea.append(str(obj[clave]))
                break
    ids_linea = list(dict.fromkeys(ids_linea))
    log(f"  {len(ids_linea)} líneas en el consorcio. Bajo el detalle de las 6 primeras")
    log("  y de cualquiera cuyo nombre mencione Puerto Real o el campus.\n")

    interesantes = []
    for obj in objetos(lineas_data):
        t = texto_de(obj)
        if "puerto real" in t or "universidad" in t or "campus" in t or "cadiz" in t:
            for clave in ("idLinea", "id", "codigo"):
                if clave in obj:
                    interesantes.append(str(obj[clave]))
                    break
    muestra = list(dict.fromkeys(interesantes[:10] + ids_linea[:6]))

    for idl in muestra:
        for sufijo in ("", "/paradas", "/horarios", "/horarios_lineas", "/itinerario"):
            fetch(f"{c}/lineas/{idl}{sufijo}")
    log()

    # 7. Resumen en disco.
    (OUT / "RESUMEN.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    ficheros = sorted(p.name for p in OUT.iterdir())
    print(f"\nHecho. {len(ficheros)} ficheros en {OUT}/")
    print(f"Resumen legible en {OUT / 'RESUMEN.md'}")
    print("\nSiguiente paso: sube la carpeta ctan-dump/ al repo (ver instrucciones).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(1)
