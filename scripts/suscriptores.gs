/**
 * Ayuda al Vecino — Suscriptores
 * Google Apps Script que recibe suscripciones desde el sitio y las guarda
 * en la hoja "suscriptores" del Google Sheet del proyecto.
 *
 * INSTRUCCIONES DE DESPLIEGUE:
 * 1. Abre el Google Sheet del proyecto.
 * 2. Ve a Extensiones → Apps Script.
 * 3. Pega todo este código, reemplazando lo que haya.
 * 4. Guarda (Ctrl+S) con el nombre "Suscriptores".
 * 5. Clic en "Implementar" → "Nueva implementación".
 * 6. Tipo: "Aplicación web".
 * 7. Ejecutar como: "Yo (tu cuenta)".
 * 8. Acceso: "Cualquier persona".
 * 9. Clic en "Implementar" y copia la URL que te da.
 * 10. Pega esa URL en index.html donde dice APPS_SCRIPT_URL = "".
 */

var SHEET_ID = "1gNnACIdC4Er-GR-E96keujUrg2dyfCk9L2I_2HRHU9E";
var NOMBRE_HOJA = "suscriptores";

// Encabezados de la hoja (se crean solos si no existen)
var HEADERS = ["fecha", "nombre", "email", "municipio", "tipo", "estado"];

// ─────────────────────────────────────────────────────────────────────────────

function doGet(e) {
  try {
    var nombre    = limpiar(e.parameter.nombre);
    var email     = limpiar(e.parameter.email).toLowerCase();
    var municipio = limpiar(e.parameter.municipio);
    var tipo      = limpiar(e.parameter.tipo) || "personal";

    // Validaciones básicas
    if (!email)     return resp(false, "El correo es obligatorio");
    if (!municipio) return resp(false, "El municipio es obligatorio");
    if (!emailValido(email)) return resp(false, "El correo no es válido");

    var hoja = obtenerHoja();

    // Verificar duplicado
    var datos = hoja.getDataRange().getValues();
    for (var i = 1; i < datos.length; i++) {
      if ((datos[i][2] || "").toLowerCase() === email) {
        return resp(false, "Este correo ya está suscrito 😊");
      }
    }

    // Agregar nueva fila
    var fecha = Utilities.formatDate(new Date(), "America/Santiago", "dd/MM/yyyy HH:mm");
    hoja.appendRow([fecha, nombre, email, municipio, tipo, "activo"]);

    return resp(true, "¡Listo! Te avisamos cuando haya novedades.");

  } catch (err) {
    return resp(false, "Error interno: " + err.toString());
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function resp(ok, msg) {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: ok, msg: msg }))
    .setMimeType(ContentService.MimeType.JSON);
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
    // Ancho de columnas
    hoja.setColumnWidth(1, 130); // fecha
    hoja.setColumnWidth(2, 160); // nombre
    hoja.setColumnWidth(3, 220); // email
    hoja.setColumnWidth(4, 140); // municipio
    hoja.setColumnWidth(5, 110); // tipo
    hoja.setColumnWidth(6, 90);  // estado
  }
  return hoja;
}
