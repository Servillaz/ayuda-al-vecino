#!/usr/bin/env python3
"""
Corrige masivamente URLs rotas en municipios.csv.
Estrategia: usar la web principal del municipio para todos los beneficios
cuya URL de subpágina esté rota.
"""
import csv, sys, json, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH = Path(__file__).parent.parent / "datos-sheets" / "municipios.csv"

# Dominios correctos verificados para cada municipio
WEBS_CORRECTAS = {
    "alhue":          "https://www.municipalidadalhue.cl",
    "antofagasta":    "https://www.municipalidadantofagasta.cl",
    "buin":           "https://www.buin.cl",
    "caleradetango":  "https://www.caleradetango.cl",
    "cerrillos":      "https://www.cerrillos.cl",
    "cerronavia":     "https://www.cerronavia.cl",
    "colina":         "https://www.colina.cl",
    "concepcion":     "https://www.municipalidaddeconcepcion.cl",
    "conchali":       "https://www.conchali.cl",
    "curacavi":       "https://www.curacavi.cl",
    "elbosque":       "https://www.municipalidadelbosque.cl",
    "elmonte":        "https://www.elmonte.cl",
    "estacioncentral":"https://www.muniestacioncentral.cl",
    "huechuraba":     "https://www.huechuraba.cl",
    "independencia":  "https://www.independencia.cl",
    "islademaipo":    "https://www.islademaipo.cl",
    "lacisterna":     "https://www.lacisterna.cl",
    "laflorida":      "https://www.laflorida.cl/sitio",
    "lagranja":       "https://www.lagranja.cl",
    "lampa":          "https://www.lampa.cl",
    "lapintana":      "https://pintana.cl",
    "lareina":        "https://www.lareina.cl",
    "lascondes":      "https://www.lascondes.cl",
    "lobarnechea":    "https://www.lobarnechea.cl",
    "loespejo":       "https://www.loespejo.cl",
    "loprado":        "https://www.loprado.cl",
    "macul":          "https://www.macul.cl",
    "maipu":          "https://municipalidadmaipu.cl",
    "mariapinto":     "https://www.mariapinto.cl",
    "melipilla":      "https://www.melipilla.cl",
    "nunoa":          "https://www.nunoa.cl",
    "pac":            "https://www.mpac.cl",
    "padrehurtado":   "https://www.padrehurtado.cl",
    "paine":          "https://www.paine.cl",
    "penaflor":       "https://www.penaflor.cl",
    "penalolen":      "https://www.penalolen.cl",
    "pirque":         "https://www.pirque.cl",
    "providencia":    "https://www.providencia.cl",
    "pudahuel":       "https://www.pudahuel.cl",
    "puentealto":     "https://www.mpuentealto.cl",
    "quilicura":      "https://www.quilicura.cl",
    "quintanormal":   "https://www.quintanormal.cl",
    "recoleta":       "https://www.recoleta.cl",
    "renca":          "https://www.renca.cl",
    "sanbernardo":    "https://www.sanbernardo.cl",
    "sanjoaquin":     "https://www.sanjoaquin.cl",
    "sanjosedemaipo": "https://www.sanjosedemaipo.cl",
    "sanmiguel":      "https://www.sanmiguel.cl",
    "sanpedro":       "https://www.municipalidadsanpedro.cl",
    "sanramon":       "https://www.municipalidadsanramon.cl",
    "santiago":       "https://www.munistgo.cl",
    "talagante":      "https://www.talagante.cl",
    "temuco":         "https://www.temuco.cl",
    "tiltil":         "https://www.tiltil.cl",
    "valparaiso":     "https://www.municipalidaddevalparaiso.cl",
    "vitacura":       "https://www.vitacura.cl",
    "colina":         "https://www.colina.cl",
    "lobarnechea":    "https://www.lobarnechea.cl",
}

# URLs de subpáginas que sabemos que NO existen (patrones)
SUBPATHS_ROTAS = [
    "/salud/", "/educacion/", "/adulto-mayor/", "/adulto_mayor/",
    "/social/", "/veterinaria/", "/deporte/", "/cultura/",
    "/becas-y-fondos", "/becas/", "/farmacia/", "/como-inscribirse/",
    "/optica-popular/", "/tarjeta-vecino/", "/desarrollo-social/",
    "/farmacia-municipal-solidaria/", "/adulto-mayor",
]

def url_es_rota(url, muni_id):
    """Detecta si una URL tiene una subpágina que probablemente no existe."""
    if not url or not url.startswith("http"):
        return False
    # Dominios específicos que sabemos que están mal
    dominios_rotos = [
        "munistgo.cl/salud", "munistgo.cl/becas", "munistgo.cl/adulto",
        "ww2.recoleta.cl", "municelbosque.cl", "mconchali.cl",
        "municipalidadcerrillos.cl", "mhuechuraba.cl", "mindependencia.cl",
        "municipalidadlacisterna.cl", "mlagranja.cl", "munilapintana.cl",
        "lareina.cl/", "msanjoaquin.cl", "msanmiguel.cl", "mpac.cl/",
        "municipalidadcolina.cl", "municipalidadlampa.cl", "municipalidadtiltil.cl",
        "muniidem.cl", "municipalidadpaine.cl", "municipalidadbuin.cl",
        "municipalidadcaleradetango.cl", "municipalidadmariapinto.cl",
        "municipalidadsanpedro.cl", "municipalidadelmonte.cl",
        "municipalidadpadrehurtado.cl", "municipalidadpenaflor.cl",
        "municipalidadtalagante.cl", "municipalidadsanjosedemaipo.cl",
        "mpirque.cl", "penalolen.cl/",
    ]
    for d in dominios_rotos:
        if d in url:
            return True
    # Subpaths conocidos que no existen en la mayoría de sitios
    for sp in SUBPATHS_ROTAS:
        if sp in url:
            return True
    # Estación Central vieja
    if "estacioncentral.cl/" in url and "muniestacioncentral" not in url:
        return True
    return False

def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        campos = list(rows[0].keys())

    corregidos = 0
    webs_corregidas = 0

    for row in rows:
        mid = row["municipio_id"]

        # Corregir campo 'web' si está mal
        web_actual = row.get("web", "").strip()
        if mid in WEBS_CORRECTAS:
            web_correcta = WEBS_CORRECTAS[mid]
            if web_actual != web_correcta and url_es_rota(web_actual, mid):
                row["web"] = web_correcta
                webs_corregidas += 1

        # Corregir campo 'url' si está rota
        url_actual = row.get("url", "").strip()
        if url_es_rota(url_actual, mid):
            # Usar la web correcta del municipio
            url_nueva = WEBS_CORRECTAS.get(mid, web_actual or "https://www.chileatiende.gob.cl")
            if url_nueva and url_nueva != url_actual:
                row["url"] = url_nueva
                corregidos += 1

    with open(CSV_PATH, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(rows)

    print(f"URLs de beneficios corregidas: {corregidos}")
    print(f"Webs de municipios corregidas: {webs_corregidas}")
    print(f"Total: {corregidos + webs_corregidas} correcciones")

if __name__ == "__main__":
    main()
