#!/usr/bin/env python3
"""
Reescribe las descripciones de beneficios municipales en lenguaje simple.
Usa Claude Haiku para transformar texto burocrático en lenguaje humano.

Corre en GitHub Actions con ANTHROPIC_API_KEY disponible.
También actualiza el Google Sheet con el contenido mejorado.

Uso local (necesita ANTHROPIC_API_KEY):
  ANTHROPIC_API_KEY=sk-... python scripts/reescribir_descripciones.py
"""

import csv, json, os, sys, time
from pathlib import Path
from google.oauth2.service_account import Credentials
import gspread
import anthropic

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SHEET_ID = os.environ.get("SHEET_ID", "1gNnACIdC4Er-GR-E96keujUrg2dyfCk9L2I_2HRHU9E")
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets"]
CSV_PATH = Path(__file__).parent.parent / "datos-sheets" / "municipios.csv"

# ── Credenciales Google ───────────────────────────────────────────────────────
def cargar_credenciales():
    env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if env:
        return json.loads(env)
    local = Path(__file__).parent / "credentials.json"
    if local.exists():
        with open(local, encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError("No se encontraron credenciales Google.")

# ── Claude ────────────────────────────────────────────────────────────────────
def reescribir_beneficio(cliente, municipio, titulo, desc, como, cat):
    """Reescribe desc y como en lenguaje simple y cercano."""
    prompt = f"""Reescribe en lenguaje simple y cercano este beneficio municipal chileno.

Municipio: {municipio}
Categoría: {cat}
Título: {titulo}
Descripción actual: {desc}
Cómo acceder actual: {como}

Reglas:
- Habla de "tú/tu" directamente
- Sin referencias a leyes, resoluciones ni términos técnicos
- Máximo 120 caracteres para la descripción
- Máximo 100 caracteres para el cómo acceder
- Empieza la descripción con el beneficio concreto: "Puedes...", "Tienes derecho a...", "Tu municipio te da..."
- El cómo debe decir qué hacer, dónde ir o qué traer, en una sola acción

Responde SOLO con JSON válido, sin explicaciones:
{{"desc": "...", "como": "..."}}"""

    try:
        r = cliente.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = r.content[0].text.strip()
        import re
        texto = re.sub(r"^```(?:json)?\n?|\n?```$", "", texto).strip()
        data = json.loads(texto)
        return data.get("desc", desc), data.get("como", como)
    except Exception as e:
        print(f"    ⚠️  Error Claude: {e}")
        return desc, como

# ── Detectar si necesita reescritura ─────────────────────────────────────────
PALABRAS_BUROCRATICAS = [
    "instrumento", "personalidad jurídica", "ley 19", "ley 20", "artículo",
    "resolución", "decreto", "reglamento", "postulantes", "beneficiarios elegibles",
    "modalidad", "cofinanciamiento", "organismo", "entidad postulante",
    "acreditar", "en conformidad", "vigencia", "estamento"
]

def es_burocratico(texto):
    texto_l = texto.lower()
    return sum(1 for p in PALABRAS_BUROCRATICAS if p in texto_l) >= 1

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=== Reescritura de descripciones — Ayuda al Vecino ===\n")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY no está definido.", file=sys.stderr)
        sys.exit(1)

    cliente = anthropic.Anthropic(api_key=api_key)

    # Leer CSV
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    print(f"Beneficios a revisar: {len(rows)}")

    # Detectar cuáles necesitan reescritura
    pendientes = [r for r in rows if es_burocratico(r.get("desc","")) or es_burocratico(r.get("como",""))]
    print(f"Con lenguaje burocrático: {len(pendientes)}\n")

    if not pendientes:
        print("✅ Todas las descripciones ya están en lenguaje simple.")
        return

    # Reescribir
    reescritos = 0
    for i, row in enumerate(rows):
        if not (es_burocratico(row.get("desc","")) or es_burocratico(row.get("como",""))):
            continue

        print(f"  [{row['municipio_id']}] {row['titulo'][:45]}...")
        nueva_desc, nuevo_como = reescribir_beneficio(
            cliente,
            row["municipio_nombre"],
            row["titulo"],
            row["desc"],
            row["como"],
            row["cat"]
        )
        rows[i]["desc"] = nueva_desc
        rows[i]["como"] = nuevo_como
        reescritos += 1

        if reescritos % 10 == 0:
            print(f"  Progreso: {reescritos}/{len(pendientes)} reescritos")

        time.sleep(0.3)  # cortesía con la API

    print(f"\n✅ Reescritos: {reescritos}")

    # Guardar CSV local
    campos = list(rows[0].keys())
    with open(CSV_PATH, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV guardado: {CSV_PATH}")

    # Actualizar Google Sheets
    print("\nActualizando Google Sheets...")
    try:
        creds  = Credentials.from_service_account_info(cargar_credenciales(), scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet  = client.open_by_key(SHEET_ID)
        hoja   = sheet.worksheet("municipios")

        headers = hoja.row_values(1)
        col_desc = headers.index("desc") + 1
        col_como = headers.index("como") + 1

        all_ids  = hoja.col_values(1)  # municipio_id column

        for row in rows:
            if not (es_burocratico(row.get("desc","")) or es_burocratico(row.get("como",""))):
                continue
            try:
                sheet_row = all_ids.index(row["municipio_id"])  # may fail if not unique
                # Best effort — update first match
                hoja.update_cell(sheet_row + 1, col_desc, row["desc"])
                hoja.update_cell(sheet_row + 1, col_como, row["como"])
                time.sleep(0.4)
            except Exception:
                pass  # Skip if row can't be located

        print("✅ Google Sheets actualizado")
    except Exception as e:
        print(f"⚠️  No se pudo actualizar Sheets: {e}")

    print("\nListo. Haz commit del municipios.csv actualizado.")

if __name__ == "__main__":
    main()
