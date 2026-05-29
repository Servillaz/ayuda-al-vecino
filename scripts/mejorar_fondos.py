#!/usr/bin/env python3
"""Actualiza las descripciones de fondos.csv con lenguaje simple y humano."""
import csv, sys, json, time
from pathlib import Path
from google.oauth2.service_account import Credentials
import gspread

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH = Path(__file__).parent.parent / "datos-sheets" / "fondos.csv"
SHEET_ID = "1gNnACIdC4Er-GR-E96keujUrg2dyfCk9L2I_2HRHU9E"
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets"]

# Descripciones mejoradas por ID
# Formato: id → {desc, quien}  (solo los campos que cambian)
MEJORAS = {
    "1": {
        "desc": "¿Tu organización hace trabajo comunitario? El Estado financia proyectos que fortalezcan la participación vecinal, la cohesión social o el cuidado del barrio.",
        "quien": "Juntas de vecinos y organizaciones comunitarias con personalidad jurídica vigente."
    },
    "2": {
        "desc": "Si tu barrio necesita una sede, multicancha, plaza o área verde, MINVU puede financiar hasta 7.500 UF del proyecto. Sin poner plata propia.",
        "quien": "Juntas de vecinos y organizaciones comunitarias con personalidad jurídica."
    },
    "3": {
        "desc": "¿La sede de tu junta de vecinos está deteriorada? El Estado paga hasta 2.000 UF para repararla. Solo necesitas aportar el 10% del costo.",
        "quien": "Juntas de vecinos que tengan una sede que necesite reparación."
    },
    "4": {
        "desc": "Dinero para que tu organización compre lo que necesita: un computador, capacitaciones, materiales o actividades. Montos pequeños, trámite más simple.",
        "quien": "Organizaciones comunitarias funcionales o territoriales sin fines de lucro."
    },
    "5": {
        "desc": "El fondo más grande de la RM para organizaciones: más de $14 mil millones para cultura, deporte, seguridad, medioambiente e inclusión social.",
        "quien": "Juntas de vecinos, fundaciones, corporaciones y organizaciones sin fines de lucro de la Región Metropolitana con al menos 2 años de antigüedad."
    },
    "6": {
        "desc": "Tu municipio puede cofinanciar obras en tu sede o barrio — rejas, iluminación, mobiliario, cámaras. Sin postular a concursos nacionales.",
        "quien": "Juntas de vecinos con directorio vigente y personalidad jurídica."
    },
    "7": {
        "desc": "Cada gobierno regional destina el 8% de su presupuesto a fondos para organizaciones de la región. Son de los fondos más grandes y menos conocidos.",
        "quien": "Organizaciones privadas sin fines de lucro con domicilio en la región."
    },
    "8": {
        "desc": "Tu municipio tiene plata propia para financiar proyectos de tu junta de vecinos o club. Busca en la municipalidad de tu comuna cuándo abre.",
        "quien": "Organizaciones comunitarias con personalidad jurídica en la comuna."
    },
    "9": {
        "desc": "Banco Santander financia proyectos sociales de organizaciones sin fines de lucro. Para cultura, deporte, medioambiente y emprendimiento social.",
        "quien": "ONGs, fundaciones, juntas de vecinos y clubes deportivos de todo Chile."
    },
    "10": {
        "desc": "Maipú tiene tres líneas de financiamiento: FONDEVE para infraestructura, Subvenciones para programas y Tu Barrio Más Seguro para cámaras y alarmas.",
        "quien": "Juntas de vecinos, clubes, fundaciones y organizaciones comunitarias de Maipú."
    },
    "11": {
        "desc": "$600 millones anuales en 7 líneas: seguridad, turismo, talleres, deporte, cultura, fortalecimiento organizacional y medioambiente. Solo para organizaciones de Santiago.",
        "quien": "Juntas de vecinos, clubes deportivos, centros de madres y organizaciones con personalidad jurídica en Santiago."
    },
    "12": {
        "desc": "Ñuñoa tiene tres fondos: FONDEVE hasta $5M para tu sede, Corazón de Barrio para proyectos culturales y Ñuñoa Más Segura para seguridad vecinal.",
        "quien": "Juntas de vecinos y organizaciones comunitarias de Ñuñoa con personalidad jurídica."
    },
    "13": {
        "desc": "Providencia destina $1.000 millones para sus juntas de vecinos. Postulación 100% digital, sin ir a la municipalidad. Una de las mejores tasas de adjudicación.",
        "quien": "Juntas de vecinos con personalidad jurídica vigente en la comuna de Providencia."
    },
    "14": {
        "desc": "Las Condes tiene dos líneas: FONDEVE para mejorar infraestructura comunitaria y fondos concursables para cualquier proyecto vecinal de la comuna.",
        "quien": "Juntas de vecinos y organizaciones comunitarias con personalidad jurídica de Las Condes."
    },
    "15": {
        "desc": "El gobierno regional de Valparaíso destina $2.500 millones para organizaciones de toda la región. Incluye juntas de vecinos, sindicatos y clubes.",
        "quien": "Organizaciones comunitarias, juntas de vecinos, sindicatos y entidades culturales de la Región de Valparaíso."
    },
    "16": {
        "desc": "En Temuco las propias organizaciones del barrio deciden en qué se invierte el dinero municipal. Un modelo único de participación ciudadana real.",
        "quien": "Juntas de vecinos, organizaciones funcionales y comunidades indígenas de Temuco."
    },
    "17": {
        "desc": "El puerto de Valparaíso financia proyectos comunitarios de la ciudad: cultura, deporte, medioambiente y desarrollo local para organizaciones de Valparaíso.",
        "quien": "Juntas de vecinos, clubes deportivos, adultos mayores y organizaciones de Valparaíso."
    },
    "18": {
        "desc": "Tu organización de adultos mayores puede financiar actividades de salud, voluntariado, tecnología o recreación con fondos directos del Estado.",
        "quien": "Organizaciones de personas mayores con personalidad jurídica. Todos sus socios deben ser adultos mayores."
    },
    "19": {
        "desc": "Fondos para proyectos que promuevan la participación y el liderazgo de las mujeres. Pueden postular tanto mujeres individuales como organizaciones.",
        "quien": "Personas naturales y organizaciones sin fines de lucro de todas las regiones del país."
    },
    "20": {
        "desc": "Cuidado gratuito para los hijos e hijas de madres trabajadoras de 14:00 a 20:00 hrs, después del horario escolar. Funciona en establecimientos municipales.",
        "quien": "Madres trabajadoras con hijos o hijas en edad escolar. Se inscriben en el establecimiento participante."
    },
    "21": {
        "desc": "Si eres familia vulnerable y recibes beneficios del Estado, en marzo llega automáticamente a tu cuenta un bono anual. No tienes que hacer nada para cobrarlo.",
        "quien": "Familias del 60% más vulnerable según el RSH que reciban SUF, asignación familiar o Chile Solidario."
    },
    "22": {
        "desc": "Si tienes 65 años o más y tu pensión es baja o no tienes, el Estado te garantiza una pensión mensual. Se tramita en cualquier oficina del IPS.",
        "quien": "Personas de 65 años o más que vivan en Chile desde hace al menos 20 años y estén en el 90% más vulnerable."
    },
    "23": {
        "desc": "¿Tu junta de vecinos necesita cámaras, iluminación o alarmas? Santiago financia proyectos de seguridad vecinal hasta $2.800.000 por organización.",
        "quien": "Juntas de vecinos con personalidad jurídica y directorio vigente en la comuna de Santiago."
    },
    "24": {
        "desc": "Financia paseos, excursiones y actividades recreativas para tus vecinos. Hasta $1.500.000 para que tu organización organice una salida o evento.",
        "quien": "Organizaciones comunitarias con personalidad jurídica y directorio vigente en Santiago."
    },
    "25": {
        "desc": "Dinero para talleres de tejido, bordado, cocina, artesanía o cualquier manualidad para los vecinos de tu barrio. Hasta $1.000.000 por organización.",
        "quien": "Organizaciones comunitarias con personalidad jurídica y directorio vigente en Santiago."
    },
    "26": {
        "desc": "¿Tu club quiere organizar un torneo, una cicletada o comprar implementos? Este fondo cubre actividades deportivas y de vida saludable. Hasta $1.500.000.",
        "quien": "Organizaciones deportivas y comunitarias con personalidad jurídica y directorio vigente en Santiago."
    },
    "27": {
        "desc": "Financia festivales, murales, música en vivo o rescate del patrimonio de tu barrio. Hasta $1.500.000 para proyectos culturales y artísticos en Santiago.",
        "quien": "Organizaciones culturales y comunitarias con personalidad jurídica y directorio vigente en Santiago."
    },
    "28": {
        "desc": "¿Tu junta de vecinos necesita un computador, capacitación o arreglar la sede? Este fondo ayuda a que tu organización funcione mejor. Hasta $1.500.000.",
        "quien": "Organizaciones comunitarias con personalidad jurídica y directorio vigente en Santiago."
    },
    "29": {
        "desc": "Financia un reciclaje comunitario, un huerto urbano o plantación de árboles en tu barrio. Hasta $1.000.000 para proyectos de medioambiente en Santiago.",
        "quien": "Organizaciones comunitarias con personalidad jurídica y directorio vigente en Santiago."
    },
    "30": {
        "desc": "Fondo de Ñuñoa para proyectos culturales, recreativos y de mejoramiento del entorno del barrio. Convocatoria anual para organizaciones de la comuna.",
        "quien": "Organizaciones comunitarias y juntas de vecinos con personalidad jurídica en Ñuñoa."
    },
    "31": {
        "desc": "Ñuñoa financia cámaras, iluminación y proyectos de seguridad para tu barrio. Convocatoria anual exclusiva para organizaciones de la comuna.",
        "quien": "Organizaciones comunitarias y juntas de vecinos con personalidad jurídica en Ñuñoa."
    },
}

