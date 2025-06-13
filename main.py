import time
import os
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

def main():
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
        p = WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.LINK_TEXT, "Successivo")))
        print(driver.page_source)
    except TimeoutException as e:
        print(f"Timeout {e}")
    finally:
        driver.close()
        driver.quit()

    # driver.get("https://presenze.unisa.it/")
    #
    #     driver.find_element(By.LINK_TEXT,"Credenziali UNISA").click()
    #     username = driver.find_element(By.NAME, "_username")
    #     username.send_keys()
    #     password = driver.find_element(By.NAME, "j_password")
    #     password.send_keys()
    #     driver.find_element(By.NAME, "_eventId_proceed").click()
    #     time.sleep(10)
    #     driver.get("https://presenze.unisa.it/default.aspx?page=cartellino#dtfine=1767135600000&dtinizio=1735686000000&iddip=146187&view=full")
    #     try:
    #         p = WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.LINK_TEXT,"Successivo")))
    #         print(driver.page_source)
    #     except TimeoutException as e:
    #         print(f"Timeout {e}")
    #     finally:
    #         driver.close()
    #         driver.quit()
    # else:
    #     print("No")
    #     driver.close()
    #     driver.quit()

if __name__ == '__main__':
    main()