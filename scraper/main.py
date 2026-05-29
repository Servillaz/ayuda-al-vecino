#!/usr/bin/env python3
"""
Ayuda al Vecino — Scraper Automático
Detecta fondos comunitarios en fuentes oficiales y actualiza Google Sheets.

Ejecutar localmente:
  pip install -r requirements.txt
  cp .env.example .env  # y llena las variables
  python scraper/main.py

En GitHub Actions se ejecuta automáticamente cada lunes.
"""

import os
import json
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import anthropic

# ─── FUENTES OFICIALES A MONITOREAR ──────────────────────────────
FUENTES = [
    # ── Nacionales ──
    {
        "nombre": "FOSIS — Programas y Servicios",
        "url": "https://www.fosis.gob.cl/es/que-hacemos/programas-y-servicios/",
        "params": {}
    },
    {
        "nombre": "SENAMA — Fondos y Concursos",
        "url": "https://www.senama.gob.cl/fondos",
        "params": {}
    },
    {
        "nombre": "MINVU — Programas y Subsidios",
        "url": "https://www.minvu.gob.cl/subsidios/",
        "params": {}
    },
    {
        "nombre": "SernamEG — Fondos y Programas",
        "url": "https://sernameg.gob.cl/programas/",
        "params": {}
    },
    {
        "nombre": "SEGEGOB — Fondo de Fortalecimiento Organizaciones",
        "url": "https://fondodefortalecimiento.gob.cl/",
        "params": {}
    },
    {
        "nombre": "SERCOTEC — Instrumentos de Apoyo",
        "url": "https://www.sercotec.cl/instrumentos/",
        "params": {}
    },
    {
        "nombre": "ChileAtiende — Bonos y Beneficios del Estado",
        "url": "https://www.chileatiende.gob.cl/temas/bonos-y-beneficios-del-estado",
        "params": {}
    },
    {
        "nombre": "SUBDERE — Fondos Regionales",
        "url": "https://www.subdere.gov.cl/programas",
        "params": {}
    },
    # ── Región Metropolitana ──
    {
        "nombre": "GORE Metropolitano — Fondos Concursables",
        "url": "https://www.gobiernosantiago.cl/fondos-concursables/",
        "params": {}
    },
    {
        "nombre": "Municipalidad de Santiago — Fondos Concursables",
        "url": "https://www.munistgo.cl/fondos/",
        "params": {}
    },
    {
        "nombre": "Municipalidad de Ñuñoa — Fondos 2026",
        "url": "https://www.nunoa.cl/fondos-concursables/",
        "params": {}
    },
    {
        "nombre": "Las Condes — Fondos Concursables Organizaciones",
        "url": "https://www.lascondes.cl/beneficios/financiamiento-de-proyectos/fondos-concursables/",
        "params": {}
    },
    {
        "nombre": "Providencia — Fondos para Organizaciones",
        "url": "https://www.providencia.cl/fondos-concursables/",
        "params": {}
    },
    {
        "nombre": "La Florida — Fondos Organizaciones",
        "url": "https://www.municipiodelaflorida.cl/fondos-concursables/",
        "params": {}
    },
    {
        "nombre": "Maipú — Fondos Concursables",
        "url": "https://municipalidadmaipu.cl/fondos-concursables/",
        "params": {}
    },
    {
        "nombre": "Puente Alto — Fondos y FONDEVE",
        "url": "https://www.mpuentealto.cl/fondos-concursables/",
        "params": {}
    },
]

