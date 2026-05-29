#!/usr/bin/env python3
"""Aprueba los fondos de 'Nuevos Fondos' y los mueve al tab oficial."""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from google.oauth2.service_account import Credentials
import gspread
from pathlib import Path

SHEET_ID = '1gNnACIdC4Er-GR-E96keujUrg2dyfCk9L2I_2HRHU9E'
SCOPES   = ['https://www.googleapis.com/auth/spreadsheets']

with open(Path(__file__).parent / 'credentials.json', encoding='utf-8') as f:
    creds_json = json.load(f)
creds  = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
client = gspread.authorize(creds)
sheet  = client.open_by_key(SHEET_ID)
hoja   = sheet.worksheet('fondos')

FONDOS_NUEVOS = [
    [23,'municipal','Fondos Concursables Santiago — Seguridad Vecinal (FONSEVE)','Municipalidad de Santiago',
     'Financia proyectos de seguridad vecinal: camaras, iluminacion, alarmas y equipamiento para juntas de vecinos de Santiago.',
     'cerrado','Hasta $2.800.000','No requerido',
     'Juntas de vecinos con personalidad juridica y directorio vigente en Santiago.',
     'Seguridad','Region Metropolitana','Santiago','16 mar 2026','10 abr 2026',
     'https://www.munistgo.cl/fondos/',
     'Personalidad juridica vigente, directorio vigente, domicilio en Santiago.',
     'Revisa bases en munistgo.cl/fondos · Asiste a taller · Completa formulario online · Adjunta documentos · Envia antes del plazo',
     'Camaras de seguridad para pasajes|Iluminacion de espacios oscuros|Sistema de alarma comunitaria|Equipamiento para rondas vecinales',
     'La Junta de Vecinos Pasaje Las Flores (Santiago) instalo 4 camaras en puntos ciegos del barrio.'],

    [24,'municipal','Fondos Concursables Santiago — Turismo y Recreacion','Municipalidad de Santiago',
     'Financia paseos, excursiones y actividades recreativas para vecinos y organizaciones de Santiago.',
     'cerrado','Hasta $1.500.000','No requerido',
     'Organizaciones comunitarias con personalidad juridica y directorio vigente en Santiago.',
     'Cultura|Social','Region Metropolitana','Santiago','16 mar 2026','10 abr 2026',
     'https://www.munistgo.cl/fondos/',
     'Personalidad juridica vigente, directorio en ejercicio, domicilio en Santiago.',
     'Revisa bases en munistgo.cl/fondos · Completa formulario online · Adjunta documentos · Envia antes del plazo',
     'Paseo a la playa para vecinos|Excursion a parque nacional|Visita a parque de atracciones|Dia de campo recreativo',
     'El Club de Adultos Mayores Los Aromos organizo un paseo a Vina del Mar para 40 socios.'],

    [25,'municipal','Fondos Concursables Santiago — Talleres y Manualidades','Municipalidad de Santiago',
     'Financia talleres de tejido, bordado, cocina, artesania y manualidades para vecinos de Santiago.',
     'cerrado','Hasta $1.000.000','No requerido',
     'Organizaciones comunitarias con personalidad juridica y directorio vigente en Santiago.',
     'Social|Cultura','Region Metropolitana','Santiago','16 mar 2026','10 abr 2026',
     'https://www.munistgo.cl/fondos/',
     'Personalidad juridica vigente, directorio en ejercicio, domicilio en Santiago.',
     'Revisa bases en munistgo.cl/fondos · Completa formulario online · Adjunta documentos · Envia antes del plazo',
     'Taller de tejido y bordado|Taller de cocina saludable|Taller de pintura y artesania|Costura y reparacion de ropa',
     'El Centro de Madres Villa Portales realizo 8 talleres de manualidades para 30 mujeres del barrio.'],

    [26,'municipal','Fondos Concursables Santiago — Deporte y Vida Saludable','Municipalidad de Santiago',
     'Financia actividades deportivas, torneos y programas de vida saludable para organizaciones de Santiago.',
     'cerrado','Hasta $1.500.000','No requerido',
     'Organizaciones deportivas y comunitarias con personalidad juridica y directorio vigente en Santiago.',
     'Deporte','Region Metropolitana','Santiago','16 mar 2026','10 abr 2026',
     'https://www.munistgo.cl/fondos/',
     'Personalidad juridica vigente, directorio en ejercicio, domicilio en Santiago.',
     'Revisa bases en munistgo.cl/fondos · Completa formulario online · Adjunta documentos · Envia antes del plazo',
     'Campeonato de futbol barrial|Programa de running comunitario|Equipamiento deportivo para el club|Cicletada familiar',
     'El Club Deportivo Union Central organizo un torneo de futbol 7 con 12 equipos del sector.'],

    [27,'municipal','Fondos Concursables Santiago — Arte, Cultura y Patrimonio','Municipalidad de Santiago',
     'Financia proyectos culturales, artisticos y de rescate del patrimonio historico de los barrios de Santiago.',
     'cerrado','Hasta $1.500.000','No requerido',
     'Organizaciones culturales y comunitarias con personalidad juridica y directorio vigente en Santiago.',
     'Cultura','Region Metropolitana','Santiago','16 mar 2026','10 abr 2026',
     'https://www.munistgo.cl/fondos/',
     'Personalidad juridica vigente, directorio en ejercicio, domicilio en Santiago.',
     'Revisa bases en munistgo.cl/fondos · Completa formulario online · Adjunta documentos · Envia antes del plazo',
     'Festival cultural del barrio|Mural artistico identitario|Registro fotografico del barrio|Concierto o pena folclorica',
     'La Agrupacion Cultural El Almendral produjo un documental sobre la historia del barrio Yungay.'],

    [28,'municipal','Fondos Concursables Santiago — Fortalecimiento Organizacional','Municipalidad de Santiago',
     'Financia proyectos que mejoran la gestion, infraestructura y capacidades de las organizaciones vecinales de Santiago.',
     'cerrado','Hasta $1.500.000','No requerido',
     'Organizaciones comunitarias con personalidad juridica y directorio vigente en Santiago.',
     'Social','Region Metropolitana','Santiago','16 mar 2026','10 abr 2026',
     'https://www.munistgo.cl/fondos/',
     'Personalidad juridica vigente, directorio en ejercicio, domicilio en Santiago.',
     'Revisa bases en munistgo.cl/fondos · Completa formulario online · Adjunta documentos · Envia antes del plazo',
     'Computador y conectividad para la sede|Mobiliario y equipamiento|Capacitacion en gestion|Reparaciones menores de la sede',
     'La Junta de Vecinos Poblacion Quinta Normal renovo el equipamiento de su sede y capacito a su directorio.'],

    [29,'municipal','Fondos Concursables Santiago — Medioambiente','Municipalidad de Santiago',
     'Financia proyectos de reciclaje, compostaje, huertos urbanos y cuidado del medioambiente en Santiago.',
     'cerrado','Hasta $1.000.000','No requerido',
     'Organizaciones comunitarias con personalidad juridica y directorio vigente en Santiago.',
     'Medio Ambiente','Region Metropolitana','Santiago','16 mar 2026','10 abr 2026',
     'https://www.munistgo.cl/fondos/',
     'Personalidad juridica vigente, directorio en ejercicio, domicilio en Santiago.',
     'Revisa bases en munistgo.cl/fondos · Completa formulario online · Adjunta documentos · Envia antes del plazo',
     'Punto limpio de reciclaje comunitario|Huerto urbano para el barrio|Plantacion de arboles y jardines|Compostaje de residuos organicos',
     'La Junta de Vecinos El Arenal instalo un huerto urbano que abastece de verduras a 20 familias.'],

    [30,'municipal','Corazon de Barrio — Municipalidad de Nunoa','Municipalidad de Nunoa',
     'Fondo concursable de Nunoa para proyectos de mejoramiento del entorno, cultura y vida comunitaria en el barrio.',
     'cerrado','Sin informacion','No requerido',
     'Organizaciones comunitarias y juntas de vecinos con personalidad juridica en Nunoa.',
     'Social|Cultura','Region Metropolitana','Nunoa','Por confirmar','Por confirmar',
     'https://www.nunoa.cl',
     'Personalidad juridica vigente, directorio en ejercicio, domicilio en Nunoa.',
     'Revisa convocatoria en nunoa.cl · Descarga bases · Prepara proyecto · Postula antes del plazo',
     'Mejoramiento de plazas y areas verdes|Actividades culturales y recreativas|Proyectos de embellecimiento del barrio',
     'Organizaciones de Nunoa han recuperado plazas y espacios publicos con este fondo anual.'],

    [31,'municipal','Nunoa + Segura — Municipalidad de Nunoa','Municipalidad de Nunoa',
     'Fondo de seguridad vecinal de Nunoa para financiar camaras, iluminacion y proyectos de seguridad barrial.',
     'cerrado','Sin informacion','No requerido',
     'Organizaciones comunitarias y juntas de vecinos con personalidad juridica en Nunoa.',
     'Seguridad','Region Metropolitana','Nunoa','Por confirmar','Por confirmar',
     'https://www.nunoa.cl',
     'Personalidad juridica vigente, directorio en ejercicio, domicilio en Nunoa.',
     'Revisa convocatoria en nunoa.cl · Descarga bases · Prepara proyecto · Postula antes del plazo',
     'Camaras de seguridad para el barrio|Iluminacion de pasajes oscuros|Sistemas de alarma comunitaria',
     'Juntas de vecinos de Nunoa han mejorado la seguridad de sus barrios con equipamiento financiado por este fondo.'],
]

print(f'Agregando {len(FONDOS_NUEVOS)} fondos al Sheet...')
for fondo in FONDOS_NUEVOS:
    hoja.append_row(fondo, value_input_option='RAW')
    print(f'  OK {fondo[0]}: {fondo[2][:55]}')
    time.sleep(0.8)

# Marcar como aprobados en Nuevos Fondos
hoja_nf = sheet.worksheet('Nuevos Fondos')
rows = hoja_nf.get_all_values()
for i in range(2, len(rows) + 1):
    hoja_nf.update_cell(i, 2, 'aprobado')
    time.sleep(0.3)

print(f'\nListos. {len(FONDOS_NUEVOS)} fondos agregados, pestaña Nuevos Fondos marcada.')
