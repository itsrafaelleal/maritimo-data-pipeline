#%%
import pandas as pd
import unicodedata
from pathlib import Path
from datetime import datetime
from io import StringIO


# Pasta do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Pasta onde estão os arquivos de origem
pasta = BASE_DIR / "landing_raw"
tabela_atual = "manobras_previstas"
# Procura arquivos de manobras previstas
arquivos = pasta.glob(
    f"*{tabela_atual}.html"
)

# Data de hoje
today = datetime.now().strftime("%Y-%m-%d")


# Encontra o arquivo referente à data de hoje
arquivo = next(
    (
        arquivo
        for arquivo in arquivos
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

df = tabelas[0]
col = df.columns
print("df colunas ="f'{col}')

# normalizar e limpar o cabecalho do df

df.columns = df.columns.str.lower()
df.columns = [
    unicodedata.normalize('NFKD', col)
    .encode('ascii', 'ignore')
    .decode('utf-8')
    for col in df.columns
]
# cria colunas dividir a coluna horario em duas

df[['hora', 'status']] = df['horario'].str.extract(
    r'(?:(\d{2}:\d{2})\s+)?(\w+)'
)
print("## NOME DAS COLUNAS ##")
print(df.columns)

  ### NORMALIMAZAR DADOS ###

colunas = ['data', 'horario', 'manobra', 'berco', 'bordo', 'navio', 'rota',
            'calado', 'situacao', 'hora', 'status']

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

#%% ### CRIAR SILVER E SALVA 


SILVER_DIR = BASE_DIR / "silver"

pasta_saida = SILVER_DIR / "manobras_previstas"

pasta_saida.mkdir(
    parents=True,
    exist_ok=True
)

snapshot = arquivo.stem.removesuffix(
    "_manobras_previstas"
)

arquivo_saida = pasta_saida / f"{snapshot}.parquet"

df.to_parquet(
    arquivo_saida,
    engine="pyarrow",
    index=False
)

print(f"Parquet salvo em: {arquivo_saida}")
