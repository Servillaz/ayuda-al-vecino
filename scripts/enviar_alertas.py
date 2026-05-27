#!/usr/bin/env python3
"""
Envía alertas semanales a suscriptores de Ayuda al Vecino vía Brevo.

Variables de entorno requeridas:
  - BREVO_API_KEY        → obtener en app.brevo.com → SMTP & API → API Keys
  - BREVO_SENDER_EMAIL   → email verificado como remitente en Brevo
  - GOOGLE_CREDENTIALS_JSON  (o scripts/credentials.json en local)
  - SHEET_ID             (opcional, tiene valor por defecto)
"""

import csv, json, os, sys, requests
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote as url_quote
from google.oauth2.service_account import Credentials
import gspread

# ── Config ────────────────────────────────────────────────────────────────────
SHEET_ID           = os.environ.get("SHEET_ID", "1gNnACIdC4Er-GR-E96keujUrg2dyfCk9L2I_2HRHU9E")
BREVO_API_KEY      = os.environ.get("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "")
BREVO_SENDER_NAME  = "Ayuda al Vecino"
BREVO_API_URL      = "https://api.brevo.com/v3/smtp/email"
APPS_SCRIPT_URL    = "https://script.google.com/macros/s/AKfycbyO4eeJGuFK3V2JI8khuF4IIR2W3cy3WVTrqSgVMQV2ULSXl715Zd90QBw9LhXfiz9J/exec"
SITIO_URL          = "https://servillaz.github.io/ayuda-al-vecino/"
DIAS_EVENTO        = 21   # avisar eventos en los próximos N días
SCOPES             = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

MESES_ES = {
    1:"enero", 2:"febrero", 3:"marzo", 4:"abril", 5:"mayo", 6:"junio",
    7:"julio", 8:"agosto", 9:"septiembre", 10:"octubre", 11:"noviembre", 12:"diciembre"
}

# ── Credenciales Google ───────────────────────────────────────────────────────
def cargar_credenciales():
    env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if env:
        try:
            return json.loads(env)
        except json.JSONDecodeError:
            print("ERROR: GOOGLE_CREDENTIALS_JSON no es JSON válido", file=sys.stderr)
            sys.exit(1)
    local = Path(__file__).parent / "credentials.json"
    if local.exists():
        with open(local, encoding="utf-8") as f:
            return json.load(f)
    print("ERROR: No se encontraron credenciales.", file=sys.stderr)
    sys.exit(1)

# ── Leer suscriptores desde Sheets ───────────────────────────────────────────
def leer_suscriptores():
    creds  = Credentials.from_service_account_info(cargar_credenciales(), scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SHEET_ID)
    try:
        hoja = sheet.worksheet("suscriptores")
    except gspread.exceptions.WorksheetNotFound:
        print("⚠️  Hoja 'suscriptores' no encontrada.")
        return []
    rows = hoja.get_all_records()
    return [r for r in rows if (r.get("estado") or "").strip().lower() == "activo"]

# ── Leer CSV locales ──────────────────────────────────────────────────────────
def leer_csv(nombre):
    ruta = Path(__file__).parent.parent / "datos-sheets" / nombre
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def fondos_relevantes():
    fondos = leer_csv("fondos.csv")
    return [f for f in fondos if (f.get("estado") or "").strip().lower() in ("abierto", "proximo")]

def eventos_proximos():
    eventos = leer_csv("calendario.csv")
    hoy     = datetime.now()
    limite  = hoy + timedelta(days=DIAS_EVENTO)
    proximos = []
    for ev in eventos:
        try:
            dia = int((ev.get("dia") or "0").strip())
            mes = MESES_ES.get((ev.get("mes") or "").strip().lower(), 0)
            if not dia or not mes:
                continue
            año    = hoy.year
            fecha  = datetime(año, mes, dia)
            if fecha < hoy:
                fecha = datetime(año + 1, mes, dia)
            if hoy <= fecha <= limite:
                proximos.append({**ev, "_fecha": fecha})
        except Exception:
            continue
    return sorted(proximos, key=lambda x: x["_fecha"])

# ── Template HTML ─────────────────────────────────────────────────────────────
def html_email(nombre, fondos, eventos, email_dest):
    saludo   = f"Hola {nombre.split()[0]}" if nombre else "Hola vecino/a"
    unsub    = f"{APPS_SCRIPT_URL}?action=baja&email={url_quote(email_dest)}"

    # Fondos
    fondos_html = ""
    if fondos:
        items = ""
        for f in fondos[:5]:
            estado  = (f.get("estado") or "").strip().lower()
            badge   = "🟢 Abierto" if estado == "abierto" else "🟡 Próximamente"
            cierra  = (f.get("cierra") or "").strip()
            cierra_txt = f"⏰ Cierra: {cierra}" if cierra and cierra not in ("Por confirmar", "") else ""
            monto   = (f.get("monto") or "").strip()
            link    = (f.get("link") or SITIO_URL).strip()
            desc    = (f.get("desc") or "")[:100]
            items += f"""
            <tr><td style="padding:12px 0;border-bottom:1px solid #e8f5ee">
              <div style="font-size:12px;color:#2d9e5f;margin-bottom:3px">{badge} · {f.get('inst','')}</div>
              <div style="font-weight:600;color:#1c2331;margin-bottom:4px">{f.get('nombre','')}</div>
              <div style="font-size:13px;color:#4a5568;line-height:1.5">{desc}…</div>
              <div style="margin-top:6px;font-size:12px;color:#4a5568">💰 {monto}&nbsp;&nbsp;{cierra_txt}</div>
              <a href="{link}" style="display:inline-block;margin-top:8px;color:#1a6b3c;font-size:13px;font-weight:600;text-decoration:none">Ver fondo →</a>
            </td></tr>"""
        fondos_html = f"""
        <h2 style="color:#1a6b3c;font-size:17px;margin:24px 0 8px;font-family:Arial,sans-serif">💰 Fondos disponibles</h2>
        <table style="width:100%;border-collapse:collapse">{items}</table>"""

    # Eventos
    eventos_html = ""
    if eventos:
        items = ""
        for ev in eventos[:4]:
            urgente = str(ev.get("urgente", "")).lower() in ("true", "1", "sí", "si")
            badge   = "🔴 Urgente —" if urgente else "📅"
            fecha   = ev["_fecha"]
            fecha_s = f"{fecha.day} de {MESES_ES[fecha.month]}"
            items += f"""
            <tr><td style="padding:10px 0;border-bottom:1px solid #e8f5ee">
              <div style="font-size:12px;color:#b7860a;margin-bottom:2px">{badge} {fecha_s}</div>
              <div style="font-weight:600;color:#1c2331">{ev.get('nombre','')}</div>
              <div style="font-size:12px;color:#4a5568">{ev.get('tipo','')}</div>
            </td></tr>"""
        eventos_html = f"""
        <h2 style="color:#1a6b3c;font-size:17px;margin:24px 0 8px;font-family:Arial,sans-serif">📅 Fechas próximas</h2>
        <table style="width:100%;border-collapse:collapse">{items}</table>"""

    mes_año = f"{MESES_ES[datetime.now().month]} {datetime.now().year}"

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f7f8fa;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f7f8fa;padding:32px 16px">
<tr><td><table width="100%" style="max-width:560px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">

  <tr><td style="background:linear-gradient(135deg,#1a6b3c,#0f4a28);padding:28px 32px">
    <div style="font-size:22px;font-weight:700;color:#fff">🏘️ Ayuda al Vecino</div>
    <div style="font-size:13px;color:rgba(255,255,255,.7);margin-top:4px">Chile · Fondos y Beneficios · {mes_año}</div>
  </td></tr>

  <tr><td style="padding:28px 32px">
    <p style="color:#1c2331;font-size:16px;margin:0 0 8px"><strong>{saludo}</strong> 👋</p>
    <p style="color:#4a5568;font-size:14px;line-height:1.6;margin:0 0 4px">Aquí tienes las novedades de esta semana para tu comunidad.</p>
    {fondos_html}
    {eventos_html}
    <div style="margin-top:28px;text-align:center">
      <a href="{SITIO_URL}" style="display:inline-block;background:#1a6b3c;color:#fff;padding:12px 28px;border-radius:24px;text-decoration:none;font-weight:600;font-size:14px">
        Ver todo en el sitio →
      </a>
    </div>
  </td></tr>

  <tr><td style="background:#f7f8fa;padding:20px 32px;text-align:center;border-top:1px solid #e2e8f0">
    <p style="color:#718096;font-size:12px;margin:0;line-height:1.6">
      Recibes esto porque te suscribiste a Ayuda al Vecino.<br>
      <a href="{unsub}" style="color:#718096">Cancelar suscripción</a>
    </p>
  </td></tr>

</table></td></tr>
</table>
</body></html>"""

# ── Envío vía Brevo ───────────────────────────────────────────────────────────
def enviar(email_dest, nombre, asunto, html):
    if not BREVO_API_KEY:
        print(f"  ⚠️  Sin BREVO_API_KEY — simulando envío a {email_dest}")
        return True
    r = requests.post(
        BREVO_API_URL,
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
        json={
            "sender":      {"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
            "to":          [{"email": email_dest, "name": nombre or email_dest}],
            "subject":     asunto,
            "htmlContent": html,
        },
        timeout=20,
    )
    if r.status_code in (200, 201):
        return True
    print(f"  ❌ Error {r.status_code} enviando a {email_dest}: {r.text[:150]}")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=== Alertas Ayuda al Vecino ===")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

    fondos  = fondos_relevantes()
    eventos = eventos_proximos()

    if not fondos and not eventos:
        print("ℹ️  Sin fondos activos ni eventos próximos — no se envían alertas esta semana.")
        return

    print(f"📊 Contenido: {len(fondos)} fondo(s), {len(eventos)} evento(s) próximo(s)")

    suscriptores = leer_suscriptores()
    if not suscriptores:
        print("ℹ️  Sin suscriptores activos.")
        return

    print(f"👥 Suscriptores activos: {len(suscriptores)}\n")

    mes_año = f"{MESES_ES[datetime.now().month]} {datetime.now().year}"
    asunto  = f"🔔 Novedades Ayuda al Vecino — {mes_año}"
    if any(str(ev.get("urgente","")).lower() in ("true","1") for ev in eventos):
        asunto = "🚨 " + asunto

    ok = 0
    for sub in suscriptores:
        email  = (sub.get("email") or "").strip()
        nombre = (sub.get("nombre") or "").strip()
        if not email:
            continue
        html = html_email(nombre, fondos, eventos, email)
        print(f"  Enviando a {email}...", end=" ", flush=True)
        if enviar(email, nombre, asunto, html):
            print("✅")
            ok += 1

    print(f"\n✅ Alertas enviadas: {ok}/{len(suscriptores)}")

if __name__ == "__main__":
    main()
