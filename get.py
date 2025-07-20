import time
import os
import shutil

import pandas as pd

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from io import StringIO
from pathlib import Path

load_dotenv()

def multiselect_set_selections(driver, element_name, labels) -> None:
    el = driver.find_element(By.NAME, element_name)
    for option in el.find_elements(By.TAG_NAME,'option'):
        if option.text in labels:
            option.click()

def ottieni_cartellino(data_folder:Path) -> None:
    output_folder = data_folder / 'input'
    if not output_folder.exists():
        output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / 'cartellino.xlsx'
    # https://presenze.unisa.it/
    driver = webdriver.Firefox()
    # driver = webdriver.Chrome()

    try:
        driver.get("https://presenze.unisa.it/")
        driver.find_element(By.LINK_TEXT, "Credenziali UNISA").click()
        username = driver.find_element(By.NAME, "_username")
        username.send_keys(os.getenv("USERNAME"))
        password = driver.find_element(By.NAME, "j_password")
        password.send_keys(os.getenv("PASSWORD"))
        driver.find_element(By.NAME, "_eventId_proceed").click()
        # WebDriverWait(driver, 100).until(EC.text_to_be_present_in_element((By.XPATH,"//title"), "Start Web"))
        time.sleep(10)
        driver.get("https://presenze.unisa.it/default.aspx?page=cartellino#dtfine=1767135600000&dtinizio=1735686000000&iddip=146187&view=full")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Successivo")))
        el = driver.find_element(By.ID, "1011_next")
        class_attr = el.get_attribute('class')
        class_names = class_attr.split(' ')
        driver.find_element(By.ID, "cookieChoiceDismiss").click()
        multiselect_set_selections(driver, "1011_length", ["100"])
        page = 1
        print(f"Processing page {page}")
        table = "<table>" + driver.find_element(By.ID, "1011").get_attribute('innerHTML') + "</table>"
        table = table.replace("<br><span>", "<br>&nbsp;&amp;-&amp;&nbsp;<span>")
        table = StringIO(table)
        df = pd.read_html(table)

        while "disabled" not in class_names:
            el = driver.find_element(By.LINK_TEXT, "Successivo")
            el.click()
            time.sleep(1)
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Successivo")))
            el = driver.find_element(By.ID, "1011_next")
            class_attr = el.get_attribute('class')
            class_names = class_attr.split(' ')
            page += 1
            print(f"Processing page {page}")
            table = "<table>" + driver.find_element(By.ID, "1011").get_attribute('innerHTML') + "</table>"
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

def main() -> None:
    data_folder = Path('data')
    if not data_folder.exists():
        data_folder.mkdir(parents=True, exist_ok=True)
    ottieni_cartellino(data_folder)


if __name__ == '__main__':
    main()