"""
DAG maritimo_transform — Marco 3.

Orquestra as TRANSFORMAÇÕES do pipeline marítimo (medalhão):
    landing_raw (HTML)  --silver-->  silver (Parquet)  --gold-->  gold (Star Schema)

Roda os scripts já existentes e montados (read-only) em
/opt/airflow/workspace/maritimo-data-pipeline:
    - transform_silver.processar_todos_arquivos(apenas_pendentes=True)
    - transform_gold.executar_pipeline_gold()

Escopo (decisão de arquitetura):
    - O SCRAPER (Selenium) NÃO faz parte desta DAG. Ele continua no cron do host.
    - Esta DAG cuida só do que é Python puro/determinístico (silver -> gold).

schedule=None: dispara manualmente (ou, no futuro, via `docker exec ... dags
trigger` acionado pelo cron — gatilho externo). Quem decide QUANDO rodar é externo.

Nota de engenharia: os imports pesados (pandas etc.) ficam DENTRO das tasks,
não no topo do arquivo. Assim o dag-processor parseia a DAG sem carregar pandas
a cada scan (boa prática do Airflow).
"""

from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow.sdk import dag, task

# Caminho do código do pipeline dentro do container (bind mount read-only).
# Já está no PYTHONPATH (definido no compose), mas garantimos aqui também.
PIPELINE_PATH = "/opt/airflow/workspace/maritimo-data-pipeline"


@dag(
    dag_id="maritimo_transform",
    description="Transformações do pipeline marítimo: silver -> gold",
    schedule=None,            # disparo manual/externo (event-driven)
    start_date=pendulum.datetime(2026, 1, 1, tz="America/Sao_Paulo"),
    catchup=False,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    tags=["maritimo", "transform", "marco3"],
    doc_md=__doc__,
)
def maritimo_transform():

    @task
    def transform_silver() -> dict:
        """landing_raw (HTML) -> silver (Parquet). Idempotente: só processa
        os HTML que ainda não têm o Parquet correspondente."""
        import sys
        from pathlib import Path

        if PIPELINE_PATH not in sys.path:
            sys.path.insert(0, PIPELINE_PATH)

        # Importa o módulo do pipeline (usa MARITIMO_DATA_DIR do ambiente).
        import transform_silver as ts

        # Estado ANTES, para reportar o que mudou.
        antes = {
            tab.name: len(list(tab.glob("*.parquet")))
            for tab in ts.SILVER_DIR.iterdir()
            if tab.is_dir()
        } if ts.SILVER_DIR.exists() else {}

        ts.processar_todos_arquivos(apenas_pendentes=True)

        # Estado DEPOIS.
        depois = {
            tab.name: len(list(tab.glob("*.parquet")))
            for tab in ts.SILVER_DIR.iterdir()
            if tab.is_dir()
        } if ts.SILVER_DIR.exists() else {}

        print(f"[silver] SILVER_DIR={ts.SILVER_DIR}")
        print(f"[silver] parquets por tabela (antes): {antes}")
        print(f"[silver] parquets por tabela (depois): {depois}")

        # Falha explícita se a silver ficou vazia (nada para o gold consumir).
        total = sum(depois.values())
        if total == 0:
            raise ValueError(
                f"Silver vazia após o processamento (SILVER_DIR={ts.SILVER_DIR}). "
                "Verifique se há HTML em landing_raw."
            )
        return depois

    @task
    def transform_gold() -> list[str]:
        """silver (Parquet) -> gold (Star Schema). Gera as dims e fatos."""
        import sys
        from pathlib import Path

        if PIPELINE_PATH not in sys.path:
            sys.path.insert(0, PIPELINE_PATH)

        import transform_gold as tg

        tg.executar_pipeline_gold()

        # Lista os artefatos gerados na gold como evidência de sucesso.
        gold_files = sorted(p.name for p in tg.GOLD_DIR.glob("*.parquet"))
        print(f"[gold] GOLD_DIR={tg.GOLD_DIR}")
        print(f"[gold] artefatos gerados: {gold_files}")

        esperados = {
            "dim_navios.parquet",
            "dim_bercos.parquet",
            "dim_calendario.parquet",
            "fct_manobras_previsto_vs_realizado.parquet",
            "fct_tempo_fila_barra.parquet",
        }
        faltando = esperados - set(gold_files)
        if faltando:
            raise AssertionError(f"Artefatos gold esperados ausentes: {faltando}")
        print("[gold] OK: todos os artefatos esperados do Star Schema foram gerados.")
        return gold_files

    # Encadeamento: gold só roda depois que silver terminar com sucesso.
    silver = transform_silver()
    gold = transform_gold()
    silver >> gold


maritimo_transform()
