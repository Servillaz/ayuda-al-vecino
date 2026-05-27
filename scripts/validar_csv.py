#!/usr/bin/env python3
"""Valida la integridad de todos los CSVs del proyecto Ayuda al Vecino."""
import csv, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos-sheets")

MUNICIPIOS_HEADERS = [
    "municipio_id", "municipio_nombre", "region", "pop", "web",
    "cat", "cat_emoji", "titulo", "desc", "como", "url"
]

errors   = []
warnings = []

# ── municipios.csv ────────────────────────────────────────────────────────────
path = os.path.join(BASE, "municipios.csv")
if not os.path.exists(path):
    errors.append("❌ municipios.csv no encontrado")
else:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = [h for h in (reader.fieldnames or []) if h]
        rows = list(reader)

    if headers != MUNICIPIOS_HEADERS:
        errors.append(f"❌ municipios.csv: headers incorrectos\n   Esperado: {MUNICIPIOS_HEADERS}\n   Actual  : {headers}")
    elif len(rows) < 50:
        errors.append(f"❌ municipios.csv: muy pocas filas ({len(rows)}), probablemente corrupto")
    else:
        print(f"✅ municipios.csv: {len(rows)} filas")

    seen_ids   = {}
    munis_set  = set()
    empty_rows = 0

    for i, row in enumerate(rows, 2):
        mid = (row.get("municipio_id") or "").strip()
        if not mid:
            empty_rows += 1
            continue
        munis_set.add(mid)

        # Detectar IDs duplicados con título diferente (duplicado real)
        titulo = (row.get("titulo") or "").strip()
        key    = (mid, titulo)
        if key in seen_ids:
            warnings.append(f"⚠️  municipios.csv línea {i}: beneficio duplicado '{titulo}' en {mid}")
        seen_ids[key] = i

        url = (row.get("url") or "").strip()
        if url and not url.startswith("http"):
            warnings.append(f"⚠️  municipios.csv línea {i}: URL sin protocolo: {url[:60]}")

        web = (row.get("web") or "").strip()
        if web and not web.startswith("http"):
            warnings.append(f"⚠️  municipios.csv línea {i}: web sin protocolo: {web[:60]}")

    if empty_rows:
        warnings.append(f"⚠️  municipios.csv: {empty_rows} filas con municipio_id vacío")

    print(f"   Municipios únicos : {len(munis_set)}")
    print(f"   Beneficios totales: {len(rows)}")

# ── fondos.csv ────────────────────────────────────────────────────────────────
path = os.path.join(BASE, "fondos.csv")
if not os.path.exists(path):
    errors.append("❌ fondos.csv no encontrado")
else:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    abiertos = sum(1 for r in rows if (r.get("estado") or "").strip() == "abierto")
    print(f"✅ fondos.csv: {len(rows)} fondos ({abiertos} abiertos)")

# ── calendario.csv ────────────────────────────────────────────────────────────
path = os.path.join(BASE, "calendario.csv")
if not os.path.exists(path):
    warnings.append("⚠️  calendario.csv no encontrado")
else:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"✅ calendario.csv: {len(rows)} eventos")

# ── faqs.csv ──────────────────────────────────────────────────────────────────
path = os.path.join(BASE, "faqs.csv")
if not os.path.exists(path):
    warnings.append("⚠️  faqs.csv no encontrado")
else:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"✅ faqs.csv: {len(rows)} preguntas")

# ── Resultado ─────────────────────────────────────────────────────────────────
print()
for w in warnings:
    print(w)

if errors:
    print()
    for e in errors:
        print(e)
    print(f"\n🚫 {len(errors)} error(es) encontrado(s). Corrige antes de hacer commit.")
    sys.exit(1)

if warnings:
    print(f"\n✅ CSVs válidos con {len(warnings)} advertencia(s) menores. Commit permitido.")
else:
    print("✅ Todos los CSVs en perfecto estado.")

sys.exit(0)
