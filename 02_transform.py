#%%

import pandas as pd
import os
from pathlib import Path
from datetime import datetime

pasta = Path("landing")

arquivos_manobras_previstas = pasta.glob("*_manobras_previstas.html")

today = datetime.now().strftime("%Y-%m-%d")
print(today)

#%%
arquivo = next(
    (
        arquivo
        for arquivo in arquivos_manobras_previstas
        if arquivo.name.startswith(today)
    ),
    None
)
print(arquivo)  

tabelas = pd.read_html(arquivo)

for i, tabela in enumerate(tabelas):

    if "Navio" in tabela.columns and "Manobra" in tabela.columns:
        print(f"Encontramos a tabela de manobras na posicao: {i}")
        df_manobras = tabela
        break

#%%
print(f'valor de i = {i}')
print(f'valor de tabela = {tabela}')
#%%
print(f'valor de # %%


colunas_manobras = [
    "Data",
    "Navio",
    "Manobra",
    "Berço",
    "Loa",
    "Boca",
    "Horário",
    "Calado",
    "Rota",
    "Bordo",
    "Rebocadores",
]

df_manobras = encontrar_tabela(
    tabelas,
    colunas_manobras
)

#%%
tabelas = pd.read_html(arquivo)
df_manobras = df_teste = tabelas[0]
type(df_manobras)
# %%
len(df_manobras)
# %%
df_manobras[0].shape
# %%
df_manobras.head(5)
# %%


#%%
tabelas = pd.read_html(arquivo)

print(f"Quantidade de tabelas: {len(tabelas)}")

for i, tabela in enumerate(tabelas):
    print(f"Tabela {i}: {tabela.shape}")
    print(tabela.columns.tolist())
# %%
df_teste = tabelas[0]
# %%
df_teste.shape
# %%
