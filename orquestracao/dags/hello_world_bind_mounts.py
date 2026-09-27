"""
DAG hello world — Marco 2.

Objetivo: PROVAR que o container do Airflow enxerga os bind mounts de:
  - CÓDIGO: /opt/airflow/workspace/maritimo-data-pipeline (read-only)
  - DADOS:  /opt/airflow/data/maritimo (read-write)

Não roda nenhuma transformação real — só inspeciona o que está montado e
imprime nos logs das tasks. Se as tasks terminarem com sucesso e os logs
listarem os arquivos esperados, os volumes estão corretos.

schedule=None: esta DAG só roda quando disparada manualmente (coerente com a
arquitetura event-driven decidida — quem agenda o pipeline real é o cron).
"""

from __future__ import annotations

import os
from pathlib import Path

from airflow.sdk import dag, task  # API TaskFlow do Airflow 3.x

# Caminhos DENTRO do container (alvos dos bind mounts definidos no compose).
CODE_DIR = Path("/opt/airflow/workspace/maritimo-data-pipeline")
DATA_DIR = Path("/opt/airflow/data/maritimo")


@dag(
    dag_id="hello_world_bind_mounts",
    schedule=None,          # só dispara manualmente
    catchup=False,          # não faz backfill de execuções passadas
    tags=["marco2", "validacao"],
    doc_md=__doc__,
)
def hello_world_bind_mounts():

    @task
    def checar_codigo() -> list[str]:
        """Lista os arquivos .py do código montado (read-only)."""
        if not CODE_DIR.exists():
            raise FileNotFoundError(
                f"CÓDIGO não encontrado em {CODE_DIR}. Bind mount falhou."
            )
        arquivos_py = sorted(p.name for p in CODE_DIR.glob("*.py"))
        print(f"[código] {CODE_DIR} existe. Scripts .py: {arquivos_py}")
        # Confere que os 3 scripts esperados estão visíveis.
        esperados = {"scraper.py", "transform_silver.py", "transform_gold.py"}
        faltando = esperados - set(arquivos_py)
        if faltando:
            raise AssertionError(f"Scripts esperados ausentes: {faltando}")
        print("[código] OK: os 3 scripts do pipeline estão visíveis.")
        return arquivos_py

    @task
    def checar_dados() -> dict[str, int]:
        """Lista as camadas de dados montadas e conta os arquivos de cada uma."""
        if not DATA_DIR.exists():
            raise FileNotFoundError(
                f"DADOS não encontrados em {DATA_DIR}. Bind mount falhou."
            )
        # Confere a env que os scripts do pipeline usam para gravar dados.
        env_data_dir = os.environ.get("MARITIMO_DATA_DIR")
        print(f"[dados] MARITIMO_DATA_DIR={env_data_dir}")
        assert env_data_dir == str(DATA_DIR), (
            f"MARITIMO_DATA_DIR ({env_data_dir}) != esperado ({DATA_DIR})"
        )

        contagem: dict[str, int] = {}
        for camada in ("landing_raw", "silver", "gold"):
            caminho = DATA_DIR / camada
            n = len(list(caminho.iterdir())) if caminho.exists() else 0
            contagem[camada] = n
            print(f"[dados] {camada}: {n} item(ns)")
        return contagem

    @task
    def testar_escrita() -> str:
        """Prova que o mount de DADOS é gravável (read-write), escrevendo e
        apagando um arquivo-sonda. Não toca nos dados reais."""
        sonda = DATA_DIR / "_marco2_write_test.tmp"
        sonda.write_text("bind mount de dados é gravável\n", encoding="utf-8")
        conteudo = sonda.read_text(encoding="utf-8").strip()
        sonda.unlink()  # limpa a sonda
        print(f"[escrita] gravou e leu de volta: {conteudo!r} -> sonda removida")
        return "escrita OK"

    # Encadeamento: primeiro inspeciona código e dados (em paralelo),
    # depois testa a escrita. As dependências saem naturalmente do TaskFlow.
    codigo = checar_codigo()
    dados = checar_dados()
    escrita = testar_escrita()
    [codigo, dados] >> escrita


hello_world_bind_mounts()
