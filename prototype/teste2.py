#%%
from pathlib import Path
import pandas as pd
from datetime import datetime

# Diretório do projeto
BASE_DIR = Path(__file__).resolve().parent

# Diretório onde estão os arquivos de origem
pasta = BASE_DIR.parent / "landing_raw"
tipos_tabela = ["manobras_previstas.html", "manobras_realizadas.html", "navios_atracados.html", "navios_fundeados.html", "navios_previstos.html"]

# Procura arquivos de manobras previstas
arquivos_manobras_previstas = pasta.glob(
    "*manobras_realizadas.html"
)

# Data de hoje
today = datetime.now().strftime("%Y-%m-%d")


# Encontra o arquivo referente à data de hoje
arquivo = next(
    (
        arquivo
        for arquivo in arquivos_manobras_previstas
        if arquivo.name.startswith(today)
    ),
    None
)
# %%
