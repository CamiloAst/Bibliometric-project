#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, time, json, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

# — Parámetros —
QUERY = "Computational Thinking"
LIMIT = 30
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'outputs')

GOOGLE_USER = os.getenv("GOOGLE_USER")
GOOGLE_PASS = os.getenv("GOOGLE_PASS")


def init_driver():
    options = webdriver.ChromeOptions()
    # mientras depuras, comenta la siguiente línea para VER el navegador
    # options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def login_uni(driver):
    wait = WebDriverWait(driver, 20)

    # 1) CRAI/databases
    driver.get("https://library.uniquindio.edu.co/databases")
    time.sleep(3)

    # 2) Desplegar Facultad de Ingeniería
    eng = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "/html/body/div[3]/div[2]/div[3]/div/div[2]/div/main"
        "/div[1]/div[5]/div/details[7]/summary"
    )))
    eng.click()
    time.sleep(1)

    # 3) Clic en IEEE Xplore
    ieee = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "/html/body/div[3]/div[2]/div[3]/div/div[2]/div/main"
        "/div[1]/div[5]/div/details[7]/div/article[7]/div/div/h3/a/span"
    )))
    ieee.click()
    time.sleep(2)

    # 4) Botón Google SSO
    google_btn = wait.until(EC.element_to_be_clickable((By.ID, "btn-google")))
    google_btn.click()
    time.sleep(2)

    # 5) Credenciales de Google
    wait.until(EC.element_to_be_clickable((By.ID, "identifierId"))).send_keys(GOOGLE_USER)
    driver.find_element(By.ID, "identifierNext").click()
    wait.until(EC.element_to_be_clickable((By.NAME, "Passwd"))).send_keys(GOOGLE_PASS)
    driver.find_element(By.ID, "passwordNext").click()

    # 6) Esperar campo de búsqueda de IEEE
    wait.until(EC.presence_of_element_located((
        By.XPATH,
        "/html/body/div[5]/div/div/div[3]/div/xpl-root/header/xpl-header/div/div[2]/div[2]/xpl-search-bar-migr/div/form/div[2]/div/div[1]/xpl-typeahead-migr/div/input"
    )))
    print("✔ Login en IEEE Xplore completado")

    # 7) Abrir CRAI/databases en nueva pestaña para seguir con ScienceDirect y SAGE
    driver.execute_script("window.open('https://library.uniquindio.edu.co/databases','_blank');")
    # mantenemos la pestaña 0 en IEEE y pestaña 1 en CRAI
    driver.switch_to.window(driver.window_handles[1])
    print("✔ CRAI listo en pestaña secundaria")


def scrape_ieee(driver):
    """
    1) Navega a la página de resultados de la búsqueda en IEEE.
    2) Espera que cargue el JSON embebido.
    3) Extrae hasta LIMIT artículos desde global.document.metadata.
    """
    wait = WebDriverWait(driver, 20)

    # 1) Cambiar a la pestaña IEEE (índice 0) y lanzar la búsqueda
    driver.switch_to.window(driver.window_handles[0])
    search_url = (
        "https://ieeexplore.ieee.org/search/searchresult.jsp"
        f"?queryText={QUERY.replace(' ', '%20')}"
    )
    driver.get(search_url)
    time.sleep(3)

    # 2) Esperar a que el script con global.document.metadata esté en el DOM
    wait.until(lambda d: "global.document.metadata" in d.page_source)

    # 3) Extraerlo con regex
    html = driver.page_source
    m = re.search(r'global\.document\.metadata\s*=\s*(\{.*?\});', html, re.S)
    if not m:
        print("⚠ No encontré el metadata JSON en IEEE después de la búsqueda.")
        return []
    data = json.loads(m.group(1))

    # 4) Parsear registros
    recs = []
    for art in data.get("records", [])[:LIMIT]:
        recs.append({
            'ENTRYTYPE':'article',
            'ID'       : art.get('articleNumber',''),
            'title'    : art.get('documentTitle','').strip(),
            'author'   : ' and '.join(a.get('preferredName','') for a in art.get('authors',[])),
            'year'     : art.get('publicationYear',''),
            'abstract' : art.get('abstract','').strip(),
            'doi'      : art.get('doi','')
        })

    print(f"✔ IEEE: {len(recs)} artículos extraídos")
    return recs


