#!/usr/bin/env python3
"""Corrige URLs rotos en municipios.csv."""
import csv

DOMAIN_FIX = {
    'maipu.cl':                       'municipalidadmaipu.cl',
    'macul.cl':                       'munimacul.cl',
    'mconchali.cl':                   'conchali.cl',
    'www.mconchali.cl':               'www.conchali.cl',
    'mhuechuraba.cl':                 'huechuraba.cl',
    'www.mhuechuraba.cl':             'www.huechuraba.cl',
    'mindependencia.cl':              'chileatiende.gob.cl',
    'www.mindependencia.cl':          'chileatiende.gob.cl',
    'mpac.cl':                        'pac.cl',
    'www.mpac.cl':                    'www.pac.cl',
    'msanjoaquin.cl':                 'sanjoaquin.cl',
    'www.msanjoaquin.cl':             'www.sanjoaquin.cl',
    'msanmiguel.cl':                  'sanmiguel.cl',
    'www.msanmiguel.cl':              'www.sanmiguel.cl',
    'municelbosque.cl':               'elbosque.cl',
    'www.municelbosque.cl':           'www.elbosque.cl',
    'munilapintana.cl':               'lapintana.cl',
    'www.munilapintana.cl':           'www.lapintana.cl',
    'muniidem.cl':                    'islademaipo.cl',
    'municipalidadbuin.cl':           'buin.cl',
    'municipalidadcaleradetango.cl':  'caleradetango.cl',
    'municipalidadcerrillos.cl':      'cerrillos.cl',
    'municipalidadcolina.cl':         'colina.cl',
    'municipalidadelmonte.cl':        'munielmonte.cl',
    'municipalidadlacisterna.cl':     'lacisterna.cl',
    'municipalidadlampa.cl':          'lampa.cl',
    'municipalidadmariapinto.cl':     'mariapinto.cl',
    'municipalidadpadrehurtado.cl':   'chileatiende.gob.cl',
    'municipalidadpaine.cl':          'paine.cl',
    'municipalidadpenaflor.cl':       'penaflor.cl',
    'municipalidadsanjosedemaipo.cl': 'sanjosedemaipo.cl',
    'municipalidadsanpedro.cl':       'sanpedro.cl',
    'municipalidadtalagante.cl':      'munitalagante.cl',
    'municipalidadtiltil.cl':         'tiltil.cl',
    'mlagranja.cl':                   'lagranja.cl',
    'www.mlagranja.cl':               'www.lagranja.cl',
    'lareina.cl':                     'www.lareina.cl',
    'munistgo.cl':                    'www.munistgo.cl',
    'ww2.recoleta.cl':                'www.recoleta.cl',
    'cerronavia.cl':                  'www.cerronavia.cl',
    'gobiernosantiago.cl':            'www.gobiernosantiago.cl',
    'penalolen.cl':                   'www.penalolen.cl',
}

