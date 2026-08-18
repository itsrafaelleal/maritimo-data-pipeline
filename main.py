#%%
from pathlib import Path
import pandas as pd
from datetime import datetime

# Diretório do projeto
BASE_DIR = Path(__file__).resolve().parent

today = datetime.now().strftime("%Y-%m-%d")

# Caminho usando BASE_DIR
parquet = BASE_DIR / "silver" / "manobras_previstas" / f"{today}_16-39-56.parquet"

df = pd.read_parquet(parquet)