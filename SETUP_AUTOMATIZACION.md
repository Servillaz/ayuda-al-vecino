# ⚙️ Setup: Automatización Ayuda al Vecino

Tiempo estimado: ~30 minutos la primera vez.

---

## Paso 1 — Crear repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre: `ayuda-al-vecino` (o el que prefieras)
3. Visibilidad: **Privado** (recomendado — tiene credenciales)
4. Haz click en **Create repository**
5. Sube todos los archivos de la carpeta del proyecto a ese repositorio

---

## Paso 2 — Configurar Google Cloud (Service Account)

Esto le da permiso al scraper para escribir en tu Google Sheet.

1. Ve a https://console.cloud.google.com/
2. Crea un proyecto nuevo → ponle nombre "ayuda-al-vecino"
3. En el menú lateral: **APIs y servicios → Biblioteca**
4. Busca **"Google Sheets API"** → habilítala
5. Ve a **APIs y servicios → Credenciales**
6. Haz click en **+ Crear credenciales → Cuenta de servicio**
   - Nombre: `scraper-ayuda-al-vecino`
   - Haz click en **Crear y continuar → Listo**
7. Haz click en la cuenta de servicio recién creada
8. Ve a la pestaña **Claves → Agregar clave → Crear clave nueva → JSON**
9. Se descarga un archivo `.json` — **guárdalo bien, no lo pierdas**
10. Copia el email de la cuenta de servicio (algo como `scraper@proyecto.iam.gserviceaccount.com`)

### Dar acceso al Sheet:
1. Abre tu Google Sheet
2. Haz click en **Compartir** (arriba a la derecha)
3. Pega el email de la cuenta de servicio
4. Rol: **Editor**
5. Haz click en **Enviar**

---

## Paso 3 — Obtener API Key de Anthropic (Claude)

El scraper usa Claude para interpretar las páginas web.

1. Ve a https://console.anthropic.com/
2. Crea una cuenta (si no tienes)
3. Ve a **API Keys → Create Key**
4. Copia la key (empieza con `sk-ant-...`)
5. El costo es muy bajo: el scraper usa claude-haiku (el modelo más barato)
   → aprox. USD $0.01–0.05 por ejecución semanal

---

## Paso 4 — Configurar Secrets en GitHub

Los secrets son variables privadas que GitHub Actions usa sin exponerlas.

1. En tu repositorio de GitHub: **Settings → Secrets and variables → Actions**
2. Haz click en **New repository secret** para cada uno:

| Nombre del secret | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | Tu API key de Anthropic (`sk-ant-...`) |
| `SHEET_ID` | El ID de tu Google Sheet (entre `/d/` y `/edit` en la URL) |
| `GOOGLE_CREDENTIALS_JSON` | El contenido **completo** del archivo JSON descargado en el Paso 2 |

**Para el JSON de Google:** abre el archivo `.json`, selecciona todo el contenido (Ctrl+A), cópialo y pégalo directamente como valor del secret. Debe quedar en una sola línea.

---

## Paso 5 — Probar manualmente

Antes de esperar al lunes:

1. En tu repositorio de GitHub: **Actions**
2. Haz click en **"🔍 Actualizar Fondos Comunitarios"** en el panel izquierdo
3. Haz click en **"Run workflow" → Run workflow** (botón verde)
4. Espera ~3-5 minutos y revisa el log

Si todo está bien verás algo como:
```
✅ Proceso completado
   Actualizaciones aplicadas : 3
   Fondos nuevos (revisar)   : 2
```

---

## Cómo funciona cada semana

```
Lunes 9:00 AM (Chile)
  → GitHub Actions ejecuta el scraper automáticamente
  → Revisa 6 fuentes oficiales:
      fondos.gob.cl, FOSIS, SENAMA, MINVU, SernamEG, GORE RM
  → Claude AI parsea el contenido de cada página
  → Compara con los datos actuales del Google Sheet
  → Actualiza fechas y estados de fondos existentes
  → Guarda fondos nuevos en pestaña "Nuevos Fondos" para tu revisión
  → Registra todo en pestaña "Log"
  → Tu página web lee el Sheet actualizado automáticamente
```

---

## Qué revisar tú (mínimo mensual)

El scraper actualiza automáticamente **lo que ya existe**. Tu revisión manual es solo para:

1. **Pestaña "Nuevos Fondos"**: fondos detectados que no estaban antes.
   - Si es relevante: cópialo a la pestaña `fondos`, complétalo y cambia "PENDIENTE" a "OK"
   - Si no aplica: márcalo como "DESCARTADO"

2. **Pestaña "Log"**: revisa el historial de cambios. Si ves algo raro, investiga.

---

## Agregar nuevas fuentes

Para agregar un sitio nuevo al scraper:

1. Abre `scraper/main.py`
2. Agrega una entrada al array `FUENTES`:
```python
{
    "nombre": "Nombre del sitio",
    "url": "https://ejemplo.gob.cl/fondos/",
    "params": {}
},
```
3. Sube el cambio a GitHub — el próximo lunes se incluirá esa fuente.

---

## Resolución de problemas comunes

| Error | Causa probable | Solución |
|---|---|---|
| `SHEET_ID no configurado` | Secret mal escrito | Revisa el nombre exacto del secret en GitHub |
| `Error al conectar con fondos.gob.cl` | Sitio caído o bloqueó el bot | Normal, el scraper sigue con las otras fuentes |
| `Claude devolvió JSON inválido` | Página sin fondos relevantes | Ignorar, no hay fondos que extraer |
| `No se pudo conectar: 403` | Sheet no compartido con la cuenta de servicio | Repetir Paso 2 — compartir el Sheet |
