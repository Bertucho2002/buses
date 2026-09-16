/**
 * Sondea la API de CTAN y vuelca lo que devuelve, para poder ver la forma
 * real de los datos antes de escribir el normalizador definitivo.
 *
 *   npm run explore
 *
 * Los endpoints de abajo son CANDIDATOS deducidos de la documentacion
 * publica; este script sirve precisamente para confirmar cuales existen.
 * Todo lo que responda se guarda en .ctan-dump/ (ignorado por git).
 */
import { mkdir, writeFile } from "node:fs/promises";

const BASE = "https://api.ctan.es/v1";
const OUT = ".ctan-dump";

/** Bahia de Cadiz. Se confirma con la respuesta de /Consorcios. */
const CONSORCIO = process.env.CONSORCIO ?? "2";

const CANDIDATES = [
  "/Consorcios",
  `/Consorcios/${CONSORCIO}`,
  `/Consorcios/${CONSORCIO}/municipios`,
  `/Consorcios/${CONSORCIO}/nucleos`,
  `/Consorcios/${CONSORCIO}/modos`,
  `/Consorcios/${CONSORCIO}/lineas`,
  `/Consorcios/${CONSORCIO}/paradas`,
  `/Consorcios/${CONSORCIO}/operadores`,
];

async function probe(path: string): Promise<unknown | undefined> {
  const url = `${BASE}${path}`;
  try {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    const text = await res.text();
    const name = path.replace(/[^a-z0-9]+/gi, "_").replace(/^_|_$/g, "") || "root";
    await writeFile(`${OUT}/${name}.json`, text);
    if (!res.ok) {
      console.log(`  ${res.status}  ${path}`);
      return undefined;
    }
    const body: unknown = JSON.parse(text);
    const count = Array.isArray(body)
      ? body.length
      : typeof body === "object" && body !== null && Array.isArray((body as { [k: string]: unknown }).lineas)
        ? ((body as { lineas: unknown[] }).lineas).length
        : "?";
    console.log(`  ok   ${path}  (${count} elementos) -> ${OUT}/${name}.json`);
    return body;
  } catch (err) {
    console.log(`  FALLO ${path}: ${(err as Error).message}`);
    return undefined;
  }
}

/** Busca las paradas que nos interesan por nombre, sin depender del formato exacto. */
function findStops(body: unknown, needles: string[]): unknown[] {
  const hits: unknown[] = [];
  const norm = (s: string) =>
    s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const walk = (node: unknown) => {
    if (Array.isArray(node)) return node.forEach(walk);
    if (node === null || typeof node !== "object") return;
    const values = Object.values(node as Record<string, unknown>);
    const text = values.filter((v) => typeof v === "string").map((v) => norm(v as string)).join(" ");
    if (needles.some((n) => text.includes(norm(n)))) hits.push(node);
    values.forEach(walk);
  };
  walk(body);
  return hits;
}

await mkdir(OUT, { recursive: true });
console.log(`Sondeando ${BASE} (consorcio ${CONSORCIO})\n`);

let paradas: unknown;
for (const path of CANDIDATES) {
  const body = await probe(path);
  if (path.endsWith("/paradas")) paradas = body;
}

if (paradas) {
  const needles = ["telegrafia", "escuela ingenieria", "educacion", "ciencias"];
  const hits = findStops(paradas, needles);
  console.log(`\nParadas que parecen las nuestras (${hits.length}):`);
  console.log(JSON.stringify(hits, null, 2).slice(0, 4000));
}

console.log(`\nVuelcos en ${OUT}/ — revisalos para escribir el normalizador.`);
