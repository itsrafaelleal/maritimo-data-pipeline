#!/bin/bash
# =============================================================================
# trigger_airflow_transform.sh
#
# Objetivo: DISPARAR a DAG de transformação do pipeline marítimo (silver -> gold)
# no Airflow, a partir de um agendador externo (cron do host).
#
# Arquitetura event-driven: o cron decide QUANDO rodar; o Airflow decide COMO.
# O scraper (coleta) roda separado, também no cron. Alguns minutos depois, este
# script aciona a transformação. Como a DAG é IDEMPOTENTE (só processa os HTML
# que ainda não viraram Parquet), rodar sem dado novo é inofensivo.
#
# Por que disparar de fora, e não agendar dentro do Airflow (schedule)?
#   - A coleta depende de um site externo e roda no host (Selenium).
#   - Manter o gatilho no cron desacopla a coleta da transformação: se a coleta
#     falhar, a transformação simplesmente não encontra dado novo e não faz nada.
#
# Configuração por variáveis de ambiente (com defaults). Sobrescreva conforme
# o seu ambiente, por exemplo exportando antes de chamar o script ou editando
# a linha do crontab.
# =============================================================================
set -euo pipefail

# --- Configuração (variáveis de ambiente com defaults genéricos) -------------
# Nome do container do Airflow que expõe o CLI `airflow` (scheduler).
CONTAINER="${AIRFLOW_CONTAINER:-airflow-scheduler}"
# ID da DAG a ser disparada.
DAG_ID="${AIRFLOW_DAG_ID:-maritimo_transform}"
# Diretório para os logs deste script.
LOG_DIR="${TRIGGER_LOG_DIR:-./logs}"
LOG_FILE="${LOG_DIR}/trigger_airflow_transform.log"

mkdir -p "$LOG_DIR"

# Função de log: escreve com timestamp no arquivo e também no stdout.
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $*" | tee -a "$LOG_FILE"
}

log "===== INÍCIO ====="

# --- 1. Verificar se o container do Airflow está no ar -----------------------
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    log "ERRO: container '${CONTAINER}' não está rodando. Suba o Airflow (docker compose up -d)."
    exit 1
fi

# --- 2. Disparar a DAG de transformação --------------------------------------
log "disparando DAG '${DAG_ID}' via docker exec ${CONTAINER}..."
if docker exec "$CONTAINER" airflow dags trigger "$DAG_ID" >> "$LOG_FILE" 2>&1; then
    log "DAG '${DAG_ID}' disparada com sucesso."
else
    log "ERRO: falha ao disparar a DAG '${DAG_ID}'."
    exit 1
fi

log "===== FIM ====="
