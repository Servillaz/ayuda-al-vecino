#!/usr/bin/env python3
"""
Ayuda al Vecino — Scraper profundo de beneficios personales por municipio
Visita las páginas DIDECO / Desarrollo Social de cada municipio de la RM
y usa Claude para extraer beneficios personales estructurados.

Ejecutar:
  python scraper/scraper_municipios_rm.py

Corre mensualmente en GitHub Actions (.github/workflows/actualizar-municipios.yml).
"""

import os, json, re, time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
import gspread
import anthropic

# ─── CONFIG ──────────────────────────────────────────────────────────────────
SHEET_ID = os.environ.get("SHEET_ID", "1gNnACIdC4Er-GR-E96keujUrg2dyfCk9L2I_2HRHU9E")
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets"]
REGION   = "Región Metropolitana"

CATS_VALIDAS = [
    "Salud", "Educación y Becas", "Adulto Mayor",
    "Social y Legal", "Deporte y Cultura", "Vivienda",
    "Emprendimiento", "Emergencias"
]

CAT_EMOJIS = {
    "Salud": "🏥",
    "Educación y Becas": "🎓",
    "Adulto Mayor": "👴",
    "Social y Legal": "⚖️",
    "Deporte y Cultura": "🎭",
    "Vivienda": "🏠",
    "Emprendimiento": "💼",
    "Emergencias": "🚨",
}

