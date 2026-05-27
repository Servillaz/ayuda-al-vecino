#!/usr/bin/env python3
"""
Descarga los datos actualizados de Google Sheets y los guarda como CSV locales.
Se ejecuta después del scraper en el workflow de GitHub Actions.

Credenciales (en orden de preferencia):
  1. Variable de entorno GOOGLE_CREDENTIALS_JSON  (GitHub Actions)
  2. Archivo local scripts/credentials.json        (desarrollo local)
"""

import csv, json, os, sys
from google.oauth2.service_account import Credentials
import gspread

SHEET_ID = os.environ.get("SHEET_ID", "1gNnACIdC4Er-GR-E96keujUrg2dyfCk9L2I_2HRHU9E")
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# ── Cargar credenciales ───────────────────────────────────────────────────────
_CREDS_ENV = os.environ.get("GOOGLE_CREDENTIALS_JSON")

if _CREDS_ENV:
    # Caso 1: variable de entorno (GitHub Actions)
    try:
        CREDS_JSON = json.loads(_CREDS_ENV)
    except json.JSONDecodeError:
        print("ERROR: GOOGLE_CREDENTIALS_JSON no es JSON válido", file=sys.stderr)
        sys.exit(1)
else:
    # Caso 2: archivo local (desarrollo) — NO se sube a GitHub (*.json en .gitignore)
    local_creds = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
    if not os.path.exists(local_creds):
        print(
            "ERROR: No se encontraron credenciales.\n"
            "  • En GitHub Actions: define el secret GOOGLE_CREDENTIALS_JSON\n"
            f"  • En local: crea el archivo {local_creds} con las credenciales de la service account",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(local_creds, encoding="utf-8") as f:
        CREDS_JSON = json.load(f)

HOJAS = ["municipios", "fondos", "calendario", "faqs"]

# ─────────────────────────────────────────────────────────────────────────────

def descargar_hoja(sheet, nombre_hoja, csv_path):
    try:
        hoja = sheet.worksheet(nombre_hoja)
    except gspread.exceptions.WorksheetNotFound:
        print(f"  ⚠️  Hoja '{nombre_hoja}' no encontrada — se omite")
        return False

    filas = hoja.get_all_values()
    if not filas:
        print(f"  ⚠️  Hoja '{nombre_hoja}' está vacía — se omite")
        return False

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerows(filas)

    print(f"  ✅ '{nombre_hoja}': {len(filas) - 1} filas descargadas → {csv_path}")
    return True


def main():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos-sheets")

    print("Conectando a Google Sheets...")
    creds  = Credentials.from_service_account_info(CREDS_JSON, scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        sheet = client.open_by_key(SHEET_ID)
        print(f"Conectado: {sheet.title}\n")
    except Exception as e:
        print(f"ERROR al conectar con Google Sheets: {e}", file=sys.stderr)
        sys.exit(1)

    ok = 0
    for nombre in HOJAS:
        path = os.path.join(base, f"{nombre}.csv")
        print(f"Descargando '{nombre}'...")
        if descargar_hoja(sheet, nombre, path):
            ok += 1

    print(f"\nDescarga completa: {ok}/{len(HOJAS)} hojas actualizadas.")


if __name__ == "__main__":
    main()
