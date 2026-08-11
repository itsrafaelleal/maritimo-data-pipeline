#%%

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


load_dotenv()
URL_DATA1 = os.getenv("URL_DATA1")


# Configura o Chrome
options = Options()
options.add_argument("--lang=pt-BR")
options.add_argument("--window-size=1920,1080")

# Abre o navegador
driver = webdriver.Chrome(options=options)

# Abre o site
driver.get(URL_DATA1)

# Espera a página até encontrar os elementos

manobras_previstas = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located(
        (By.XPATH, "//h2[contains(normalize-space(), 'Manobras previstas')]/following::table[1]" )))
manobras_previstas = manobras_previstas.get_attribute("outerHTML") #"outerHTML""innerHTML"

navios_fundeados = driver.find_element(
    By.XPATH, "//h2[normalize-space()='Navios Fundeados']/following::table[1]"
)
navios_fundeados = navios_fundeados.get_attribute("outerHTML")

navios_previstos = driver.find_element(
    By.XPATH,
    "//h2[normalize-space()='Navios Previstos']/following::table[1]"
)
navios_previstos = navios_previstos.get_attribute("outerHTML")

html = "\n".join([
    manobras_previstas,
    navios_fundeados,
    navios_previstos
])


#%%
# Cria a pasta
pasta = Path("landing")
pasta.mkdir(exist_ok=True)

# Nome do arquivo com data e hora
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
arquivo_saida = pasta / f"pagina_{timestamp}.html"

with open(arquivo_saida, "w", encoding="utf-8") as f:
    f.write(html)

# Fecha o navegador
driver.quit()


# %%