HEADERS_HTTP = {
    "User-Agent": "Mozilla/5.0 (compatible; AyudaAlVecinoBot/1.0; +https://servillaz.github.io/ayuda-al-vecino/)",
    "Accept-Language": "es-CL,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─── MUNICIPIOS RM — URLs de beneficios/DIDECO ───────────────────────────────
# Cada entrada tiene: id, nombre, pop (hab.), web principal, y lista de
# páginas a scrapear (en orden de riqueza de contenido esperada).
MUNICIPIOS_RM = [
    {"id": "santiago",       "nombre": "Santiago",          "pop": "404.000 hab.", "web": "https://www.munistgo.cl",
     "paginas": ["https://www.munistgo.cl/beneficios-2/", "https://www.munistgo.cl/servicios-sociales/", "https://www.munistgo.cl/adulto-mayor/"]},
    {"id": "maipu",          "nombre": "Maipú",             "pop": "600.000 hab.", "web": "https://municipalidadmaipu.cl",
     "paginas": ["https://municipalidadmaipu.cl/direccion-de-desarrollo-comunitario-dideco", "https://municipalidadmaipu.cl/beneficios-y-estudios", "https://municipalidadmaipu.cl/adulto-mayor"]},
    {"id": "puentealto",     "nombre": "Puente Alto",       "pop": "640.000 hab.", "web": "https://www.mpuentealto.cl",
     "paginas": ["https://www.mpuentealto.cl/estructura/direccion-social/", "https://www.mpuentealto.cl/beneficios/", "https://www.mpuentealto.cl/adultos-mayores/"]},
    {"id": "laflorida",      "nombre": "La Florida",        "pop": "366.000 hab.", "web": "https://www.municipiodelaflorida.cl",
     "paginas": ["https://www.municipiodelaflorida.cl/dideco", "https://www.municipiodelaflorida.cl/beneficios", "https://www.municipiodelaflorida.cl/adultos-mayores"]},
    {"id": "penalolen",      "nombre": "Peñalolén",         "pop": "236.000 hab.", "web": "https://www.penalolen.cl",
     "paginas": ["https://www.penalolen.cl/dideco/", "https://www.penalolen.cl/adultos-mayores/", "https://www.penalolen.cl/salud/"]},
    {"id": "sanbernardo",    "nombre": "San Bernardo",      "pop": "317.000 hab.", "web": "https://www.msb.cl",
     "paginas": ["https://www.msb.cl/dideco/", "https://www.msb.cl/beneficios/", "https://www.msb.cl/adultos-mayores/"]},
    {"id": "quilicura",      "nombre": "Quilicura",         "pop": "230.000 hab.", "web": "https://www.quilicura.cl",
     "paginas": ["https://www.quilicura.cl/vecinos/", "https://www.quilicura.cl/salud/", "https://www.quilicura.cl/educacion/"]},
    {"id": "recoleta",       "nombre": "Recoleta",          "pop": "172.000 hab.", "web": "https://www.recoleta.cl",
     "paginas": ["https://www.recoleta.cl/dideco/", "https://www.recoleta.cl/servicios-vecinos/", "https://www.recoleta.cl/adultos-mayores/"]},
    {"id": "pudahuel",       "nombre": "Pudahuel",          "pop": "239.000 hab.", "web": "https://www.pudahuel.cl",
     "paginas": ["https://www.pudahuel.cl/dideco/", "https://www.pudahuel.cl/beneficios/", "https://www.pudahuel.cl/adultos-mayores/"]},
    {"id": "cerronavia",     "nombre": "Cerro Navia",       "pop": "148.000 hab.", "web": "https://www.cerronavia.cl",
     "paginas": ["https://www.cerronavia.cl/dideco/", "https://www.cerronavia.cl/beneficios/", "https://www.cerronavia.cl/adultos-mayores/"]},
    {"id": "providencia",    "nombre": "Providencia",       "pop": "143.000 hab.", "web": "https://www.providencia.cl",
     "paginas": ["https://www.providencia.cl/personas/vecinos/", "https://www.providencia.cl/personas/adulto-mayor/", "https://www.providencia.cl/personas/salud/"]},
    {"id": "lascondes",      "nombre": "Las Condes",        "pop": "294.000 hab.", "web": "https://www.lascondes.cl",
     "paginas": ["https://www.lascondes.cl/vecinos/", "https://www.lascondes.cl/vecinos/beneficios-sociales/", "https://www.lascondes.cl/salud/"]},
    {"id": "vitacura",       "nombre": "Vitacura",          "pop": "88.000 hab.",  "web": "https://www.vitacura.cl",
     "paginas": ["https://vitacura.cl/vecinos/beneficios-sociales/", "https://vitacura.cl/salud/", "https://vitacura.cl/educacion/"]},
    {"id": "nunoa",          "nombre": "Ñuñoa",             "pop": "208.000 hab.", "web": "https://www.nunoa.cl",
     "paginas": ["https://www.nunoa.cl/vecinos/", "https://www.nunoa.cl/adulto-mayor/", "https://www.nunoa.cl/salud/"]},
    {"id": "lobarnechea",    "nombre": "Lo Barnechea",      "pop": "106.000 hab.", "web": "https://www.lobarnechea.cl",
     "paginas": ["https://www.lobarnechea.cl/vecinos/", "https://www.lobarnechea.cl/adultos-mayores/", "https://www.lobarnechea.cl/salud/"]},
    {"id": "elbosque",       "nombre": "El Bosque",         "pop": "175.000 hab.", "web": "https://www.municipalidad-elbosque.cl",
     "paginas": ["https://www.municipalidad-elbosque.cl/dideco/", "https://www.municipalidad-elbosque.cl/beneficios/", "https://www.municipalidad-elbosque.cl/adultos-mayores/"]},
    {"id": "renca",          "nombre": "Renca",             "pop": "148.000 hab.", "web": "https://www.renca.cl",
     "paginas": ["https://www.renca.cl/dideco/", "https://www.renca.cl/beneficios/", "https://www.renca.cl/adultos-mayores/"]},
    {"id": "conchali",       "nombre": "Conchalí",          "pop": "134.000 hab.", "web": "https://www.conchali.cl",
     "paginas": ["https://www.conchali.cl/dideco/", "https://www.conchali.cl/beneficios/", "https://www.conchali.cl/adultos-mayores/"]},
    {"id": "independencia",  "nombre": "Independencia",     "pop": "100.000 hab.", "web": "https://www.independencia.cl",
     "paginas": ["https://www.independencia.cl/dideco/", "https://www.independencia.cl/beneficios/", "https://www.independencia.cl/adultos-mayores/"]},
    {"id": "quintanormal",   "nombre": "Quinta Normal",     "pop": "103.000 hab.", "web": "https://www.quintanormal.cl",
     "paginas": ["https://www.quintanormal.cl/dideco/", "https://www.quintanormal.cl/beneficios/", "https://www.quintanormal.cl/adultos-mayores/"]},
    {"id": "macul",          "nombre": "Macul",             "pop": "112.000 hab.", "web": "https://www.macul.cl",
     "paginas": ["https://www.macul.cl/dideco/", "https://www.macul.cl/beneficios/", "https://www.macul.cl/adultos-mayores/"]},
    {"id": "lareina",        "nombre": "La Reina",          "pop": "93.000 hab.",  "web": "https://www.lareina.cl",
     "paginas": ["https://www.lareina.cl/vecinos/", "https://www.lareina.cl/adultos-mayores/", "https://www.lareina.cl/salud/"]},
    {"id": "sanjoaquin",     "nombre": "San Joaquín",       "pop": "98.000 hab.",  "web": "https://www.sanjoaquin.cl",
     "paginas": ["https://www.sanjoaquin.cl/dideco/", "https://www.sanjoaquin.cl/beneficios/", "https://www.sanjoaquin.cl/adultos-mayores/"]},
    {"id": "loespejo",       "nombre": "Lo Espejo",         "pop": "107.000 hab.", "web": "https://www.loespejo.cl",
     "paginas": ["https://www.loespejo.cl/dideco/", "https://www.loespejo.cl/beneficios/", "https://www.loespejo.cl/adultos-mayores/"]},
    {"id": "loprado",        "nombre": "Lo Prado",          "pop": "103.000 hab.", "web": "https://www.loprado.cl",
     "paginas": ["https://www.loprado.cl/dideco/", "https://www.loprado.cl/beneficios/", "https://www.loprado.cl/adultos-mayores/"]},
    {"id": "lagranja",       "nombre": "La Granja",         "pop": "130.000 hab.", "web": "https://www.lagranja.cl",
     "paginas": ["https://www.lagranja.cl/dideco/", "https://www.lagranja.cl/beneficios/", "https://www.lagranja.cl/adultos-mayores/"]},
    {"id": "sanmiguel",      "nombre": "San Miguel",        "pop": "107.000 hab.", "web": "https://www.sanmiguel.cl",
     "paginas": ["https://www.sanmiguel.cl/dideco/", "https://www.sanmiguel.cl/beneficios/", "https://www.sanmiguel.cl/adultos-mayores/"]},
    {"id": "lapintana",      "nombre": "La Pintana",        "pop": "190.000 hab.", "web": "https://www.lapintana.cl",
     "paginas": ["https://www.lapintana.cl/dideco/", "https://www.lapintana.cl/beneficios/", "https://www.lapintana.cl/adultos-mayores/"]},
    {"id": "estacioncentral","nombre": "Estación Central",  "pop": "148.000 hab.", "web": "https://www.estacioncentral.cl",
     "paginas": ["https://www.estacioncentral.cl/dideco/", "https://www.estacioncentral.cl/beneficios/", "https://www.estacioncentral.cl/adultos-mayores/"]},
    {"id": "lacisterna",     "nombre": "La Cisterna",       "pop": "91.000 hab.",  "web": "https://www.lacisterna.cl",
     "paginas": ["https://www.lacisterna.cl/dideco/", "https://www.lacisterna.cl/beneficios/", "https://www.lacisterna.cl/adultos-mayores/"]},
    {"id": "huechuraba",     "nombre": "Huechuraba",        "pop": "98.000 hab.",  "web": "https://www.huechuraba.cl",
     "paginas": ["https://www.huechuraba.cl/dideco/", "https://www.huechuraba.cl/beneficios/", "https://www.huechuraba.cl/adultos-mayores/"]},
    {"id": "pac",            "nombre": "Pedro Aguirre Cerda","pop": "114.000 hab.", "web": "https://www.mpac.cl",
     "paginas": ["https://www.mpac.cl/dideco/", "https://www.mpac.cl/beneficios/", "https://www.mpac.cl/adultos-mayores/"]},
    {"id": "sanramon",       "nombre": "San Ramón",         "pop": "100.000 hab.", "web": "https://www.municipalidadsanramon.cl",
     "paginas": ["https://www.municipalidadsanramon.cl/dideco/", "https://www.municipalidadsanramon.cl/beneficios/"]},
    {"id": "cerrillos",      "nombre": "Cerrillos",         "pop": "82.000 hab.",  "web": "https://www.cerrillos.cl",
     "paginas": ["https://www.cerrillos.cl/dideco/", "https://www.cerrillos.cl/beneficios/", "https://www.cerrillos.cl/adultos-mayores/"]},
    {"id": "colina",         "nombre": "Colina",            "pop": "133.000 hab.", "web": "https://www.municipalidadcolina.cl",
     "paginas": ["https://www.municipalidadcolina.cl/dideco/", "https://www.municipalidadcolina.cl/beneficios/"]},
    {"id": "lampa",          "nombre": "Lampa",             "pop": "93.000 hab.",  "web": "https://www.lampa.cl",
     "paginas": ["https://www.lampa.cl/dideco/", "https://www.lampa.cl/beneficios/"]},
    {"id": "buin",           "nombre": "Buin",              "pop": "82.000 hab.",  "web": "https://www.buin.cl",
     "paginas": ["https://www.buin.cl/dideco/", "https://www.buin.cl/beneficios/"]},
    {"id": "paine",          "nombre": "Paine",             "pop": "72.000 hab.",  "web": "https://www.paine.cl",
     "paginas": ["https://www.paine.cl/dideco/", "https://www.paine.cl/beneficios/"]},
    {"id": "melipilla",      "nombre": "Melipilla",         "pop": "120.000 hab.", "web": "https://www.melipilla.cl",
     "paginas": ["https://www.melipilla.cl/dideco/", "https://www.melipilla.cl/beneficios/"]},
    {"id": "talagante",      "nombre": "Talagante",         "pop": "77.000 hab.",  "web": "https://www.talagante.cl",
     "paginas": ["https://www.talagante.cl/dideco/", "https://www.talagante.cl/beneficios/"]},
    {"id": "penaflor",       "nombre": "Peñaflor",          "pop": "88.000 hab.",  "web": "https://www.penaflor.cl",
     "paginas": ["https://www.penaflor.cl/dideco/", "https://www.penaflor.cl/beneficios/"]},
    {"id": "padrehurtado",   "nombre": "Padre Hurtado",     "pop": "69.000 hab.",  "web": "https://www.padrehurtado.cl",
     "paginas": ["https://www.padrehurtado.cl/dideco/", "https://www.padrehurtado.cl/beneficios/"]},
    {"id": "caleradetango",  "nombre": "Calera de Tango",   "pop": "31.000 hab.",  "web": "https://www.caleradetango.cl",
     "paginas": ["https://www.caleradetango.cl/dideco/", "https://www.caleradetango.cl/beneficios/"]},
    {"id": "islademaipo",    "nombre": "Isla de Maipo",     "pop": "34.000 hab.",  "web": "https://www.islademaipo.cl",
     "paginas": ["https://www.islademaipo.cl/dideco/", "https://www.islademaipo.cl/beneficios/"]},
    {"id": "elmonte",        "nombre": "El Monte",          "pop": "32.000 hab.",  "web": "https://www.elmonte.cl",
     "paginas": ["https://www.elmonte.cl/dideco/", "https://www.elmonte.cl/beneficios/"]},
    {"id": "alhue",          "nombre": "Alhué",             "pop": "4.800 hab.",   "web": "https://www.alhue.cl",
     "paginas": ["https://www.alhue.cl/dideco/", "https://www.alhue.cl/beneficios/"]},
    {"id": "curacavi",       "nombre": "Curacaví",          "pop": "27.000 hab.",  "web": "https://www.curacavi.cl",
     "paginas": ["https://www.curacavi.cl/dideco/", "https://www.curacavi.cl/beneficios/"]},
    {"id": "mariapinto",     "nombre": "María Pinto",       "pop": "13.000 hab.",  "web": "https://www.mariapinto.cl",
     "paginas": ["https://www.mariapinto.cl/dideco/", "https://www.mariapinto.cl/beneficios/"]},
    {"id": "sanpedro",       "nombre": "San Pedro",         "pop": "9.000 hab.",   "web": "https://www.municipalidadsanpedro.cl",
     "paginas": ["https://www.municipalidadsanpedro.cl/dideco/", "https://www.municipalidadsanpedro.cl/beneficios/"]},
    {"id": "pirque",         "nombre": "Pirque",            "pop": "16.000 hab.",  "web": "https://www.pirque.cl",
     "paginas": ["https://www.pirque.cl/dideco/", "https://www.pirque.cl/beneficios/"]},
    {"id": "sanjosedemaipo", "nombre": "San José de Maipo", "pop": "14.000 hab.",  "web": "https://www.sanjosedemaipo.cl",
     "paginas": ["https://www.sanjosedemaipo.cl/direcciones-municipales/direccion-de-desarrollo-comunitario/", "https://www.sanjosedemaipo.cl/beneficios/"]},
    {"id": "tiltil",         "nombre": "Tiltil",            "pop": "18.000 hab.",  "web": "https://www.tiltil.cl",
     "paginas": ["https://www.tiltil.cl/dideco/", "https://www.tiltil.cl/beneficios/"]},
]

# ─── CREDENCIALES ────────────────────────────────────────────────────────────
def cargar_credenciales():
    import json
    from pathlib import Path
    env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if env:
        return json.loads(env)
    local = Path(__file__).parent / "credentials.json"
    if local.exists():
        with open(local, encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError("No se encontraron credenciales Google.")

def conectar_sheets():
    creds = Credentials.from_service_account_info(cargar_credenciales(), scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

# ─── SCRAPING ────────────────────────────────────────────────────────────────
def fetch_pagina(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS_HTTP, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and len(r.text) > 500:
            return r.text
        return None
    except Exception:
        return None

def extraer_texto(html, max_chars=15000):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "form", "aside"]):
        tag.decompose()
    main = soup.find("main") or soup.find(id="content") or soup.find(class_="content")
    texto = (main or soup.body or soup).get_text(separator="\n", strip=True)
    return texto[:max_chars]

# ─── CLAUDE ──────────────────────────────────────────────────────────────────
def extraer_beneficios_con_claude(texto, municipio_nombre, url_fuente, cats_existentes):
    cliente = anthropic.Anthropic()

    cats_str = "\n".join(f"- {c}" for c in CATS_VALIDAS)
    existentes_str = ", ".join(f'"{c}"' for c in cats_existentes) if cats_existentes else "(ninguno aún)"

    prompt = f"""Eres un experto en beneficios sociales municipales de Chile.

Analiza el siguiente texto de la página web de la Municipalidad de {municipio_nombre} y extrae TODOS los beneficios, programas y servicios disponibles para los vecinos.

CATEGORÍAS VÁLIDAS (usa solo estas):
{cats_str}

Beneficios que ya tenemos de este municipio (NO los repitas): {existentes_str}

Para cada beneficio nuevo extrae:
- titulo: nombre corto del beneficio (máx 60 caracteres)
- desc: qué es y para quién es, en lenguaje simple (máx 150 caracteres)
- como: cómo acceder o postular (máx 120 caracteres)
- cat: categoría (una de la lista)
- url: URL específica si aparece en el texto, si no usa "{url_fuente}"

Texto de la página:
{texto}

Responde ÚNICAMENTE con un JSON array. Sin explicaciones. Sin markdown.
Si no encuentras beneficios nuevos o el texto no tiene información útil, responde: []

Ejemplo:
[{{"titulo":"Beca escolar municipal","desc":"Apoyo económico para estudiantes en situación vulnerable de {municipio_nombre}.","como":"Postula en la DIDECO con certificado de matrícula y RSH.","cat":"Educación y Becas","url":"{url_fuente}"}}]"""

    try:
        r = cliente.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        texto_json = r.content[0].text.strip()
        texto_json = re.sub(r"^```(?:json)?\n?|\n?```$", "", texto_json).strip()
        beneficios = json.loads(texto_json)
        # Validar y limpiar
        validos = []
        for b in beneficios:
            if isinstance(b, dict) and b.get("titulo") and b.get("cat") in CATS_VALIDAS:
                b["cat_emoji"] = CAT_EMOJIS.get(b["cat"], "✅")
                b.setdefault("url", url_fuente)
                b.setdefault("como", "Consulta en la Municipalidad.")
                validos.append(b)
        return validos
    except Exception as e:
        print(f"    ⚠️  Claude error: {e}")
        return []

# ─── SHEETS ──────────────────────────────────────────────────────────────────
def leer_beneficios_existentes(sheet, municipio_id):
    hoja = sheet.worksheet("municipios")
    rows = hoja.get_all_records()
    return [r for r in rows if r.get("municipio_id") == municipio_id]

def agregar_beneficios(sheet, municipio, nuevos):
    hoja = sheet.worksheet("municipios")
    for b in nuevos:
        fila = [
            municipio["id"],
            municipio["nombre"],
            REGION,
            municipio["pop"],
            municipio["web"],
            b["cat"],
            b["cat_emoji"],
            b["titulo"],
            b["desc"],
            b["como"],
            b["url"],
        ]
        hoja.append_row(fila, value_input_option="RAW")
        time.sleep(0.5)  # evitar rate limit de Sheets API

# ─── DEDUPLICACIÓN ───────────────────────────────────────────────────────────
def normalizar(t):
    t = t.lower().strip()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)

def es_duplicado(titulo_nuevo, beneficios_existentes, umbral=0.6):
    n = set(normalizar(titulo_nuevo).split())
    for b in beneficios_existentes:
        e = set(normalizar(b.get("titulo","")).split())
        if n and e:
            sim = len(n & e) / max(len(n), len(e))
            if sim >= umbral:
                return True
    return False

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    sep = "=" * 58
    print(f"\n{sep}")
    print("🏘️  Ayuda al Vecino — Scraper DIDECO Municipios RM")
    print(f"📅  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{sep}\n")

    print("📊 Conectando a Google Sheets...")
    try:
        sheet = conectar_sheets()
        print("   ✅ Conectado\n")
    except Exception as e:
        print(f"   ❌ {e}")
        return

    total_nuevos = 0
    total_municipios_con_datos = 0

    for muni in MUNICIPIOS_RM:
        mid   = muni["id"]
        nombre = muni["nombre"]
        print(f"🏛️  {nombre}")

        # Leer beneficios existentes para este municipio
        existentes = leer_beneficios_existentes(sheet, mid)
        titulos_existentes = [e.get("titulo","") for e in existentes]
        print(f"   Actuales: {len(existentes)} beneficios")

        # Scrapear páginas
        texto_total = ""
        for url in muni["paginas"][:3]:  # máx 3 páginas por municipio
            html = fetch_pagina(url)
            if html:
                t = extraer_texto(html)
                if len(t) > 300:
                    texto_total += f"\n\n--- Página: {url} ---\n{t}"
                    print(f"   📄 {url[:60]} ({len(t):,} chars)")
            time.sleep(1)

        if not texto_total.strip():
            # Fallback: intentar homepage
            html = fetch_pagina(muni["web"])
            if html:
                texto_total = extraer_texto(html)
                print(f"   📄 Fallback homepage ({len(texto_total):,} chars)")

        if len(texto_total) < 200:
            print("   ⚠️  Sin contenido útil — saltando\n")
            continue

        # Extraer con Claude
        nuevos = extraer_beneficios_con_claude(
            texto_total[:18000], nombre,
            muni["paginas"][0], titulos_existentes
        )

        # Filtrar duplicados
        nuevos_reales = [b for b in nuevos if not es_duplicado(b["titulo"], existentes)]

        if nuevos_reales:
            print(f"   🆕 {len(nuevos_reales)} nuevos beneficios → agregando...")
            try:
                agregar_beneficios(sheet, muni, nuevos_reales)
                for b in nuevos_reales:
                    print(f"      ✅ {b['cat']} | {b['titulo'][:50]}")
                total_nuevos += len(nuevos_reales)
                total_municipios_con_datos += 1
            except Exception as e:
                print(f"   ❌ Error al escribir en Sheet: {e}")
        else:
            print(f"   ✔️  Sin beneficios nuevos")

        print()
        time.sleep(3)  # cortesía entre municipios

    print(f"{sep}")
    print(f"✅ Proceso completado")
    print(f"   Municipios con datos nuevos : {total_municipios_con_datos}")
    print(f"   Beneficios nuevos agregados : {total_nuevos}")
    print(f"{sep}\n")

if __name__ == "__main__":
    main()
