import socket
import time
from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from cartellino.config import Config
from cartellino.credentials import get_credentials

def multiselect_set_selections(driver, element_name, labels) -> None:
    el = driver.find_element(By.NAME, element_name)
    for option in el.find_elements(By.TAG_NAME,'option'):
        if option.text in labels:
            option.click()

METODI_AUTENTICAZIONE = ["Credenziali UNISA", "SPID", "CIE"]

def is_on_unisa_network(host: str = "172.16.19.250", port: int = 22, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, OSError):
        return False

def scegli_metodo_autenticazione() -> str:
    su_rete_unisa = is_on_unisa_network()
    metodi_disponibili = [m for m in METODI_AUTENTICAZIONE if m != "Credenziali UNISA" or su_rete_unisa]

    print("\nScegli il metodo di autenticazione:")
    if not su_rete_unisa:
        print("  (Credenziali UNISA non disponibile: non sei sulla rete universitaria)")
    for i, metodo in enumerate(metodi_disponibili, 1):
        print(f"  {i}. {metodo}")
    while True:
        scelta = input(f"Inserisci il numero (1-{len(metodi_disponibili)}): ").strip()
        if scelta.isdigit() and 1 <= int(scelta) <= len(metodi_disponibili):
            return metodi_disponibili[int(scelta) - 1]
        print("Scelta non valida, riprova.")

def ottieni_cartellino(data_folder:Path) -> None:
    config = Config.load(data_folder=data_folder)
    current_year = config.current_year
    start_date = datetime(year=current_year, month=1, day=1)
    end_date = datetime(year=current_year, month=12, day=31)
    headless = config.headless
    output_file = config.input_folder / 'cartellino.feather'

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
            credentials = get_credentials()
            if credentials is None:
                raise RuntimeError(
                    "Credenziali UNISA non configurate. Impostale nel keyring di sistema "
                    "(cartellino.credentials.set_credentials) oppure tramite il file '.env' legacy."
                )
            username_value, password_value = credentials
            driver.find_element(By.LINK_TEXT, "Credenziali UNISA").click()
            time.sleep(1)
            username = driver.find_element(By.ID, "_username")
            username.send_keys(username_value)
            password = driver.find_element(By.ID, "password")
            password.send_keys(password_value)
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
        df.reset_index(drop=True).to_feather(output_file)
        print(f"Cartellino salvato in '{output_file}'")
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