/**
 * Ayuda al Vecino — Suscriptores (v2)
 * Endpoints:
 *   ?                            → suscribir (comportamiento por defecto)
 *   ?action=baja&email=...       → cancelar suscripción (devuelve HTML)
 *   ?action=info&email=...       → consultar datos del suscriptor (JSON)
 *   ?action=actualizar&email=... → actualizar municipio y/o tipo (JSON)
 *
 * INSTRUCCIONES DE DESPLIEGUE (primera vez o al actualizar):
 * 1. Abre el Google Sheet → Extensiones → Apps Script.
 * 2. Pega este código completo, reemplazando todo lo anterior.
 * 3. Guarda (Ctrl+S).
 * 4. Clic en "Implementar" → "Administrar implementaciones".
 * 5. Sobre la implementación existente, clic en el lápiz (editar).
 * 6. En "Versión", elige "Nueva versión".
 * 7. Clic en "Implementar". La URL no cambia.
 */

var SHEET_ID    = "1gNnACIdC4Er-GR-E96keujUrg2dyfCk9L2I_2HRHU9E";
var NOMBRE_HOJA = "suscriptores";
var SITIO_URL   = "https://servillaz.github.io/ayuda-al-vecino/";
var HEADERS     = ["fecha", "nombre", "email", "municipio", "tipo", "estado"];

// ─────────────────────────────────────────────────────────────────────────────

function doGet(e) {
  var action = limpiar(e.parameter.action).toLowerCase() || "suscribir";

  switch (action) {
    case "baja":       return procesarBaja(e);
    case "info":       return procesarInfo(e);
    case "actualizar": return procesarActualizar(e);
    default:           return procesarSuscripcion(e);
  }
}

// ── Suscribir ─────────────────────────────────────────────────────────────────
function procesarSuscripcion(e) {
  var nombre    = limpiar(e.parameter.nombre);
  var email     = limpiar(e.parameter.email).toLowerCase();
  var municipio = limpiar(e.parameter.municipio);
  var tipo      = limpiar(e.parameter.tipo) || "personal";

  if (!email)     return respJSON(false, "El correo es obligatorio");
  if (!municipio) return respJSON(false, "El municipio es obligatorio");
  if (!emailValido(email)) return respJSON(false, "El correo no es válido");

  var hoja  = obtenerHoja();
  var datos = hoja.getDataRange().getValues();

  for (var i = 1; i < datos.length; i++) {
    if ((datos[i][2] || "").toLowerCase() === email) {
      return respJSON(false, "Este correo ya está suscrito 😊");
    }
  }

  var fecha = Utilities.formatDate(new Date(), "America/Santiago", "dd/MM/yyyy HH:mm");
  hoja.appendRow([fecha, nombre, email, municipio, tipo, "activo"]);
  return respJSON(true, "¡Listo! Te avisamos cuando haya novedades.");
}

// ── Dar de baja (devuelve página HTML) ────────────────────────────────────────
function procesarBaja(e) {
  var email = limpiar(e.parameter.email).toLowerCase();
  if (!email) return respHTML("⚠️ Error", "No se especificó un correo.");

  var hoja  = obtenerHoja();
  var datos = hoja.getDataRange().getValues();

  for (var i = 1; i < datos.length; i++) {
    if ((datos[i][2] || "").toLowerCase() === email) {
      if ((datos[i][5] || "").toLowerCase() === "baja") {
        return respHTML("Ya estabas dado de baja", "Tu correo ya estaba cancelado.<br><br><a href='" + SITIO_URL + "'>Volver al sitio</a>");
      }
      hoja.getRange(i + 1, 6).setValue("baja");
      return respHTML(
        "✅ Suscripción cancelada",
        "Lamentamos verte partir. Ya no recibirás más alertas.<br><br>" +
        "<a href='" + SITIO_URL + "' style='color:#1a6b3c;font-weight:600'>Volver al sitio →</a>"
      );
    }
  }
  return respHTML("No encontrado", "No encontramos ese correo en nuestra lista.<br><br><a href='" + SITIO_URL + "'>Volver al sitio</a>");
}

// ── Consultar info (para prefill del formulario) ──────────────────────────────
function procesarInfo(e) {
  var email = limpiar(e.parameter.email).toLowerCase();
  if (!email) return respJSON(false, "Email no proporcionado");

  var hoja  = obtenerHoja();
  var datos = hoja.getDataRange().getValues();

  for (var i = 1; i < datos.length; i++) {
    if ((datos[i][2] || "").toLowerCase() === email) {
      return respJSON(true, "ok", {
        nombre:    datos[i][1],
        municipio: datos[i][3],
        tipo:      datos[i][4],
        estado:    datos[i][5]
      });
    }
  }
  return respJSON(false, "No encontrado");
}

// ── Actualizar preferencias ───────────────────────────────────────────────────
function procesarActualizar(e) {
  var email     = limpiar(e.parameter.email).toLowerCase();
  var municipio = limpiar(e.parameter.municipio);
  var tipo      = limpiar(e.parameter.tipo);

  if (!email) return respJSON(false, "Email no proporcionado");

  var hoja  = obtenerHoja();
  var datos = hoja.getDataRange().getValues();

  for (var i = 1; i < datos.length; i++) {
    if ((datos[i][2] || "").toLowerCase() === email) {
      if (municipio) hoja.getRange(i + 1, 4).setValue(municipio);
      if (tipo)      hoja.getRange(i + 1, 5).setValue(tipo);
      hoja.getRange(i + 1, 6).setValue("activo");  // reactivar si estaba de baja
      return respJSON(true, "Preferencias actualizadas correctamente");
    }
  }
  return respJSON(false, "Email no encontrado en la lista");
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function respJSON(ok, msg, data) {
  var payload = { ok: ok, msg: msg };
  if (data) payload.data = data;
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function respHTML(titulo, cuerpo) {
  var html =
    '<html><head><meta charset="UTF-8">' +
    '<style>body{font-family:Arial,sans-serif;max-width:480px;margin:80px auto;text-align:center;color:#333;padding:0 24px}' +
    'h2{color:#1a6b3c;font-size:1.4rem}p{line-height:1.6;color:#4a5568}a{color:#1a6b3c}' +
    '.logo{font-size:2rem;margin-bottom:8px}</style></head>' +
    '<body><div class="logo">🏘️</div><h2>' + titulo + '</h2><p>' + cuerpo + '</p></body></html>';
  return HtmlService.createHtmlOutput(html);
}

function limpiar(val) {
  return (val || "").toString().trim();
}

function emailValido(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function obtenerHoja() {
  var ss   = SpreadsheetApp.openById(SHEET_ID);
  var hoja = ss.getSheetByName(NOMBRE_HOJA);
  if (!hoja) {
    hoja = ss.insertSheet(NOMBRE_HOJA);
    hoja.appendRow(HEADERS);
    hoja.setFrozenRows(1);
    hoja.setColumnWidth(1, 130);
    hoja.setColumnWidth(2, 160);
    hoja.setColumnWidth(3, 220);
    hoja.setColumnWidth(4, 140);
    hoja.setColumnWidth(5, 110);
    hoja.setColumnWidth(6, 90);
  }
  return hoja;
}
