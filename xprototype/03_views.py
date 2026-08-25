#%%
import pandas as pd
from pathlib import Path

# Diretório do projeto
BASE_DIR = Path(__file__).resolve().parent

# Tabela que vou trabalhar
tabela_atual = "manobras_realizadas"

# Pasta da tabela na Silver
pasta = BASE_DIR / "silver" / tabela_atual

# Pega os arquivos Parquet
arquivos = list(pasta.glob("*.parquet"))

# Pega o arquivo mais recente
arquivo = max(arquivos, key=lambda x: x.stat().st_mtime)

print(f"Arquivo aberto: {arquivo.name}")

# Lê o Parquet
df = pd.read_parquet(arquivo)

#%% Visualização
"\n## PRIMEIRAS LINHAS ##"
df.head()

"\n## DIMENSÕES ##"
f"Linhas: {df.shape[0]}"
f"Colunas: {df.shape[1]}"

"\n## COLUNAS ##"
df.columns.tolist()

"\n## DTYPES ##"
df.dtypes