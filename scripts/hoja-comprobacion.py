#!/usr/bin/env python3
"""Genera COMPROBACION.md: los horarios en tabla, para contrastarlos con la
web del consorcio sin tener que leer el JSON.

Uso:
    python3 scripts/hoja-comprobacion.py [YYYY-MM-DD]

Sin fecha usa el próximo martes lectivo, que es el día con más servicio.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

HORARIO = Path("src/data/schedule.json")
SALIDA = Path("COMPROBACION.md")


def circula(t: dict, s: dict, fecha: datetime.date) -> bool:
    iso = fecha.isoformat()
    if t.get("periodId"):
        p = next((p for p in s["periods"] if p["id"] == t["periodId"]), None)
        if not p or iso < p["from"] or iso > p["to"]:
            return False
    dow = (fecha.weekday() + 1) % 7  # 0 domingo ... 6 sábado
    festivo = iso in s["holidays"] or dow == 0
    lab = not festivo
    return {
        "L-V": lab and 1 <= dow <= 5, "L-J": lab and 1 <= dow <= 4,
        "V": lab and dow == 5, "L": lab and dow == 1,
        "L-S": lab and 1 <= dow <= 6, "S": lab and dow == 6,
        "D": festivo, "D*": festivo,
        "S-D-F": festivo or (lab and dow == 6), "L-D": True,
    }.get(t["days"].strip().upper(), False)


def hm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def main() -> int:
    s = json.loads(HORARIO.read_text(encoding="utf-8"))
    if len(sys.argv) > 1:
        fecha = datetime.date.fromisoformat(sys.argv[1])
    else:
        fecha = datetime.date.today()
        while fecha.weekday() != 1 or fecha.isoformat() in s["holidays"]:
            fecha += datetime.timedelta(days=1)

    codigo = {l["id"]: l["code"] for l in s["lines"]}
    viajes = [t for t in s["trips"] if circula(t, s, fecha)]

    out = [
        "# Hoja de comprobación de horarios",
        "",
        f"Horarios del **{DIAS[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}**, "
        "tal y como los está usando la app.",
        "Contrastar con <https://siu.cmtbc.es/movil/horarios_lineas.php>.",
        "",
        f"Generados el {s['generatedAt'][:10]} desde `{s['source']}`.",
        "",
    ]
    for corredor in s["corridors"]:
        clave = [i for i in corredor["stops"] if i in ("telegrafia", "casem", "esi")]
        nombre = {x["id"]: x["name"] for x in s["stops"]}
        filas = sorted(
            (t for t in viajes if t["corridorId"] == corredor["id"]),
            key=lambda t: t["stops"][0]["time"],
        )
        out += ["", f"## {corredor['name']}", "",
                "| Línea | " + " | ".join(nombre[i] for i in clave) + " | Días |",
                "| --- | " + " | ".join("---" for _ in clave) + " | --- |"]
        for t in filas:
            porp = {p["stopId"]: p["time"] for p in t["stops"]}
            celdas = " | ".join(hm(porp[i]) if i in porp else "·" for i in clave)
            out.append(f"| {codigo[t['lineId']]} | {celdas} | {t['days']} |")
        out.append("")
        out.append(f"{len(filas)} salidas.")

    out += ["", "## Qué mirar", "",
            "No hace falta repasarlo entero. Con estas cuatro cosas vale:", "",
            "1. **El primero de la mañana** que llega a la ESI.",
            "2. **El hueco de la tarde**: ¿de verdad no hay buses directos a la ESI",
            "   entre media tarde y la noche?",
            "3. **La M-035**, que arranca el 21 de septiembre: ida a las 07:48 desde",
            "   Telegrafía, y vuelta a las 20:10 y 21:15 de lunes a jueves.",
            "4. **El último de la noche**.", "",
            "Si algo no cuadra, di **qué línea y qué hora**.", ""]
    SALIDA.write_text("\n".join(out), encoding="utf-8")
    print(f"Escrito {SALIDA}: {len(viajes)} expediciones del {fecha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
