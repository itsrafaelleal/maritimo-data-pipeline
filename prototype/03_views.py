#%%
import pandas as pd
from pathlib import Path

# Diretório do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Tabela que vou trabalhar
tabela_atual = "manobras_previstas"

# Pasta da tabela na Silver
pasta_silver = BASE_DIR / "silver" / tabela_atual

# Pega os arquivos Parquet
arquivos = [
    arq for arq in pasta_silver.glob("*.parquet")
    if not arq.name.endswith("example.parquet")
]

# Pega o arquivo mais recente
arquivo_mais_recente = max(arquivos, key=lambda x: x.name)

print(f" Tabela selecionada: {tabela_atual}")
print(f" Arquivo mais recente aberto: {arquivo_mais_recente.name}")


# Lê o Parquet
df = pd.read_parquet(arquivo_mais_recente)

#%% Visualização
"\n## DIMENSÕES ##"
f"Linhas: {df.shape[0]}"
f"Colunas: {df.shape[1]}"

"\n## COLUNAS ##"
print(df.columns)

"\n## DTYPES ##"
df.dtypes
# %%
