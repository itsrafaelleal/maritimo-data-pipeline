#%%
import io
import logging
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# ==============================================================================
# 1. CONFIGURAÇÕES GERAIS E LOGGING
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
LANDING_DIR = BASE_DIR / "landing_raw"
SILVER_DIR = BASE_DIR / "silver"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==============================================================================
# 2. FUNÇÕES AUXILIARES DE LIMPEZA E PADRONIZAÇÃO
# ==============================================================================
def normalizar_texto(valor: object) -> object:
    """
    Remove acentos, caracteres especiais e converte texto para minúsculo.
    Mantém valores nulos (NaN/None) inalterados.
    """
    if pd.isna(valor):
        return valor
    texto = str(valor).strip()
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
    )


def padronizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza os nomes das colunas: remove acentos, substitui espaços
    por underscores e converte para minúsculo (snake_case).
    """
    novas_colunas = []
    for col in df.columns:
        col_limpa = normalizar_texto(col)
        col_limpa = col_limpa.replace(" - ", "_").replace(" ", "_").replace("-", "_")
        novas_colunas.append(col_limpa)
    df.columns = novas_colunas
    return df


# ==============================================================================
# 3. REGRAS DE TRANSFORMAÇÃO ESPECÍFICAS POR TABELA
# ==============================================================================
def _transformar_manobras_previstas(df: pd.DataFrame, arquivo_origem: str) -> pd.DataFrame:
    """
    Regra específica para 'manobras_previstas':
    1. Extrai hora e status a partir do campo 'horario'.
    2. Cria o timestamp completo 'data_hora_manobra_prevista'.
    3. Força os tipos de dados via dicionário de esquema.
    """
    # 1. Extração de hora e status
    if "horario" in df.columns:
        df[["hora", "status"]] = df["horario"].str.extract(
            r"(?:(\d{2}:\d{2})\s+)?(\w+)"
        )

    # 2. Criação da coluna unificada 'data_hora_manobra_prevista'
    if "data" in df.columns and "hora" in df.columns:
        df["data_hora_manobra_prevista"] = pd.to_datetime(
            df["data"].astype(str) + " " + df["hora"].astype(str),
            format="%d/%m/%Y %H:%M",
            errors="coerce"
        )

    # 3. Conversão da coluna 'data' isolada para datetime
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")

    # 4. Conversão numérica de LOA e BOCA
    for col_num in ["loa", "boca"]:
        if col_num in df.columns:
            df[col_num] = pd.to_numeric(
                df[col_num].astype(str).str.replace(",", "."),
                errors="coerce"
            ).astype("Int64")

    # 5. Dicionário para forçar os tipos textuais das demais colunas
    tipos_texto = {
        "horario": "string",
        "manobra": "string",
        "berco": "string",
        "bordo": "string",
        "navio": "string",
        "rota": "string",
        "calado": "string",
        "situacao": "string",
        "hora": "string",
        "status": "string",
    }
    for col, tipo in tipos_texto.items():
        if col in df.columns:
            df[col] = df[col].astype(tipo)

    return df


def _transformar_manobras_realizadas(df: pd.DataFrame, arquivo_origem: str) -> pd.DataFrame:
    """
    Regra específica para 'manobras_realizadas':
    1. Extrai hora e status a partir do campo 'horario'.
    2. Cria o timestamp completo 'data_hora_manobra_realizada'.
    3. Força os tipos de dados via dicionário de esquema.
    """
    # 1. Extração de hora e status do campo 'horario' (ex: '15:15 ATB')
    if "horario" in df.columns:
        df[["hora", "status"]] = df["horario"].str.extract(
            r"(?:(\d{2}:\d{2})\s+)?(\w+)"
        )

    # 2. Criação da coluna unificada 'data_hora_manobra_realizada'
    if "data" in df.columns and "hora" in df.columns:
        df["data_hora_manobra_realizada"] = pd.to_datetime(
            df["data"].astype(str) + " " + df["hora"].astype(str),
            format="%d/%m/%Y %H:%M",
            errors="coerce"
        )

    # 3. Conversão da coluna 'data' isolada para datetime
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")

    # 4. Conversão numérica de LOA e BOCA
    for col_num in ["loa", "boca"]:
        if col_num in df.columns:
            df[col_num] = pd.to_numeric(
                df[col_num].astype(str).str.replace(",", "."),
                errors="coerce"
            ).astype("Int64")

    # 5. Dicionário para forçar os tipos textuais das demais colunas
    tipos_texto = {
        "navio": "string",
        "manobra": "string",
        "berco": "string",
        "horario": "string",
        "calado": "string",
        "rota": "string",
        "bordo": "string",
        "rebocadores": "string",
        "hora": "string",
        "status": "string",
    }
    for col, tipo in tipos_texto.items():
        if col in df.columns:
            df[col] = df[col].astype(tipo)

    return df


def _transformar_navios_atracados(df: pd.DataFrame, arquivo_origem: str) -> pd.DataFrame:
    """
    Regra específica para 'navios_atracados':
    1. Renomeia e converte coluna de data/hora de atracagem.
    2. Adiciona a coluna 'situacao' como 'atracado'.
    """
    if "data_hora" in df.columns:
        df = df.rename(columns={"data_hora": "data_hora_atracagem"})
    
    if "data_hora_atracagem" in df.columns:
        df["data_hora_atracagem"] = pd.to_datetime(
            df["data_hora_atracagem"],
            format="%d/%m/%Y - %H:%M",
            errors="coerce"
        )

    df["situacao"] = "atracado"
    df["situacao"] = df["situacao"].astype("string")
    return df


def _transformar_navios_fundeados(df: pd.DataFrame, arquivo_origem: str) -> pd.DataFrame:
    """
    Regra específica para 'navios_fundeados':
    1. Renomeia e converte coluna de data/hora de fundeio.
    2. Adiciona a coluna 'situacao' como 'fundeado'.
    """
    if "data_hora" in df.columns:
        df = df.rename(columns={"data_hora": "data_hora_fundeado"})
    
    if "data_hora_fundeado" in df.columns:
        df["data_hora_fundeado"] = pd.to_datetime(
            df["data_hora_fundeado"],
            format="%d/%m/%Y - %H:%M",
            errors="coerce"
        )

    df["situacao"] = "fundeado"
    df["situacao"] = df["situacao"].astype("string")
    return df


def _transformar_navios_previstos(df: pd.DataFrame, arquivo_origem: str) -> pd.DataFrame:
    """
    Regra específica para 'navios_previstos':
    1. Renomeia e converte coluna de data/hora de previsão de chegada.
    2. Adiciona a coluna 'situacao' como 'chegada_prevista'.
    """
    if "previsao_de_chegada" in df.columns:
        df = df.rename(columns={"previsao_de_chegada": "data_hora_previsao_de_chegada"})
    
    if "data_hora_previsao_de_chegada" in df.columns:
        df["data_hora_previsao_de_chegada"] = pd.to_datetime(
            df["data_hora_previsao_de_chegada"],
            format="%d/%m/%Y - %H:%M",
            errors="coerce"
        )

    df["situacao"] = "chegada_prevista"
    df["situacao"] = df["situacao"].astype("string")
    return df


# Mapeia o nome da tabela diretamente para sua função de transformação
REGRAS_TABELAS = {
    "manobras_previstas": _transformar_manobras_previstas,
    "manobras_realizadas": _transformar_manobras_realizadas,
    "navios_atracados": _transformar_navios_atracados,
    "navios_fundeados": _transformar_navios_fundeados,
    "navios_previstos": _transformar_navios_previstos,
}


# ==============================================================================
# 4. FUNÇÃO GENÉRICA DE PROCESSAMENTO (LANDING_RAW -> SILVER)
# ==============================================================================
def processar_arquivo_html(caminho_arquivo: Path) -> Optional[Path]:
    """
    Função genérica e idempotente que transforma um arquivo HTML da Landing Raw
    em um arquivo Parquet normalizado na Silver.

    Args:
        caminho_arquivo (Path): Caminho completo do arquivo HTML na landing_raw.

    Returns:
        Optional[Path]: Caminho do arquivo Parquet gerado na Silver, ou None se falhar.
    """
    if not caminho_arquivo.exists():
        logger.error("Arquivo não encontrado: %s", caminho_arquivo)
        return None

    # Identifica o tipo de tabela pelo nome do arquivo
    # Ex: '2026-08-23_16-00-06_manobras_previstas.html' -> 'manobras_previstas'
    tipo_tabela = None
    for tabela in REGRAS_TABELAS.keys():
        if caminho_arquivo.name.endswith(f"{tabela}.html"):
            tipo_tabela = tabela
            break

    if not tipo_tabela:
        logger.warning(
            "Arquivo '%s' não corresponde a nenhuma tabela configurada. Ignorando.",
            caminho_arquivo.name,
        )
        return None

    logger.info("Iniciando processamento de [%s]: %s", tipo_tabela, caminho_arquivo.name)

    # 1. Leitura com encoding UTF-8 direto
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            html_content = f.read()

        tabelas = pd.read_html(io.StringIO(html_content))
        if not tabelas:
            logger.warning("Nenhuma tabela encontrada no HTML: %s", caminho_arquivo.name)
            return None

        df = tabelas[0]
    except Exception as e:
        logger.exception("Erro ao ler tabela do HTML '%s': %s", caminho_arquivo.name, e)
        return None

    # 2. Padronização dos Cabeçalhos
    df = padronizar_colunas(df)

    # 3. Normalização inicial de texto em todas as colunas
    for col in df.columns:
        df[col] = df[col].apply(normalizar_texto).astype("string")

    # 4. Aplicação da transformação específica da tabela (onde tipos específicos e novas colunas são aplicados)
    funcao_transformacao = REGRAS_TABELAS.get(tipo_tabela)
    if funcao_transformacao:
        df = funcao_transformacao(df, caminho_arquivo.name)

    # 5. Adição de Metadados de Auditoria e Linhagem (Data Lineage)
    df["data_processamento"] = datetime.now()
    df["arquivo_origem"] = caminho_arquivo.name

    # Extrai o timestamp do snapshot do nome do arquivo (ex: '2026-08-23_16-00-06')
    timestamp_snapshot_str = caminho_arquivo.name[:19]
    try:
        df["snapshot_timestamp"] = pd.to_datetime(
            timestamp_snapshot_str, format="%Y-%m-%d_%H-%M-%S"
        )
    except Exception:
        df["snapshot_timestamp"] = pd.NaT

    # 6. Salvamento na camada Silver (Parquet)
    pasta_destino = SILVER_DIR / tipo_tabela
    pasta_destino.mkdir(parents=True, exist_ok=True)

    # O nome do parquet mantém o timestamp do snapshot para idempotência
    # Ex: '2026-08-23_16-00-06_manobras_previstas.html' -> '2026-08-23_16-00-06.parquet'
    snapshot_nome = caminho_arquivo.stem.removesuffix(f"_{tipo_tabela}")
    arquivo_saida = pasta_destino / f"{snapshot_nome}.parquet"

    df.to_parquet(arquivo_saida, engine="pyarrow", index=False)
    logger.info("Sucesso! Parquet salvo em: %s (Total de linhas: %d)", arquivo_saida, len(df))

    return arquivo_saida


# ==============================================================================
# 5. PROCESSAMENTO EM LOTE (OU FILTRO POR DATA / ARQUIVOS PENDENTES)
# ==============================================================================
def processar_todos_arquivos(
    data_filtro: Optional[str] = None,
    apenas_pendentes: bool = True
) -> None:
    """
    Executa a transformação em lote da camada Landing para a camada Silver.

    Args:
        data_filtro (str, opcional): Prefixo de data no formato 'YYYY-MM-DD'.
                                     Se None, avalia todos os arquivos da landing_raw.
        apenas_pendentes (bool): Se True, processa apenas arquivos HTML que ainda
                                 não possuem o respectivo Parquet na Silver.
    """
    if not LANDING_DIR.exists():
        logger.error("Pasta landing_raw não encontrada em: %s", LANDING_DIR)
        return

    arquivos_html = sorted(LANDING_DIR.glob("*.html"))
    logger.info("Total de arquivos HTML encontrados na landing_raw: %d", len(arquivos_html))

    processados = 0
    ignorados = 0

    for arq in arquivos_html:
        # Filtra por data caso informado
        if data_filtro and not arq.name.startswith(data_filtro):
            continue

        # Se apenas_pendentes estiver ativo, verifica se já existe na Silver
        if apenas_pendentes:
            tipo_tabela = None
            for tab in REGRAS_TABELAS.keys():
                if arq.name.endswith(f"{tab}.html"):
                    tipo_tabela = tab
                    break
            if tipo_tabela:
                snapshot_nome = arq.stem.removesuffix(f"_{tipo_tabela}")
                parquet_esperado = SILVER_DIR / tipo_tabela / f"{snapshot_nome}.parquet"
                if parquet_esperado.exists():
                    ignorados += 1
                    continue

        resultado = processar_arquivo_html(arq)
        if resultado:
            processados += 1

    logger.info(
        "Processamento concluído: %d arquivos gerados/atualizados, %d já existentes ignorados.",
        processados,
        ignorados,
    )


# ==============================================================================
# 6. BLOCO PRINCIPAL PARA EXECUÇÃO DIRETA OU VIA AIRFLOW
# ==============================================================================
if __name__ == "__main__":
    # Processa apenas os arquivos pendentes da pasta landing_raw
    processar_todos_arquivos(apenas_pendentes=True)