HEADERS_HTTP = {
    "User-Agent": "Mozilla/5.0 (compatible; AyudaAlVecinoBot/1.0)",
    "Accept-Language": "es-CL,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# ─── CONEXIÓN A GOOGLE SHEETS ────────────────────────────────────

def conectar_sheets():
    sheet_id = os.environ.get("SHEET_ID")
    creds_raw = os.environ.get("GOOGLE_CREDENTIALS_JSON")

    if not sheet_id:
        raise ValueError("❌ SHEET_ID no está configurado")
    if not creds_raw:
        raise ValueError("❌ GOOGLE_CREDENTIALS_JSON no está configurado")

    creds_dict = json.loads(creds_raw)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    cliente = gspread.authorize(creds)
    return cliente.open_by_key(sheet_id)


def leer_fondos_actuales(sheet):
    hoja = sheet.worksheet("fondos")
    return hoja.get_all_records()


def actualizar_fondo_en_sheet(hoja, row_idx, campos_nuevos):
    """Actualiza campos específicos de una fila (row_idx es índice 0-based del array de datos)."""
    headers = hoja.row_values(1)
    for campo, valor in campos_nuevos.items():
        if campo in headers:
            col = headers.index(campo) + 1  # gspread usa base 1
            fila = row_idx + 2              # +1 header, +1 base-1
            hoja.update_cell(fila, col, valor)


def guardar_nuevos_fondos(sheet, nuevos):
    """Guarda fondos nuevos detectados en la pestaña 'Nuevos Fondos' para revisión."""
    try:
        hoja = sheet.worksheet("Nuevos Fondos")
    except gspread.exceptions.WorksheetNotFound:
        hoja = sheet.add_worksheet("Nuevos Fondos", rows=200, cols=12)
        hoja.append_row([
            "fecha_deteccion", "revisado", "nombre", "institucion",
            "abre", "cierra", "monto", "estado", "link", "fuente"
        ])

    for f in nuevos:
        hoja.append_row([
            datetime.now().strftime("%d/%m/%Y"),
            "PENDIENTE",
            f.get("nombre", ""),
            f.get("institucion", ""),
            f.get("abre", ""),
            f.get("cierra", ""),
            f.get("monto", ""),
            f.get("estado", ""),
            f.get("link", ""),
            f.get("fuente", ""),
        ])


def registrar_log(sheet, cambios, nuevos):
    """Escribe el resumen de cambios en la pestaña 'Log'."""
    try:
        hoja = sheet.worksheet("Log")
    except gspread.exceptions.WorksheetNotFound:
        hoja = sheet.add_worksheet("Log", rows=1000, cols=7)
        hoja.append_row(["fecha", "tipo", "fondo", "campo", "valor_nuevo", "fuente"])

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    for c in cambios:
        hoja.append_row([fecha, "ACTUALIZACIÓN", c["fondo"], c["campo"], c["valor"], c["fuente"]])

    for n in nuevos:
        hoja.append_row([fecha, "NUEVO DETECTADO", n.get("nombre", ""), "—", "—", n.get("fuente", "")])

    if not cambios and not nuevos:
        hoja.append_row([fecha, "SIN CAMBIOS", "—", "—", "—", "todas las fuentes"])


# ─── SCRAPING + PARSING CON CLAUDE ───────────────────────────────

def fetch_pagina(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS_HTTP, timeout=30)
        r.raise_for_status()
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"    ⚠️  Error al conectar con {url}: {e}")
        return None


def extraer_texto(html):
    """Extrae texto limpio del HTML eliminando ruido (nav, scripts, ads)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Intentar encontrar el contenido principal
    main = (
        soup.find("main")
        or soup.find(id=re.compile(r"content|main|fondos", re.I))
        or soup.find(class_=re.compile(r"content|main|fondos|entry", re.I))
    )
    texto = (main or soup.body or soup).get_text(separator="\n", strip=True)

    # Limitar para no exceder contexto de Claude
    return texto[:18000]


def parsear_con_claude(texto, nombre_fuente):
    """
    Usa Claude para extraer fondos estructurados desde texto libre.
    Al ser un modelo de lenguaje, es resiliente a cambios de estructura HTML.
    """
    cliente = anthropic.Anthropic()

    prompt = f"""Eres un asistente experto en fondos y beneficios comunitarios de Chile.

Analiza el siguiente texto del sitio oficial "{nombre_fuente}" y extrae TODOS los fondos, programas o beneficios de financiamiento comunitario que encuentres.

Para cada uno extrae:
- nombre: nombre completo del fondo o programa
- institucion: institución u organismo que lo ofrece
- abre: fecha de inicio de postulación. Formato "DD mmm YYYY" (ej: "15 mar 2026"). Si no está disponible: "Por confirmar"
- cierra: fecha de cierre de postulación. Mismo formato. Si no está: "Por confirmar"
- monto: monto disponible (ej: "Hasta $5.000.000", "Hasta 1.000 UF"). Si no hay info: "Sin información"
- estado: "abierto" si está recibiendo postulaciones ahora, "proximo" si aún no abre, "cerrado" si ya terminó
- link: URL específica del fondo si aparece en el texto, si no pon ""

Texto a analizar:
{texto}

IMPORTANTE: Responde ÚNICAMENTE con un JSON array válido. Sin explicaciones, sin markdown. Solo el JSON.
Si no encuentras fondos, responde: []

