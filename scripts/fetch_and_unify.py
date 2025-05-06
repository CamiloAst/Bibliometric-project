#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_and_unify.py

Busca en IEEE, SAGE y ScienceDirect la palabra clave "Computational Thinking",
extrae título, abstract, autores y año; detecta duplicados (por DOI o título)
y genera two archivos BibTeX en outputs/: unified.bib y duplicates.bib.
"""

import os
import requests
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

# Configuración
QUERY       = "Computational Thinking"
MAX_RECORDS = 200  # ajustar según necesidad
OUT_DIR     = os.path.join(os.path.dirname(__file__), '..', 'outputs')
IEEE_KEY    = os.getenv('IEEE_API_KEY')
ELSEVIER_KEY= os.getenv('ELSEVIER_API_KEY')

def fetch_ieee(query, max_records=MAX_RECORDS):
    if not IEEE_KEY:
        raise RuntimeError("Define IEEE_API_KEY en tus variables de entorno")
    url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    params = {
        'apikey': IEEE_KEY,
        'querytext': query,
        'max_records': max_records
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json().get('articles', [])
    resultados = []
    for art in data:
        resultados.append({
            'ENTRYTYPE': 'article',
            'ID'       : art.get('article_number',''),
            'title'    : art.get('title','').strip(),
            'abstract' : art.get('abstract','').strip(),
            'author'   : ' and '.join(a.get('full_name','') for a in art.get('authors',{}).get('authors',[])),
            'year'     : art.get('publication_year',''),
            'doi'      : art.get('doi','')
        })
    return resultados

def fetch_sciencedirect(query, max_records=MAX_RECORDS):
    if not ELSEVIER_KEY:
        raise RuntimeError("Define ELSEVIER_API_KEY en tus variables de entorno")
    url = "https://api.elsevier.com/content/search/sciencedirect"
    headers = {'X-ELS-APIKey': ELSEVIER_KEY}
    params = {
        'query': f"TITLE({query})",
        'count': max_records
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    entries = resp.json().get('search-results',{}).get('entry', [])
    resultados = []
    for item in entries:
        resultados.append({
            'ENTRYTYPE':'article',
            'ID'       : item.get('dc:identifier',''),
            'title'    : item.get('dc:title','').strip(),
            'abstract' : item.get('dc:description','').strip(),
            'author'   : item.get('authors','').replace(';', ' and '),
            'year'     : item.get('prism:coverDate','')[:4],
            'doi'      : item.get('prism:doi','')
        })
    return resultados

def fetch_sage(query, max_records=MAX_RECORDS):
    # Se usa Crossref para filtrar por editor SAGE Publications
    url = "https://api.crossref.org/works"
    params = {
        'query.bibliographic': query,
        'filter': 'publisher-name:SAGE Publications',
        'rows': max_records
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    items = resp.json().get('message',{}).get('items',[])
    resultados = []
    for it in items:
        resultados.append({
            'ENTRYTYPE':'article',
            'ID'       : it.get('DOI',''),
            'title'    : it.get('title',[''])[0].strip(),
            'abstract' : it.get('abstract','').strip().replace('\n',' '),
            'author'   : ' and '.join(
                f"{a.get('given','')} {a.get('family','')}".strip()
                for a in it.get('author',[])
            ),
            'year'     : str(it.get('issued',{}).get('date-parts',[[None]])[0][0] or '')
        })
    return resultados

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) Descargar de cada BD
    todos = []
    print("🔎 Buscando en IEEE…")
    todos += fetch_ieee(QUERY)
    print("🔎 Buscando en ScienceDirect…")
    todos += fetch_sciencedirect(QUERY)
    print("🔎 Buscando en SAGE…")
    todos += fetch_sage(QUERY)
    print(f"→ Total registros descargados: {len(todos)}")

    # 2) Detectar duplicados por DOI o título normalizado
    vistos, dupes = {}, []
    únicos = []
    for e in todos:
        clave = (e.get('doi') or e['title']).lower().strip()
        if clave in vistos:
            dupes.append(e)
        else:
            vistos[clave] = e
            únicos.append(e)

    print(f"✔ Registros únicos: {len(únicos)}")
    print(f"✔ Duplicados detectados: {len(dupes)}")

    # 3) Escribir BibTeX unificados y duplicados
    writer = BibTexWriter()
    db_u = BibDatabase(); db_u.entries = únicos
    db_d = BibDatabase(); db_d.entries = dupes

    fn_u = os.path.join(OUT_DIR, 'unified.bib')
    fn_d = os.path.join(OUT_DIR, 'duplicates.bib')
    with open(fn_u, 'w', encoding='utf-8') as f: f.write(writer.write(db_u))
    with open(fn_d, 'w', encoding='utf-8') as f: f.write(writer.write(db_d))

    print(f"→ Archivo unificado: {fn_u}")
    print(f"→ Archivo duplicados: {fn_d}")

if __name__ == '__main__':
    main()
