#%%

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


# 1. CONFIGURAÇÕES GERAIS E LOGGING

BASE_DIR = Path(__file__).resolve().parent
SILVER_DIR = BASE_DIR / "silver"
GOLD_DIR = BASE_DIR / "gold"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TransformGold")



#  FUNÇÕES AUXILIARES DE LEITURA DA CAMADA SILVER

def carregar_tabela_silver(nome_tabela: str) -> pd.DataFrame:
    """
    Carrega e unifica todos os arquivos Parquet de uma tabela da Camada Silver,
    ignorando arquivos de exemplo (*_example.parquet).
    """
    pasta = SILVER_DIR / nome_tabela
    if not pasta.exists():
        logger.warning("Pasta não encontrada na Silver: %s", pasta)
        return pd.DataFrame()

    arquivos = sorted([
        f for f in pasta.glob("*.parquet")
        if not f.name.endswith("example.parquet")
    ])

    if not arquivos:
        logger.warning("Nenhum arquivo Parquet encontrado em: %s", pasta)
        return pd.DataFrame()

    logger.info("Carregando [%s]: %d arquivos encontrados na Silver...", nome_tabela, len(arquivos))
    dfs = [pd.read_parquet(f) for f in arquivos]
    df_consolidado = pd.concat(dfs, ignore_index=True)
    logger.info("Total de registros lidos de [%s]: %d linhas.", nome_tabela, len(df_consolidado))
    return df_consolidado



# 3. CONSTRUÇÃO DAS TABELAS DIMENSÃO (CONFORMES)

