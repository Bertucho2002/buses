"""Genera datos de EJEMPLO para poder desarrollar sin acceso a la API.

No son horarios reales. Se sustituyen en cuanto se pueda leer api.ctan.es.
"""
import json, datetime

def m(hhmm):
    h, mm = hhmm.split(":")
    return int(h) * 60 + int(mm)

stops = [
    {"id": "telegrafia", "name": "Telegrafía", "officialName": "Telegrafía Sin Hilos"},
    {"id": "esi", "name": "ESI", "officialName": "Escuela Ingeniería"},
    {"id": "casem", "name": "CASEM", "officialName": "C. Educación/Facultad Ciencias"},
]

lines = [
    {"id": "linea-campus", "code": "EJEMPLO-1", "name": "Cádiz – Campus Puerto Real", "kind": "bus"},
    {"id": "lanzadera", "code": "EJEMPLO-L", "name": "Lanzadera CASEM – ESI", "kind": "lanzadera"},
]

periods = [
    {"id": "lectivo", "name": "Periodo lectivo", "from": "2026-09-01", "to": "2027-06-30"},
    {"id": "verano", "name": "Verano", "from": "2027-07-01", "to": "2027-08-31"},
]

calendars = [
    {"id": f"{p['id']}-{d}", "periodId": p["id"], "dayType": d}
    for p in periods
    for d in ("laborable", "sabado", "domingo-festivo")
]

trips = []

def bus(cal, dep, to_esi):
    """Ida: Telegrafía -> CASEM -> (ESI)."""
    s = [{"stopId": "telegrafia", "time": m(dep)},
         {"stopId": "casem", "time": m(dep) + 25}]
    if to_esi:
        s.append({"stopId": "esi", "time": m(dep) + 32})
    trips.append({"lineId": "linea-campus", "calendarId": cal, "stops": s})

def vuelta(cal, dep, from_esi):
    """Vuelta: (ESI) -> CASEM -> Telegrafía."""
    s = []
    t = m(dep)
    if from_esi:
        s.append({"stopId": "esi", "time": t})
        t += 7
    s.append({"stopId": "casem", "time": t})
    s.append({"stopId": "telegrafia", "time": t + 25})
    trips.append({"lineId": "linea-campus", "calendarId": cal, "stops": s})

def lanzadera(cal, dep, ida):
    a, b = ("casem", "esi") if ida else ("esi", "casem")
    trips.append({"lineId": "lanzadera", "calendarId": cal,
                  "stops": [{"stopId": a, "time": m(dep)}, {"stopId": b, "time": m(dep) + 6}]})

# Laborables lectivos: por la mañana llegan buses a la ESI, por la tarde casi ninguno.
for i, dep in enumerate(["07:15", "07:45", "08:15", "08:45", "09:15", "09:45",
                         "10:15", "11:15", "12:15", "13:15", "14:15", "15:15",
                         "16:15", "17:15", "18:15", "19:15", "20:15"]):
    bus("lectivo-laborable", dep, to_esi=(i < 7 or dep in ("13:15", "19:15")))

for i, dep in enumerate(["08:10", "09:10", "10:10", "13:10", "14:10", "15:10",
                         "16:10", "17:10", "18:10", "19:10", "20:10", "21:10"]):
    vuelta("lectivo-laborable", dep, from_esi=(dep in ("14:10", "15:10", "20:10")))

for h in range(8, 21):
    for mm in ("05", "35"):
        lanzadera("lectivo-laborable", f"{h:02d}:{mm}", ida=True)
        lanzadera("lectivo-laborable", f"{h:02d}:{mm}", ida=False)

# Sábados: servicio reducido, sin lanzadera.
for dep in ["09:15", "11:15", "13:15", "17:15", "19:15"]:
    bus("lectivo-sabado", dep, to_esi=False)
for dep in ["10:10", "12:10", "14:10", "18:10", "20:10"]:
    vuelta("lectivo-sabado", dep, from_esi=False)

# Verano: mínimos.
for dep in ["08:15", "12:15", "16:15"]:
    bus("verano-laborable", dep, to_esi=False)
for dep in ["09:10", "13:10", "17:10"]:
    vuelta("verano-laborable", dep, from_esi=False)

schedule = {
    "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "source": "DATOS DE EJEMPLO INVENTADOS — no son horarios reales",
    "isSample": True,
    "stops": stops,
    "lines": lines,
    "periods": periods,
    "calendars": calendars,
    "trips": trips,
    "walkLinks": [
        {"from": "esi", "to": "casem", "minutes": 18},
        {"from": "casem", "to": "esi", "minutes": 18},
    ],
    "holidays": ["2026-10-12", "2026-11-02", "2026-12-08", "2026-12-25", "2027-01-01"],
}

with open("src/data/schedule.json", "w", encoding="utf-8") as f:
    json.dump(schedule, f, ensure_ascii=False, indent=2)
print(f"{len(trips)} expediciones de ejemplo")