def scrape_sciencedirect(driver):
    """Pestaña 1 -> CRAI -> abrir ScienceDirect -> buscar -> parsear."""
    wait = WebDriverWait(driver, 20)

    # 1) Desde CRAI, desplegar Ingeniería de nuevo
    eng = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//h3[contains(., 'Facultad de Ingeniería')]"
    )))
    eng.click();
    time.sleep(1)

    # 2) Clic en ScienceDirect
    sd = wait.until(EC.element_to_be_clickable((
        By.LINK_TEXT, "Science Direct"
    )))
    sd.click();
    time.sleep(3)

    # 3) Pestaña nueva o misma pestaña depende del proxy; asumimos nueva
    driver.switch_to.window(driver.window_handles[-1])
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='search']")))

    # 4) Buscar y extraer enlaces
    inp = driver.find_element(By.CSS_SELECTOR, "input[id*='search']")
    inp.clear();
    inp.send_keys(QUERY);
    inp.send_keys("\n")
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "lxml")
    links = []
    for a in soup.select("a[href^='/science/article/pii/']"):
        url = "https://www.sciencedirect.com" + a['href'].split("?")[0]
        if url not in links:
            links.append(url)
    recs = []
    for link in links[:LIMIT]:
        driver.get(link);
        time.sleep(2)
        ds = BeautifulSoup(driver.page_source, "lxml")

        def meta(name):
            tag = ds.find("meta", {'name': name})
            return tag and tag.get('content', '').strip() or ''

        recs.append({
            'ENTRYTYPE': 'article',
            'ID': meta('citation_doi') or link.split("/")[-1],
            'title': meta('citation_title'),
            'author': ' and '.join(m['content'] for m in ds.find_all('meta', {'name': 'citation_author'})),
            'year': (meta('citation_publication_date') or "").split("-")[0],
            'abstract': meta('citation_abstract'),
            'doi': meta('citation_doi')
        })
    print(f"✔ ScienceDirect: {len(recs)} artículos")
    return recs


def scrape_sage(driver):
    """Desde la misma pestaña del último proxy (ScienceDirect), volvemos a CRAI y luego SAGE."""
    wait = WebDriverWait(driver, 20)

    # 1) Volver a CRAI en pestaña 1
    driver.switch_to.window(driver.window_handles[1])
    time.sleep(1)

    # 2) Desplegar Ingeniería
    eng = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//h3[contains(., 'Facultad de Ingeniería')]"
    )))
    eng.click();
    time.sleep(1)

    # 3) Clic en SAGE Publications
    sage = wait.until(EC.element_to_be_clickable((
        By.LINK_TEXT, "SAGE Publications"
    )))
    sage.click();
    time.sleep(3)

    # 4) Pasar a la nueva pestaña de SAGE
    driver.switch_to.window(driver.window_handles[-1])
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#AllField")))

    # 5) Buscar
    inp = driver.find_element(By.CSS_SELECTOR, "input#AllField")
    inp.clear();
    inp.send_keys(QUERY);
    inp.send_keys("\n")
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "lxml")
    links = ["https://journals.sagepub.com" + a['href']
             for a in soup.select("a.search-result-title-link")]
    recs = []
    for link in links[:LIMIT]:
        driver.get(link);
        time.sleep(2)
        ds = BeautifulSoup(driver.page_source, "lxml")

        def meta(name):
            tag = ds.find("meta", {'name': name})
            return tag and tag.get('content', '').strip() or ''

        recs.append({
            'ENTRYTYPE': 'article',
            'ID': meta('citation_doi') or link.split("/")[-1],
            'title': meta('citation_title'),
            'author': ' and '.join(m['content'] for m in ds.find_all('meta', {'name': 'citation_author'})),
            'year': (meta('citation_publication_date') or "").split("-")[0],
            'abstract': meta('citation_abstract'),
            'doi': meta('citation_doi')
        })
    print(f"✔ SAGE: {len(recs)} artículos")
    return recs


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    driver = init_driver()

    # Login y primer pestaña IEEE + segunda pestaña CRAI
    login_uni(driver)

    # Scraping en cada base
    todos = []
    todos += scrape_ieee(driver)
    todos += scrape_sciencedirect(driver)
    todos += scrape_sage(driver)

    driver.quit()

    # Unificar + duplicados
    vistos, dupes, únicos = {}, [], []
    for e in todos:
        clave = (e.get('doi') or e['title']).lower().strip()
        if clave in vistos:
            dupes.append(e)
        else:
            vistos[clave] = e
            únicos.append(e)

    # Escribir BibTeX
    writer = BibTexWriter()
    db_u, db_d = BibDatabase(), BibDatabase()
    db_u.entries, db_d.entries = únicos, dupes
    with open(os.path.join(OUT_DIR, 'unified.bib'), 'w', encoding='utf-8') as f:
        f.write(writer.write(db_u))
    with open(os.path.join(OUT_DIR, 'duplicates.bib'), 'w', encoding='utf-8') as f:
        f.write(writer.write(db_d))

    print(f"✔ Unificados: {len(únicos)}, Duplicados: {len(dupes)}")
    print("✔ Archivos generados en outputs/")


if __name__ == '__main__':
    main()