Ejemplo de formato correcto:
[{{"nombre":"Fondo X","institucion":"FOSIS","abre":"1 abr 2026","cierra":"30 may 2026","monto":"Hasta $2.000.000","estado":"abierto","link":"https://fosis.gob.cl/fondo-x"}}]"""

    try:
        respuesta = cliente.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        texto_json = respuesta.content[0].text.strip()
        # Limpiar posibles backticks de markdown
        texto_json = re.sub(r"^```(?:json)?\n?|\n?```$", "", texto_json).strip()
        return json.loads(texto_json)

    except json.JSONDecodeError as e:
        print(f"    ⚠️  Claude devolvió JSON inválido: {e}")
        return []
    except Exception as e:
        print(f"    ⚠️  Error llamando a Claude: {e}")
        return []


# ─── COMPARACIÓN FONDOS ───────────────────────────────────────────

def normalizar(texto):
    if not texto:
        return ""
    # Quitar acentos básicos y normalizar espacios
    reemplazos = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n","—":"-","–":"-"}
    t = texto.lower().strip()
    for orig, rep in reemplazos.items():
        t = t.replace(orig, rep)
    return re.sub(r"\s+", " ", t)


def similitud(a, b):
    """Porcentaje de palabras en común entre dos strings (0-1)."""
    wa = set(normalizar(a).split())
    wb = set(normalizar(b).split())
    if not wa or not wb:
        return 0
    return len(wa & wb) / max(len(wa), len(wb))


def encontrar_existente(nombre_scrapeado, fondos_actuales):
    """
    Busca si un fondo scrapeado coincide con uno ya existente en el Sheet.
    Retorna el índice (0-based) o -1 si no hay match.
    """
    for i, fondo in enumerate(fondos_actuales):
        sim = similitud(nombre_scrapeado, fondo.get("nombre", ""))
        if sim >= 0.65:
            return i
    return -1


def comparar(fondos_scrapeados, fondos_actuales, fuente):
    """
    Compara fondos scrapeados vs existentes.
    Retorna:
      cambios: lista de actualizaciones para aplicar en el Sheet
      nuevos:  fondos no reconocidos (van a pestaña de revisión)
    """
    CAMPOS = ["abre", "cierra", "monto", "estado"]
    cambios, nuevos = [], []

    for fs in fondos_scrapeados:
        idx = encontrar_existente(fs.get("nombre", ""), fondos_actuales)

        if idx >= 0:
            fe = fondos_actuales[idx]
            for campo in CAMPOS:
                val_nuevo = str(fs.get(campo, "")).strip()
                val_actual = str(fe.get(campo, "")).strip()
                if val_nuevo and val_nuevo not in ("Por confirmar", "Sin información") and val_nuevo != val_actual:
                    cambios.append({
                        "fondo": fe.get("nombre", ""),
                        "campo": campo,
                        "valor": val_nuevo,
                        "row_idx": idx,
                        "fuente": fuente,
                    })
        else:
            fs["fuente"] = fuente
            nuevos.append(fs)

    return cambios, nuevos


# ─── MAIN ────────────────────────────────────────────────────────

def main():
    separador = "=" * 55
    print(f"\n{separador}")
    print("🔍  Ayuda al Vecino — Scraper Automático")
    print(f"📅  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{separador}\n")

    # 1. Conectar a Google Sheets
    print("📊 Conectando a Google Sheets...")
    try:
        sheet = conectar_sheets()
        hoja_fondos = sheet.worksheet("fondos")
        fondos_actuales = leer_fondos_actuales(sheet)
        print(f"   ✅ {len(fondos_actuales)} fondos existentes cargados\n")
    except Exception as e:
        print(f"   ❌ No se pudo conectar: {e}")
        return

    todos_cambios = []
    todos_nuevos = []

    # 2. Procesar cada fuente
    for fuente in FUENTES:
        print(f"🌐 {fuente['nombre']}")

        html = fetch_pagina(fuente["url"], fuente.get("params"))
        if not html:
            print("   ❌ Sin respuesta — saltando\n")
            continue

        texto = extraer_texto(html)
        print(f"   📝 {len(texto):,} caracteres de texto extraídos")

        fondos_detectados = parsear_con_claude(texto, fuente["nombre"])
        print(f"   🤖 Claude detectó {len(fondos_detectados)} fondos")

        cambios, nuevos = comparar(fondos_detectados, fondos_actuales, fuente["nombre"])
        todos_cambios.extend(cambios)
        todos_nuevos.extend(nuevos)

        print(f"   ↻  {len(cambios)} actualizaciones | 🆕 {len(nuevos)} fondos nuevos\n")
        time.sleep(3)  # cortesía entre requests

    # 3. Aplicar actualizaciones al Sheet
    if todos_cambios:
        print(f"📝 Aplicando {len(todos_cambios)} actualizaciones...")
        for cambio in todos_cambios:
            try:
                actualizar_fondo_en_sheet(hoja_fondos, cambio["row_idx"], {cambio["campo"]: cambio["valor"]})
                fondo_corto = cambio["fondo"][:45]
                print(f"   ✅ {fondo_corto} → {cambio['campo']}: {cambio['valor']}")
            except Exception as e:
                print(f"   ⚠️  Error actualizando {cambio['fondo'][:30]}: {e}")
    else:
        print("✅ Sin cambios en fondos existentes")

    # 4. Guardar fondos nuevos para revisión manual
    if todos_nuevos:
        print(f"\n🆕 {len(todos_nuevos)} fondos nuevos → guardando en pestaña 'Nuevos Fondos'")
        guardar_nuevos_fondos(sheet, todos_nuevos)
        for n in todos_nuevos:
            print(f"   • {n.get('nombre', 'Sin nombre')[:55]}")

    # 5. Registrar log
    registrar_log(sheet, todos_cambios, todos_nuevos)

    # 6. Resumen final
    print(f"\n{separador}")
    print("✅ Proceso completado")
    print(f"   Actualizaciones aplicadas : {len(todos_cambios)}")
    print(f"   Fondos nuevos (revisar)   : {len(todos_nuevos)}")
    print(f"{separador}\n")


if __name__ == "__main__":
    main()
