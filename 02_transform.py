# %%
import pandas as pd
from pathlib import Path
from datetime import datetime
from io import StringIO


# Diretório onde estão os arquivos de origem
pasta = Path("landing")


# Procura arquivos de manobras previstas
arquivos_manobras_previstas = pasta.glob(
    "*_manobras_previstas.html"
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


# Valida se o arquivo foi encontrado
if arquivo is None:
    raise FileNotFoundError(
        f"Nenhum arquivo encontrado para {today}"
    )


print(f"Arquivo encontrado: {arquivo}")


# Lê o HTML como texto
with open(arquivo, "r", encoding="latin1") as f:
    html = f.read()


# Corrige o problema de encoding
html = html.encode("latin1").decode("utf-8")


# Converte o texto HTML em um objeto semelhante a arquivo
# para que o pandas possa fazer a leitura
tabelas = pd.read_html(StringIO(html))


print(f"Tabelas encontradas: {len(tabelas)}")


# Procura a tabela de manobras
df = None

for i, tabela in enumerate(tabelas):

    if "Navio" in tabela.columns and "Manobra" in tabela.columns:
        print(
            f"Encontramos a tabela de manobras na posição: {i}"
        )

        df = tabela
        break


# Valida se a tabela foi encontrada
if df is None:
    raise ValueError(
        "Tabela de manobras não encontrada no HTML."
    )

#%%
print(df.head(10))
print("-xxx--xxxxx--xxx--xxxxx--xxx--xxxxx-")
print("-xxx--xxxxx--xxx--xxxxx--xxx--xxxxx-")
#%%
df.columns = df.columns.str.lower()

#%%
df.dtypes
#%%
df
colunas = ['data', 'horário', 'manobra', 'berço', 'bordo', 'navio',
            'rota', 'calado', 'situação']

df[colunas] = df[colunas].apply(
    lambda col: col.str.replace('[áàãâäÁÀÃÂÄ]', 'a', regex=True)
                     .str.replace('[éèêëÉÈÊË]', 'e', regex=True)
                     .str.replace('[íìîïÍÌÎÏ]', 'i', regex=True)
                     .str.replace('[óòõôöÓÒÕÔÖ]', 'o', regex=True)
                     .str.replace('[úùûüÚÙÛÜ]', 'u', regex=True)
                     .str.replace('[çÇ]', 'c', regex=True)
                     .str.lower()
)

df["data_processamento"] = datetime.now()
df["arquivo_origem"] = arquivo.name

# Visualiza os primeiros registros
print(df.head(10))
print("-xxx--xxxxx--xxx--xxxxx--xxx--xxxxx-")
print("-xxx--xxxxx--xxx--xxxxx--xxx--xxxxx-")
# %%