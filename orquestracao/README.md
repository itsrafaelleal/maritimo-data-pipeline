# Orquestração — Apache Airflow

Esta pasta contém a camada de **orquestração** do pipeline marítimo: as DAGs do
Apache Airflow que executam as transformações e o script de disparo agendado
via cron.

A orquestração foi desenhada seguindo um modelo **event-driven** (dirigido por
evento) e **desacoplado**: a coleta de dados e a transformação são independentes,
e o agendamento fica fora do Airflow (no cron do host). O porquê dessas decisões
está explicado abaixo.

---

## Estrutura

```text
orquestracao/
├── dags/
│   ├── maritimo_transform.py        # DAG principal: silver -> gold
│   └── hello_world_bind_mounts.py   # DAG de validação da infra (smoke test)
└── scriptcron/
    ├── trigger_airflow_transform.sh # dispara a DAG a partir do cron do host
    └── crontab.example              # exemplo de agendamento
```

---

## Arquitetura da orquestração

```text
        CRON (host)                         AIRFLOW (containers)
┌─────────────────────────┐        ┌──────────────────────────────────┐
│ scraper (Selenium)      │        │  DAG maritimo_transform            │
│   ↓ gera HTML novo      │        │                                    │
│ landing_raw/            │        │   transform_silver ──▶ transform_gold │
│                         │        │   (HTML → Parquet)   (→ Star Schema) │
│ trigger_...sh ──────────┼───────▶│  (disparada via `docker exec`)     │
└─────────────────────────┘        └──────────────────────────────────┘
```

### Por que o agendamento fica no cron, e não no `schedule` do Airflow?

As duas DAGs usam `schedule=None` (disparo manual/externo). A decisão é
proposital:

- **A coleta depende de um site externo** e roda no host com Selenium. Manter o
  gatilho no cron desacopla a coleta da transformação.
- **Desacoplamento:** se a coleta falhar, a transformação simplesmente não
  encontra dado novo e não faz nada — em vez de a DAG quebrar por falta de
  insumo.
- **Idempotência:** a DAG só processa os HTML que ainda não viraram Parquet.
  Disparar sem dado novo é inofensivo.

### As duas DAGs

**`maritimo_transform.py`** — DAG principal. Orquestra a arquitetura medalhão na
parte determinística (Python puro):

```text
landing_raw (HTML) ──silver──▶ silver (Parquet) ──gold──▶ gold (Star Schema)
```

Ela importa e executa os módulos do próprio projeto
(`transform_silver.py` e `transform_gold.py`), que ficam montados no container
como bind mount **read-only**. Detalhes de engenharia:

- Os imports pesados (pandas, etc.) ficam **dentro das tasks**, não no topo do
  arquivo — assim o *dag-processor* parseia a DAG rapidamente sem carregar
  pandas a cada scan.
- A task `transform_silver` **falha explicitamente** se a camada silver ficar
  vazia (nada para o gold consumir), evitando um sucesso silencioso enganoso.
- A task `transform_gold` valida que **todos** os artefatos esperados do Star
  Schema (dims e fatos) foram gerados.
- Encadeamento: `silver >> gold` (o gold só roda se o silver terminar com
  sucesso).

**`hello_world_bind_mounts.py`** — DAG de validação de infraestrutura
(*smoke test*). Não transforma nada: apenas prova que o container enxerga os
volumes de código (read-only) e de dados (read-write), e que a variável de
ambiente `MARITIMO_DATA_DIR` aponta para o lugar certo. Serve para separar o
problema "a infra está certa?" do problema "a lógica está certa?" — dois tipos
de falha bem diferentes.

---

## Como rodar

> **Pré-requisito:** um ambiente Airflow 3.x em execução, com os módulos do
> pipeline (`transform_silver.py`, `transform_gold.py`) acessíveis ao container
> via `PYTHONPATH` e os diretórios de dados montados. A DAG espera encontrar o
> código em `/opt/airflow/workspace/maritimo-data-pipeline` e os dados em
> `/opt/airflow/data/maritimo` (dentro do container).

### 1. Colocar as DAGs no Airflow

Copie os arquivos de `dags/` para a pasta de DAGs do seu Airflow (ou monte esta
pasta como volume). O *dag-processor* detecta os arquivos automaticamente.

### 2. Disparo manual (para testar)

Pela UI do Airflow (botão *Trigger DAG*) ou pelo CLI dentro do container:

```bash
docker exec airflow-scheduler airflow dags trigger maritimo_transform
```

Recomendado rodar primeiro a `hello_world_bind_mounts` para confirmar que os
volumes estão corretos antes de confiar na DAG de transformação.

### 3. Disparo agendado (cron)

O script `scriptcron/trigger_airflow_transform.sh` verifica se o container do
Airflow está no ar e dispara a DAG. Ele é configurável por variáveis de
ambiente (com defaults):

| Variável            | Default              | Descrição                              |
|---------------------|----------------------|----------------------------------------|
| `AIRFLOW_CONTAINER` | `airflow-scheduler`  | Nome do container com o CLI do Airflow |
| `AIRFLOW_DAG_ID`    | `maritimo_transform` | ID da DAG a disparar                   |
| `TRIGGER_LOG_DIR`   | `./logs`             | Diretório dos logs do script           |

Passos:

```bash
# 1. Tornar o script executável
chmod +x scriptcron/trigger_airflow_transform.sh

# 2. Testar manualmente
./scriptcron/trigger_airflow_transform.sh

# 3. Agendar no cron (ver scriptcron/crontab.example)
crontab -e
```

Veja `scriptcron/crontab.example` para um exemplo de linha de cron (dispara a
cada 4 horas, com folga para a coleta terminar antes).

---

## Nota sobre segredos

Nenhum segredo é versionado nesta pasta. As DAGs usam apenas caminhos internos
do container. A configuração sensível do Airflow (credenciais, segredo JWT,
caminhos absolutos do host) fica em arquivos `.env` que **não** fazem parte
deste repositório.
