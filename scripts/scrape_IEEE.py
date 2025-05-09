#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import os, time, json, re
import shutil

from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
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
LIMIT = 10
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'outputs')

GOOGLE_USER = os.getenv("GOOGLE_USER")
GOOGLE_PASS = os.getenv("GOOGLE_PASS")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR     = os.path.join(BASE_DIR, "data")
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")

def init_driver():
    options = webdriver.ChromeOptions()
    # mientras depuras, comenta la siguiente línea para VER el navegador
    # options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def set_download_dir(driver, path):
    """
    Usa Chrome DevTools Protocol para redirigir descargas
    a la carpeta indicada en `path`.
    """
    driver.execute_cdp_cmd(
        "Page.setDownloadBehavior",
        {
            "behavior": "allow",
            "downloadPath": os.path.abspath(path)
        }
    )


def renombrar_zip_descargado(download_dir, nombre_destino):
    """
    Espera a que un archivo .zip se descargue completamente en `download_dir`,
    y luego lo renombra como `nombre_destino`.
    """
    timeout = 90
    zip_file = None

    print(f"⏳ Esperando archivo .zip en: {os.path.abspath(download_dir)}")

    for _ in range(timeout):
        # Listo archivo zip que no estén en proceso de descarga
        archivos_zip = glob.glob(os.path.join(download_dir, "*.zip"))
        archivos_ok = [f for f in archivos_zip if not os.path.exists(f + ".crdownload")]

        if archivos_ok:
            # Toma el más reciente (por fecha de modificación)
            zip_file = max(archivos_ok, key=os.path.getmtime)
            break
        time.sleep(1)

    if not zip_file:
        raise TimeoutError("⚠️ No se encontró un archivo .zip descargado completamente en el tiempo esperado.")

    # Renombrar
    nuevo_nombre = os.path.join(download_dir, nombre_destino)
    shutil.move(zip_file, nuevo_nombre)
    print(f"✔ Archivo renombrado: {os.path.basename(zip_file)} → {nombre_destino}")


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
    """
    wait = WebDriverWait(driver, 20)

    # 1) Cambiar a la pestaña IEEE (índice 0) y lanzar la búsqueda
    driver.switch_to.window(driver.window_handles[0])
    driver.find_element(By.CLASS_NAME, "Typeahead-input").send_keys(QUERY)
    driver.find_element(By.CLASS_NAME, "fa-search").click()
    # driver.get(search_url)
    time.sleep(5)
    driver.find_element(By.ID, "dropdownPerPageLabel").click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div/div/div[3]/div/xpl-root/main/div/xpl-search-results/div/div[1]/div[1]/ul/li[2]/xpl-rows-per-page-drop-down/div/div/button[1]"))).click()

    i = 1

    while True:
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(1)
        #Se descargan los articulos
        set_download_dir(driver, "articles")
        driver.find_element(By.CLASS_NAME, "results-actions-selectall-checkbox").click()
        pdf_button = driver.find_element(By.XPATH,
                                         "/html/body/div[5]/div/div/div[3]/div/xpl-root/main/div/xpl-search-results/div/div[1]/div[1]/ul/li[1]/xpl-download-pdf/button")
        if pdf_button.is_enabled():
            pdf_button.click()
            time.sleep(2)
            driver.find_element(By.XPATH,
                                "/html/body/ngb-modal-window/div/div/div/section[2]/div/button[2]/span").click()
            try:
                close_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "modal-close")))
                close_btn.click()
            except TimeoutException:
                print("⚠️ No apareció el botón para cerrar el modal.")
        else:
            print("⚠️ El botón de descarga de artículos está deshabilitado en esta página.")

        nombre_zip = f"ieee_page_{i}.zip"
        renombrar_zip_descargado("articles", nombre_zip)

        # Esperar a que desaparezca el modal si sigue visible
        try:
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "modal-content"))
            )
        except TimeoutException:
            print("⚠️ El modal aún está visible después de 10 segundos, intentando de todos modos.")

        #Se descargan los CSV
        set_download_dir(driver, "data")
        wait.until(EC.element_to_be_clickable ((By.XPATH,
                            "/html/body/div[5]/div/div/div[3]/div/xpl-root/main/div/xpl-search-results/div/div[1]/div[1]/ul/li[3]/xpl-export-search-results/button"))).click()
        time.sleep(2)
        driver.find_element(By.XPATH,"/html/body/ngb-modal-window/div/div/div[2]/div/div[3]/button[2]").click()
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        try:
            next_btn = driver.find_element(By.CLASS_NAME,"next-btn")
            if not next_btn.is_enabled() or "disabled" in next_btn.get_attribute("class"):
                break
            next_btn.click()
            time.sleep(5)
            i += 1
        except NoSuchElementException:
            break

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    driver = init_driver()

    login_uni(driver)

    # Scraping en cada base
    todos = []
    todos += scrape_ieee(driver)



if __name__ == '__main__':
    main()
