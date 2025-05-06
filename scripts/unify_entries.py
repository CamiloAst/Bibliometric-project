#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unify_entries.py

Lee todos los .ris y .bib de data/raw/, unifica entradas únicas
y extrae los duplicados en outputs/.
"""
import os
import glob
import rispy
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

RAW_DIR     = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUT_DIR     = os.path.join(os.path.dirname(__file__), '..', 'outputs')
UNIFIED_FN  = os.path.join(OUT_DIR, 'unified.bib')
DUPES_FN    = os.path.join(OUT_DIR, 'duplicates.bib')

def load_ris(path):
    with open(path, encoding='utf-8') as fh:
        entries = rispy.load(fh)
    # transformar claves RIS → BibTeX
    bibs = []
    for e in entries:
        bib = {
            'ENTRYTYPE': e.get('type_of_reference', 'article'),
            'ID'       : e.get('id', ''),
            'title'    : ' '.join(e.get('title', [])),
            'author'   : ' and '.join(e.get('authors', [])),
            'year'     : e.get('year', ''),
            'abstract' : e.get('abstract', ''),
            'doi'      : e.get('doi', '')
        }
        bibs.append(bib)
    return bibs

def load_bib(path):
    with open(path, encoding='utf-8') as fh:
        db = bibtexparser.load(fh)
    return db.entries

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) Cargar todas las entradas
    all_entries = []
    for fn in glob.glob(os.path.join(RAW_DIR, '*.ris')):
        all_entries.extend(load_ris(fn))
    for fn in glob.glob(os.path.join(RAW_DIR, '*.bib')):
        all_entries.extend(load_bib(fn))

    # 2) Detectar duplicados (por DOI o título)
    seen     = {}
    duplicates = []
    for entry in all_entries:
        key = entry.get('doi','').lower().strip() or entry.get('title','').lower().strip()
        if not key:
            # si no hay DOI ni título, lo consideramos único igual
            key = entry.get('ID','') + str(hash(frozenset(entry.items())))
        if key in seen:
            duplicates.append(entry)
        else:
            seen[key] = entry

    # 3) Escribir unified.bib
    db_u = BibDatabase()
    db_u.entries = list(seen.values())
    writer = BibTexWriter()
    with open(UNIFIED_FN, 'w', encoding='utf-8') as fh:
        fh.write(writer.write(db_u))

    # 4) Escribir duplicates.bib
    db_d = BibDatabase()
    db_d.entries = duplicates
    with open(DUPES_FN, 'w', encoding='utf-8') as fh:
        fh.write(writer.write(db_d))

    print(f"✔ Unificados: {len(db_u.entries)} registros → {UNIFIED_FN}")
    print(f"✔ Duplicados: {len(db_d.entries)} registros → {DUPES_FN}")

if __name__ == '__main__':
    main()
