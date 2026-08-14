#%%
import logging
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Diretório do projeto
BASE_DIR = Path(__file__).resolve().parent


# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# Carrega o .env do projeto
load_dotenv(BASE_DIR / ".env")

URL_DATA1 = os.getenv("URL_DATA1")

if not URL_DATA1:
    raise RuntimeError("A variável URL_DATA1 não foi encontrada no .env")


def salva_dados(html, nome_tabela):
    """
    Salva o HTML recebido na pasta landing.
    """
    pasta = BASE_DIR / "landing"
    pasta.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    arquivo_saida = (
        pasta / f"{timestamp}_{nome_tabela}.html"
    )

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Dados salvos em: %s", arquivo_saida)


def buscar_tabela(driver, xpath, nome_tabela):
    try:
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, xpath)
            )
        )

        html = tabela.get_attribute("outerHTML")

        if html:
            logger.info(
                "Tabela encontrada: %s",
                nome_tabela
            )
            return html

        logger.warning(
            "Tabela encontrada, mas sem HTML: %s",
            nome_tabela
        )
        return None

    except Exception:
        logger.exception(
            "Erro ao buscar tabela: %s",
            nome_tabela
        )
        return None


# Configura o Chrome/Chromium
options = Options()
options.add_argument("--lang=pt-BR")
options.add_argument("--window-size=1920,1080")
options.add_argument("--headless=new")

driver = webdriver.Chrome(options=options)

try:
    # Abre o site
    driver.get(URL_DATA1)

    # Busca Manobras previstas
    manobras_previstas = buscar_tabela(
        driver,
        "//h2[contains(normalize-space(), 'Manobras previstas')]/following::table[1]",
        "manobras_previstas"
    )

    if manobras_previstas:
        salva_dados(manobras_previstas, "manobras_previstas")

    # Busca Navios atracados
    navios_atracados = buscar_tabela(
        driver,
        "//h2[normalize-space()='Navios Atracados']/following::table[1]",
        "navios_atracados"
    )

    if navios_atracados:
        salva_dados(navios_atracados, "navios_atracados")

    # Busca Navios Fundeados
    navios_fundeados = buscar_tabela(
        driver,
        "//h2[normalize-space()='Navios Fundeados']/following::table[1]",
        "navios_fundeados"
    )

    if navios_fundeados:
        salva_dados(navios_fundeados, "navios_fundeados")

    # Busca Navios Previstos
    navios_previstos = buscar_tabela(
        driver,
        "//h2[normalize-space()='Navios Previstos']/following::table[1]",
        "navios_previstos"
    )

    if navios_previstos:
        salva_dados(navios_previstos, "navios_previstos")

    # Busca Manobras Realizadas
    manobras_realizadas = buscar_tabela(
        driver,
        "//h2[normalize-space()='Manobras Realizadas']/following::table[1]",
        "manobras_realizadas"
    )

    if manobras_realizadas:
        salva_dados(manobras_realizadas, "manobras_realizadas")

finally:
    driver.quit()
    logger.info("Navegador fechado")