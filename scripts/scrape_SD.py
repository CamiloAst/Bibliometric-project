#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    options.add_argument("--headless=new")
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
    zip_path = os.path.join(download_dir, "bulk-download.zip")
    nuevo_nombre = os.path.join(download_dir, nombre_destino)

        # Esperar a que se descargue completamente
    try:
        for _ in range(30):  # Máximo 30 segundos
            if os.path.exists(zip_path) and not os.path.exists(zip_path + ".crdownload"):
                break
            time.sleep(1)
        else:
            raise TimeoutError("El archivo bulk-download.zip no terminó de descargarse.")
    except TimeoutException:
        print("El archivo bulk-download.zip no terminó de descargarse.")
    # Renombrar (o mover a otra carpeta también sirve)
    shutil.move(zip_path, nuevo_nombre)


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

    # 3) Clic en Science Direct (DESCUBRIDOR)
    sd = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "/html/body/div[3]/div[2]/div[3]/div/div[2]/div/main/div[1]/div[5]/div/details[7]/div/article[16]/div/div/h3/a/span"
    )))
    sd.click()
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
    print("✔ Login en Science Direct completado")


def scrape_sd(driver):
    """
    1) Navega a la página de resultados de la búsqueda en Science Direct.
    """
    wait = WebDriverWait(driver, 20)

    driver.find_element(By.ID, "qs").send_keys(QUERY)
    driver.find_element(By.XPATH, "/html/body/div/div/div[1]/div[2]/div[2]/div/div/form/div[2]/button").click()
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[2]/div/div/div/section/div/div[2]/div[3]/div[1]/div[2]/div[3]/div[1]/ol/li[3]/a").click()
    time.sleep(1)

    # i = 1

    while True:
        driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[2]/div/div/div/section/div/div[2]/div[3]/div[1]/div[2]/div[1]/div[1]/span/span[1]/span[1]/div/div/label/span[1]").click()
        time.sleep(1)
        driver.find_element(By.CLASS_NAME,"download-all-link-text").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/div[2]/div/div[3]/button[2]").click()
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.find_element(By.CLASS_NAME, "modal-close-button-icon").click()
        time.sleep(1)
        driver.find_element(By.CLASS_NAME, "export-all-link-text").click()
        time.sleep(1)
        set_download_dir(driver, "data")
        driver.find_element(By.XPATH, "/html/body/div[5]/div/div/div/p/div/div/button[3]/span/span").click()
        time.sleep(1)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        try:
            next_btn = driver.find_element(By.XPATH,"/html/body/div[1]/div/div/div[2]/div/div/div/section/div/div[2]/div[3]/div[1]/div[2]/div[3]/div[2]/div/ol/li[3]/a/span")
            if not next_btn.is_enabled() or "disabled" in next_btn.get_attribute("class"):
                break
            next_btn.click()
            time.sleep(5)
            # i += 1
        except NoSuchElementException:
            break

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    driver = init_driver()

    login_uni(driver)

    # Scraping en cada base
    todos = []
    todos += scrape_sd(driver)



if __name__ == '__main__':
    main()