def main():
    # Actualizar CSV
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        campos = rows[0].keys() if rows else []

    print(f"Actualizando {len(MEJORAS)} fondos...")
    cambios = 0
    for row in rows:
        rid = str(row.get("id","")).strip()
        if rid in MEJORAS:
            for campo, valor in MEJORAS[rid].items():
                row[campo] = valor
            cambios += 1
            print(f"  OK [{rid}] {row['nombre'][:50]}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCSV actualizado: {cambios} fondos mejorados")

    # Actualizar Google Sheets
    print("\nActualizando Google Sheets...")
    try:
        local = Path(__file__).parent / "credentials.json"
        with open(local, encoding="utf-8") as f:
            creds_json = json.load(f)
        creds  = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet  = client.open_by_key(SHEET_ID)
        hoja   = sheet.worksheet("fondos")

        headers = hoja.row_values(1)
        col_desc  = headers.index("desc")  + 1
        col_quien = headers.index("quien") + 1

        # Leer IDs del Sheet
        ids_col = hoja.col_values(1)  # columna 'id'

        for row in rows:
            rid = str(row.get("id","")).strip()
            if rid not in MEJORAS:
                continue
            try:
                sheet_row = ids_col.index(rid) + 1
                hoja.update_cell(sheet_row, col_desc,  row["desc"])
                hoja.update_cell(sheet_row, col_quien, row["quien"])
                time.sleep(0.4)
                print(f"  Sheet OK [{rid}]")
            except Exception as e:
                print(f"  Sheet SKIP [{rid}]: {e}")

        print("Google Sheets actualizado")
    except Exception as e:
        print(f"Sheets no disponible localmente: {e}")
        print("(Se actualizara en el proximo sync automatico)")

if __name__ == "__main__":
    main()