PATH_404 = {
    'https://laflorida.cl/sitio/salud/':                            'https://laflorida.cl',
    'https://laflorida.cl/sitio/programas/programa-adulto-mayor/':  'https://laflorida.cl',
    'https://laflorida.cl/sitio/educacion/':                        'https://laflorida.cl',
    'https://laflorida.cl/sitio/direcciones-municipales/':          'https://laflorida.cl',
    'https://laflorida.cl/sitio/noticias_florida/extension-de-postulacion-al-beneficio-de-exencion-de-derechos-de-aseo/': 'https://laflorida.cl',
    'https://quilicura.cl/farmacia-municipal-solidaria/':           'https://quilicura.cl',
    'https://quilicura.cl/salud/':                                  'https://quilicura.cl',
    'https://quilicura.cl/adulto-mayor/':                           'https://quilicura.cl',
    'https://quilicura.cl/educacion/':                              'https://quilicura.cl',
    'https://quilicura.cl/desarrollo-social/':                      'https://quilicura.cl',
    'https://quilicura.cl/':                                        'https://quilicura.cl',
    'https://nunoa.cl/salud/':                                      'https://nunoa.cl',
    'https://nunoa.cl/adulto-mayor/':                               'https://nunoa.cl',
    'https://nunoa.cl/educacion/':                                  'https://nunoa.cl',
    'https://nunoa.cl/social/':                                     'https://nunoa.cl',
    'https://quintanormal.cl/salud/':                               'https://quintanormal.cl',
    'https://quintanormal.cl/adulto-mayor/':                        'https://quintanormal.cl',
    'https://quintanormal.cl/educacion/':                           'https://quintanormal.cl',
    'https://quintanormal.cl/social/':                              'https://quintanormal.cl',
    'https://lobarnechea.cl/educacion/':                            'https://lobarnechea.cl',
    'https://lobarnechea.cl/social/':                               'https://lobarnechea.cl',
    'https://loespejo.cl/adulto-mayor/':                            'https://loespejo.cl',
    'https://loespejo.cl/social/':                                  'https://loespejo.cl',
    'https://loprado.cl/social/':                                   'https://loprado.cl',
    'https://melipilla.cl/adulto-mayor/':                           'https://melipilla.cl',
    'https://municipalidadalhue.cl/salud/':                         'https://municipalidadalhue.cl',
    'https://municipalidadalhue.cl/adulto-mayor/':                  'https://municipalidadalhue.cl',
    'https://municipalidadalhue.cl/educacion/':                     'https://municipalidadalhue.cl',
    'https://municipalidadalhue.cl/social/':                        'https://municipalidadalhue.cl',
    'https://municipalidadcuracavi.cl/salud/':                      'https://municipalidadcuracavi.cl',
    'https://municipalidadcuracavi.cl/adulto-mayor/':               'https://municipalidadcuracavi.cl',
    'https://municipalidadcuracavi.cl/social/':                     'https://municipalidadcuracavi.cl',
    'https://mpirque.cl/salud/':                                    'https://mpirque.cl',
    'https://mpirque.cl/adulto-mayor/':                             'https://mpirque.cl',
    'https://mpirque.cl/educacion/':                                'https://mpirque.cl',
    'https://mpirque.cl/social/':                                   'https://mpirque.cl',
    'https://www.cerronavia.cl/adulto-mayor/':                      'https://www.cerronavia.cl',
    'https://www.cerronavia.cl/deporte/':                           'https://www.cerronavia.cl',
    'https://www.cerronavia.cl/social/':                            'https://www.cerronavia.cl',
    'https://www.penalolen.cl/salud/':                              'https://www.penalolen.cl',
    'https://www.penalolen.cl/veterinaria/':                        'https://www.penalolen.cl',
    'https://www.providencia.cl/adulto-mayor/':                     'https://tramites.providencia.cl',
    'https://www.providencia.cl/educacion/':                        'https://tramites.providencia.cl',
    'https://www.providencia.cl/salud/':                            'https://tramites.providencia.cl',
    'https://www.providencia.cl/social/':                           'https://tramites.providencia.cl',
    'https://www.providencia.cl/tarjeta-vecino/':                   'https://tramites.providencia.cl',
    'https://www.recoleta.cl/como-inscribirse/':                    'https://www.recoleta.cl',
    'https://www.sanbernardo.cl/adulto-mayor/':                     'https://www.sanbernardo.cl',
    'https://www.sanbernardo.cl/educacion/':                        'https://www.sanbernardo.cl',
    'https://www.sanbernardo.cl/salud/':                            'https://www.sanbernardo.cl',
    'https://www.sanbernardo.cl/social/':                           'https://www.sanbernardo.cl',
    'https://www.vitacura.cl/adulto-mayor/':                        'https://vitacura.cl',
    'https://temuco.cl/adulto-mayor':                               'https://temuco.cl',
    'https://concepcion.cl/educacion':                              'https://concepcion.cl',
    'https://lascondes.cl/beneficios/financiamiento-de-proyectos':  'https://lascondes.cl',
    'https://chileatiende.gob.cl/temas/aporte-familiar-permanente': 'https://chileatiende.gob.cl/fichas/130457-aumento-de-la-pension-garantizada-universal-pgu',
}

def fix_url(url):
    if not url:
        return url
    if url in PATH_404:
        return PATH_404[url]
    for bad, good in DOMAIN_FIX.items():
        if '://' + bad in url:
            url = url.replace('://' + bad, '://' + good)
            break
    return url

import os
csv_path = os.path.join(os.path.dirname(__file__), '..', 'datos-sheets', 'municipios.csv')

with open(csv_path, encoding='utf-8', newline='') as f:
    content = f.read()

lines = content.splitlines()
header = lines[0]
fieldnames = header.split(',')

changed = 0
new_lines = [header]
for line in lines[1:]:
    if not line.strip():
        continue
    # Parse CSV row carefully
    reader_obj = csv.reader([line])
    for parts in reader_obj:
        row = dict(zip(fieldnames, parts))
        for field in ['web', 'url']:
            orig = row.get(field, '')
            fixed = fix_url(orig)
            if fixed != orig:
                row[field] = fixed
                changed += 1
        # Re-serialize the row
        import io
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow([row.get(f, '') for f in fieldnames])
        new_lines.append(buf.getvalue().rstrip('\r\n'))

with open(csv_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(new_lines) + '\n')

print(f'CSV actualizado: {changed} URLs corregidas en {len(new_lines)-1} filas')