def construir_dim_navios(dfs_silver: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Cria a dimensão 'dim_navios':
    - Consolida todas as embarcações encontradas nas 5 tabelas da Silver.
    - Deduplica por navio pegando os atributos físicos (LOA, Boca) mais recentes.
    """
    logger.info("Construindo dimensão: [dim_navios]...")
    registros = []

    # Extrai navios de todas as tabelas disponíveis
    for nome_tabela, df in dfs_silver.items():
        if df.empty or "navio" not in df.columns:
            continue
        cols = ["navio", "snapshot_timestamp"]
        for opc in ["loa", "boca"]:
            if opc in df.columns:
                cols.append(opc)
        sub_df = df[cols].copy()
        registros.append(sub_df)

    if not registros:
        return pd.DataFrame()

    df_todos_navios = pd.concat(registros, ignore_index=True)
    df_todos_navios = df_todos_navios.dropna(subset=["navio"])
    df_todos_navios["navio"] = df_todos_navios["navio"].str.strip().str.lower()

    # Ordena pelo snapshot mais recente para manter as características mais atualizadas
    df_todos_navios = df_todos_navios.sort_values(
        by=["navio", "snapshot_timestamp"],
        ascending=[True, False]
    )

    # Agrupa por navio e obtém o registro mais recente
    dim_navios = df_todos_navios.groupby("navio").first().reset_index()

    # Formatação e Tipagem das Colunas
    dim_navios["id_navio"] = dim_navios["navio"]
    dim_navios["nome_navio"] = dim_navios["navio"].str.upper()

    colunas_finais = ["id_navio", "nome_navio"]
    if "loa" in dim_navios.columns:
        dim_navios["loa_metros"] = dim_navios["loa"]
        colunas_finais.append("loa_metros")
    if "boca" in dim_navios.columns:
        dim_navios["boca_metros"] = dim_navios["boca"]
        colunas_finais.append("boca_metros")

    dim_navios["data_processamento"] = datetime.now()
    colunas_finais.append("data_processamento")

    dim_navios = dim_navios[colunas_finais]
    logger.info("dim_navios concluída com %d navios únicos cadastrados.", len(dim_navios))
    return dim_navios


def construir_dim_bercos(dfs_silver: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Cria a dimensão 'dim_bercos':
    - Lista única de berços portuários operacionais.
    - Mapeia regras de negócio para classificar o Terminal Operador.
    """
    logger.info("Construindo dimensão: [dim_bercos]...")
    bercos_set = set()

    for df in dfs_silver.values():
        if not df.empty and "berco" in df.columns:
            bercos_validos = df["berco"].dropna().str.strip().str.lower().unique()
            bercos_set.update(bercos_validos)

    df_bercos = pd.DataFrame({"id_berco": sorted(list(bercos_set))})
    df_bercos["nome_berco"] = df_bercos["id_berco"].str.upper()

    # Mapeamento do Terminal Portuário responsável pelo berço
    def identificar_terminal(berco_str: str) -> str:
        if "pnave" in berco_str:
            return "Portonave"
        elif "jbs" in berco_str:
            return "JBS / Terminais"
        elif "teporti" in berco_str:
            return "Teporti"
        elif "braskarne" in berco_str:
            return "Braskarne"
        elif "poly" in berco_str:
            return "Poly Terminais"
        elif "barra do rio" in berco_str:
            return "Barra do Rio"
        elif "navship" in berco_str:
            return "Navship"
        elif "brasil sul" in berco_str:
            return "Brasil Sul"
        elif "tpt" in berco_str:
            return "TPT"
        return "Outros / Cais Público"

    df_bercos["terminal_operador"] = df_bercos["id_berco"].apply(identificar_terminal)
    df_bercos["data_processamento"] = datetime.now()

    logger.info("dim_bercos concluída com %d berços mapeados.", len(df_bercos))
    return df_bercos


def construir_dim_calendario(data_inicio: str = "2026-01-01", data_fim: str = "2026-12-31") -> pd.DataFrame:
    """
    Gera a dimensão de tempo 'dim_calendario' contínua para facilitar análises temporais no Qlik.
    """
    logger.info("Construindo dimensão: [dim_calendario] (%s até %s)...", data_inicio, data_fim)
    datas = pd.date_range(start=data_inicio, end=data_fim, freq="D")
    
    df_cal = pd.DataFrame({"data": datas})
    df_cal["id_data"] = df_cal["data"].dt.strftime("%Y%m%d").astype(int)
    df_cal["ano"] = df_cal["data"].dt.year
    df_cal["mes"] = df_cal["data"].dt.month
    df_cal["dia"] = df_cal["data"].dt.day
    df_cal["trimestre"] = df_cal["data"].dt.quarter
    df_cal["semestre"] = (df_cal["mes"] <= 6).map({True: 1, False: 2})
    df_cal["dia_semana"] = df_cal["data"].dt.dayofweek + 1  # 1 = Segunda, 7 = Domingo
    
    # Nomes em Português
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    dias_semana_pt = {
        1: "Segunda-feira", 2: "Terça-feira", 3: "Quarta-feira",
        4: "Quinta-feira", 5: "Sexta-feira", 6: "Sábado", 7: "Domingo"
    }
    
    df_cal["mes_nome"] = df_cal["mes"].map(meses_pt)
    df_cal["dia_semana_nome"] = df_cal["dia_semana"].map(dias_semana_pt)
    df_cal["flag_fim_de_semana"] = df_cal["dia_semana"].isin([6, 7])

    logger.info("dim_calendario concluída com %d dias gerados.", len(df_cal))
    return df_cal



# 4. CONSTRUÇÃO DAS TABELAS FATO (MÉTRICAS ANALÍTICAS)

def construir_fct_manobras(df_previstas: pd.DataFrame, df_realizadas: pd.DataFrame) -> pd.DataFrame:
    """
    Cria a tabela fato principal 'fct_manobras_previsto_vs_realizado':
    1. Deduplica manobras previstas (pega a última previsão emitida antes do evento).
    2. Deduplica manobras realizadas (uma linha por evento real).
    3. Cruza Previsto vs Realizado via FULL OUTER JOIN.
    4. Calcula atraso em minutos e classificação de pontualidade.
    """
    logger.info("Construindo tabela fato: [fct_manobras_previsto_vs_realizado]...")

    # --- 1. Deduplicação das Manobras Previstas ---
    if not df_previstas.empty:
        prev = df_previstas.dropna(subset=["data", "navio", "manobra", "berco"]).copy()
        # Ordena pelo snapshot mais recente
        prev = prev.sort_values(by="snapshot_timestamp", ascending=True)
        # Pega a última previsão emitida para cada chave de manobra
        prev_dedup = prev.groupby(["data", "navio", "manobra", "berco"]).last().reset_index()
        prev_cols = [
            "data", "navio", "manobra", "berco", "bordo", "rota",
            "data_hora_manobra_prevista", "status", "situacao", "snapshot_timestamp"
        ]
        prev_dedup = prev_dedup[[c for c in prev_cols if c in prev_dedup.columns]]
        prev_dedup = prev_dedup.rename(columns={
            "bordo": "bordo_previsto",
            "rota": "rota_prevista",
            "status": "status_previsao",
            "situacao": "situacao_navio_previsao",
            "snapshot_timestamp": "timestamp_ultima_previsao"
        })
    else:
        prev_dedup = pd.DataFrame()

    # --- 2. Deduplicação das Manobras Realizadas ---
    if not df_realizadas.empty:
        real = df_realizadas.dropna(subset=["data", "navio", "manobra", "berco"]).copy()
        real = real.sort_values(by="snapshot_timestamp", ascending=True)
        real_dedup = real.groupby(["data", "navio", "manobra", "berco"]).last().reset_index()
        real_cols = [
            "data", "navio", "manobra", "berco", "bordo", "rota", "rebocadores",
            "data_hora_manobra_realizada", "status", "snapshot_timestamp"
        ]
        real_dedup = real_dedup[[c for c in real_cols if c in real_dedup.columns]]
        real_dedup = real_dedup.rename(columns={
            "bordo": "bordo_realizado",
            "rota": "rota_realizada",
            "status": "status_realizado",
            "snapshot_timestamp": "timestamp_confirmacao_realizada"
        })
    else:
        real_dedup = pd.DataFrame()

    # --- 3. Cruzamento Full Outer Join ---
    if prev_dedup.empty and real_dedup.empty:
        return pd.DataFrame()
    elif prev_dedup.empty:
        fato = real_dedup.copy()
    elif real_dedup.empty:
        fato = prev_dedup.copy()
    else:
        fato = pd.merge(
            real_dedup,
            prev_dedup,
            on=["data", "navio", "manobra", "berco"],
            how="outer"
        )

    # --- 4. Consolidação de Atributos e Métricas ---
    fato["data_operacao"] = fato["data"]
    fato["id_navio"] = fato["navio"]
    fato["id_berco"] = fato["berco"]
    fato["tipo_manobra"] = fato["manobra"]

    # Bordo e Rota consolidados
    fato["bordo"] = fato.get("bordo_realizado", pd.Series(dtype="string")).combine_first(
        fato.get("bordo_previsto", pd.Series(dtype="string"))
    )
    fato["rota"] = fato.get("rota_realizada", pd.Series(dtype="string")).combine_first(
        fato.get("rota_previsto", pd.Series(dtype="string"))
    )

    # Chave Primária da Operação
    fato["id_operacao"] = (
        fato["data_operacao"].astype(str) + "_" +
        fato["id_navio"].astype(str) + "_" +
        fato["tipo_manobra"].astype(str) + "_" +
        fato["id_berco"].astype(str)
    )

    # Contagem de Rebocadores Utilizados
    def contar_rebocadores(val: object) -> int:
        if pd.isna(val) or not str(val).strip():
            return 0
        return len(str(val).split("/"))

    if "rebocadores" in fato.columns:
        fato["qtd_rebocadores"] = fato["rebocadores"].apply(contar_rebocadores)
    else:
        fato["qtd_rebocadores"] = 0

    # Cálculo do Atraso em Minutos: (Realizado - Previsto)
    if "data_hora_manobra_realizada" in fato.columns and "data_hora_manobra_prevista" in fato.columns:
        diff_segundos = (fato["data_hora_manobra_realizada"] - fato["data_hora_manobra_prevista"]).dt.total_seconds()
        fato["diferenca_minutos_atraso"] = (diff_segundos / 60.0).round(1)
    else:
        fato["diferenca_minutos_atraso"] = np.nan

    # Classificação de Pontualidade
    def classificar_pontualidade(row: pd.Series) -> str:
        realizada = row.get("data_hora_manobra_realizada")
        prevista = row.get("data_hora_manobra_prevista")
        diff_min = row.get("diferenca_minutos_atraso")

        if pd.isna(prevista) and pd.notna(realizada):
            return "Realizado Sem Previsao"
        if pd.isna(realizada) and pd.notna(prevista):
            return "Previsto Nao Realizado"
        if pd.isna(diff_min):
            return "Horario Suspenso / TBC"
        if -30 <= diff_min <= 30:
            return "No Prazo"
        elif diff_min > 30:
            return "Atrasado"
        elif diff_min < -30:
            return "Adiantado"
        return "Indefinido"

    fato["status_pontualidade"] = fato.apply(classificar_pontualidade, axis=1)

    # Horas de Antecedência da Previsão
    if "data_hora_manobra_realizada" in fato.columns and "timestamp_ultima_previsao" in fato.columns:
        diff_ant = (fato["data_hora_manobra_realizada"] - fato["timestamp_ultima_previsao"]).dt.total_seconds()
        fato["horas_antecedencia_previsao"] = (diff_ant / 3600.0).round(1)
    else:
        fato["horas_antecedencia_previsao"] = np.nan

    fato["data_processamento"] = datetime.now()

    # Seleção e Ordenação das Colunas Analíticas
    colunas_ordenadas = [
        "id_operacao", "data_operacao", "id_navio", "id_berco", "tipo_manobra",
        "bordo", "rota", "data_hora_manobra_prevista", "data_hora_manobra_realizada",
        "diferenca_minutos_atraso", "status_pontualidade", "rebocadores", "qtd_rebocadores",
        "status_previsao", "situacao_navio_previsao", "status_realizado",
        "horas_antecedencia_previsao", "timestamp_ultima_previsao", "timestamp_confirmacao_realizada",
        "data_processamento"
    ]
    colunas_finais = [c for c in colunas_ordenadas if c in fato.columns]
    fato = fato[colunas_finais]

    logger.info("fct_manobras concluída com %d operações consolidadas.", len(fato))
    return fato


def construir_fct_tempo_fila_barra(df_fundeados: pd.DataFrame, df_atracados: pd.DataFrame) -> pd.DataFrame:
    """
    Cria a tabela fato 'fct_tempo_fila_barra':
    - Mede o tempo de espera (em horas) desde que o navio fundeou até sua atracação no cais.
    """
    logger.info("Construindo tabela fato: [fct_tempo_fila_barra]...")

    if df_fundeados.empty:
        return pd.DataFrame()

    # Pega os ciclos únicos de fundeio de cada navio
    fundeados_dedup = df_fundeados.dropna(subset=["navio", "data_hora_fundeado"]).copy()
    fundeados_dedup = fundeados_dedup.sort_values(by="snapshot_timestamp", ascending=True)
    ciclos_fundeio = fundeados_dedup.groupby(["navio", "data_hora_fundeado"]).first().reset_index()

    # Pega os eventos de atracação de cada navio
    if not df_atracados.empty:
        atracados_dedup = df_atracados.dropna(subset=["navio", "data_hora_atracagem"]).copy()
        atracados_dedup = atracados_dedup.sort_values(by="snapshot_timestamp", ascending=True)
        eventos_atracagem = atracados_dedup.groupby(["navio", "data_hora_atracagem"]).first().reset_index()
    else:
        eventos_atracagem = pd.DataFrame()

    registros_espera = []
    for _, row_fundeio in ciclos_fundeio.iterrows():
        navio = row_fundeio["navio"]
        dt_fundeio = row_fundeio["data_hora_fundeado"]

        dt_atracagem = pd.NaT
        berco_destino = None

        if not eventos_atracagem.empty:
            # Procura a primeira atracação desse navio após o momento de fundeio
            possiveis_atracagens = eventos_atracagem[
                (eventos_atracagem["navio"] == navio) &
                (eventos_atracagem["data_hora_atracagem"] >= dt_fundeio)
            ].sort_values(by="data_hora_atracagem")

            if not possiveis_atracagens.empty:
                primeira_atracagem = possiveis_atracagens.iloc[0]
                dt_atracagem = primeira_atracagem["data_hora_atracagem"]
                berco_destino = primeira_atracagem.get("berco")

        # Cálculo do tempo de espera em horas
        if pd.notna(dt_atracagem):
            tempo_horas = round((dt_atracagem - dt_fundeio).total_seconds() / 3600.0, 2)
            status_espera = "Atracado com Sucesso"
        else:
            tempo_horas = np.nan
            status_espera = "Aguardando na Barra (Fundeado)"

        registros_espera.append({
            "id_espera": f"{navio}_{dt_fundeio.strftime('%Y%m%d_%H%M')}",
            "id_navio": navio,
            "data_fundeio": dt_fundeio.date(),
            "data_hora_fundeado": dt_fundeio,
            "data_hora_atracagem": dt_atracagem,
            "tempo_espera_horas": tempo_horas,
            "status_espera": status_espera,
            "id_berco_atracado": berco_destino,
            "posicao_barra": row_fundeio.get("posicao"),
            "data_processamento": datetime.now()
        })

    fct_espera = pd.DataFrame(registros_espera)
    logger.info("fct_tempo_fila_barra concluída com %d ciclos de espera analisados.", len(fct_espera))
    return fct_espera



# 5. EXECUÇÃO DO PIPELINE GOLD

def executar_pipeline_gold() -> None:
    """
    Executa o fluxo completo de transformação da Camada Silver para a Camada Gold.
    Gera todos os arquivos Parquet dimensionais na pasta 'gold/'.
    """
    logger.info("==========================================================")
    logger.info("INICIANDO PROCESSAMENTO DA CAMADA GOLD (STAR SCHEMA)")
    logger.info("==========================================================")

    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Carregamento dos dados da Camada Silver
    tabelas_silver = [
        "manobras_previstas",
        "manobras_realizadas",
        "navios_atracados",
        "navios_fundeados",
        "navios_previstos"
    ]
    dfs_silver = {tab: carregar_tabela_silver(tab) for tab in tabelas_silver}

    # 2. Construção das Dimensões
    dim_navios = construir_dim_navios(dfs_silver)
    dim_bercos = construir_dim_bercos(dfs_silver)
    
    # Determina range de datas para o calendário a partir dos dados reais
    datas_reais = []
    for df in dfs_silver.values():
        for col in ["data", "data_operacao", "data_fundeio"]:
            if col in df.columns:
                datas_reais.extend(df[col].dropna().tolist())
    
    if datas_reais:
        dt_min = pd.to_datetime(min(datas_reais)).strftime("%Y-%m-%d")
        dt_max = pd.to_datetime(max(datas_reais)).strftime("%Y-%m-%d")
    else:
        dt_min, dt_max = "2026-08-01", "2026-09-30"

    dim_calendario = construir_dim_calendario(data_inicio=dt_min, data_fim=dt_max)

    # 3. Construção das Tabelas Fato
    fct_manobras = construir_fct_manobras(
        dfs_silver["manobras_previstas"],
        dfs_silver["manobras_realizadas"]
    )
    fct_fila_barra = construir_fct_tempo_fila_barra(
        dfs_silver["navios_fundeados"],
        dfs_silver["navios_atracados"]
    )

    # 4. Salvamento na Camada Gold (Parquet)
    modelos_gold = {
        "dim_navios": dim_navios,
        "dim_bercos": dim_bercos,
        "dim_calendario": dim_calendario,
        "fct_manobras_previsto_vs_realizado": fct_manobras,
        "fct_tempo_fila_barra": fct_fila_barra
    }

    logger.info("----------------------------------------------------------")
    logger.info("SALVANDO MODELOS NA CAMADA GOLD (PARQUET)")
    logger.info("----------------------------------------------------------")

    for nome_modelo, df_modelo in modelos_gold.items():
        if df_modelo.empty:
            logger.warning("Modelo [%s] está vazio. Ignorando gravação.", nome_modelo)
            continue
        caminho_saida = GOLD_DIR / f"{nome_modelo}.parquet"
        df_modelo.to_parquet(caminho_saida, engine="pyarrow", index=False)
        logger.info("✅ Salvo: %s | %d linhas | %d colunas", caminho_saida.name, len(df_modelo), len(df_modelo.columns))

    logger.info("==========================================================")
    logger.info("CAMADA GOLD PROCESSADA COM SUCESSO!")
    logger.info("==========================================================")


if __name__ == "__main__":
    executar_pipeline_gold()

