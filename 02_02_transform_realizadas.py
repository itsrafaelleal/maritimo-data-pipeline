#%%
import pandas as pd
import unicodedata
from pathlib import Path
from datetime import datetime
from io import StringIO

# Diretório do projeto
BASE_DIR = Path(__file__).resolve().parent

# Diretório onde estão os arquivos de origem
pasta = BASE_DIR / "landing"

tabela_atual = "manobras_realizadas"

# Procura arquivos de manobras realizadas
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
#%%        ####    CRIA COLUNAS NOVAS    ####

df["data_processamento"] = datetime.now()
df["arquivo_origem"] = arquivo.name
df["hora"] = pd.to_datetime(
    df["arquivo_origem"].str[:19],
    format="%Y-%m-%d_%H-%M-%S",
    errors="coerce"
)

# normalizar e limpar o cabecalho do df

df.columns = df.columns.str.lower()
df.columns = [
    unicodedata.normalize('NFKD', col)
    .encode('ascii', 'ignore')
    .decode('utf-8')
    for col in df.columns
]
print("## NOME DAS COLUNAS ##")
print(df.columns)


#%%  ### NORMALIMAZAR DADOS ###

colunas = ['data', 'navio', 'manobra', 'berco', 'horario', 'calado',
       'rota', 'bordo', 'rebocadores']
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
df["hora"] = pd.to_datetime(
    df["arquivo_origem"].str[:19],
    format="%Y-%m-%d_%H-%M-%S",
    errors="coerce"
)

print(df.head(2))

#%% ### CRIAR SILVER E SALVA 

SILVER_DIR = BASE_DIR / "silver"

pasta_saida = SILVER_DIR / f"{tabela_atual}"

pasta_saida.mkdir(
    parents=True,
    exist_ok=True
)

snapshot = arquivo.stem.removesuffix(
    f"{tabela_atual}"
)

arquivo_saida = pasta_saida / f"{snapshot}.parquet"

df.to_parquet(
    arquivo_saida,
    engine="pyarrow",
    index=False
)
print(f"Parquet salvo em: {arquivo_saida}")
