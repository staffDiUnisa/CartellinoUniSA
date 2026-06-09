import os
import time
from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()

def multiselect_set_selections(driver, element_name, labels) -> None:
    el = driver.find_element(By.NAME, element_name)
    for option in el.find_elements(By.TAG_NAME,'option'):
        if option.text in labels:
            option.click()

METODI_AUTENTICAZIONE = ["Credenziali UNISA", "SPID", "CIE"]

def scegli_metodo_autenticazione() -> str:
    print("\nScegli il metodo di autenticazione:")
    for i, metodo in enumerate(METODI_AUTENTICAZIONE, 1):
        print(f"  {i}. {metodo}")
    while True:
        scelta = input(f"Inserisci il numero (1-{len(METODI_AUTENTICAZIONE)}): ").strip()
        if scelta.isdigit() and 1 <= int(scelta) <= len(METODI_AUTENTICAZIONE):
            return METODI_AUTENTICAZIONE[int(scelta) - 1]
        print("Scelta non valida, riprova.")

def ottieni_cartellino(data_folder:Path) -> None:
    current_year = int(os.environ["CURRENT_YEAR"])
    start_date = datetime(year=current_year, month=1, day=1)
    end_date = datetime(year=current_year, month=12, day=31)
    output_folder = data_folder / str(current_year) / 'input'
    headless = os.getenv("HEADLESS") == "True"
    if not output_folder.exists():
        output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / 'cartellino.xlsx'

    metodo = scegli_metodo_autenticazione()

    WINDOW_SIZE = "800,600"
    chrome_options = Options()
    if headless and metodo == "Credenziali UNISA":
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://presenze.unisa.it/")

        if metodo == "Credenziali UNISA":
            driver.find_element(By.LINK_TEXT, "Credenziali UNISA").click()
            time.sleep(1)
            username = driver.find_element(By.ID, "_username")
            username.send_keys(os.environ["USERNAME"])
            password = driver.find_element(By.ID, "password")
            password.send_keys(os.environ["PASSWORD"])
            driver.find_element(By.NAME, "_eventId_proceed").click()
            time.sleep(10)
        else:
            driver.find_element(By.LINK_TEXT, metodo).click()
            print(f"\nAutenticazione {metodo}: completa il login nel browser, poi attendi.")
            print("Selenium riprenderà il controllo automaticamente quando sarà raggiunta la pagina principale.\n")
            # Attendi fino a 10 minuti che l'utente completi il login
            WebDriverWait(driver, 600).until(
                EC.url_contains("presenze.unisa.it/default.aspx")
            )
        dtinizio=int(start_date.timestamp()*1000)
        dtfine=int(end_date.timestamp()*1000)
        driver.get(f"https://presenze.unisa.it/default.aspx?page=cartellino#dtfine={dtfine}&dtinizio={dtinizio}&iddip=146187&view=full")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Successivo")))
        el = driver.find_element(By.ID, "1011_next")
        class_names = (el.get_attribute('class') or "").split(' ')
        driver.find_element(By.ID, "cookieChoiceDismiss").click()
        multiselect_set_selections(driver, "1011_length", ["100"])
        page = 1
        print(f"Processing page {page}")
        table = "<table>" + (driver.find_element(By.ID, "1011").get_attribute('innerHTML') or "") + "</table>"
        table = table.replace("<br><span>", "<br>&nbsp;&amp;-&amp;&nbsp;<span>")
        table = StringIO(table)
        df = pd.read_html(table)

        while "disabled" not in class_names:
            el = driver.find_element(By.LINK_TEXT, "Successivo")
            el.click()
            time.sleep(1)
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Successivo")))
            el = driver.find_element(By.ID, "1011_next")
            class_names = (el.get_attribute('class') or "").split(' ')
            page += 1
            print(f"Processing page {page}")
            table = "<table>" + (driver.find_element(By.ID, "1011").get_attribute('innerHTML') or "") + "</table>"
            table = table.replace("<br><span>", "<br>&nbsp;&amp;-&amp;&nbsp;<span>")
            table = StringIO(table)
            df.extend(pd.read_html(table))
        df = pd.concat(df, ignore_index=True)
        df.to_excel(output_file, index=False)
    except TimeoutException as e:
        print(f"Timeout {e}")
    finally:
        driver.close()
        driver.quit()

def run():
    data_folder = Path('data')
    if not data_folder.exists():
        data_folder.mkdir(parents=True, exist_ok=True)
    ottieni_cartellino(data_folder)

def main() -> None:
    run()

if __name__ == '__main__':
    main()