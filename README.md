# Marítimo Data Pipeline

Pipeline de dados desenvolvido para coletar, transformar, modelar e organizar informações operacionais de um porto, com foco em **manobras previstas, manobras realizadas, navios atracados, navios fundeados e chegadas previstas**.

O pipeline realiza a coleta de dados por meio de **Web Scraping com Selenium**, processa e normaliza as informações na camada **Silver** com Python e pandas gerando arquivos **Apache Parquet**, e estrutura a camada **Gold** em **Modelagem Dimensional (Star Schema)**. A execução das transformações é **orquestrada pelo Apache Airflow** (rodando em Docker no homelab) e a camada Gold está pronta para consumo em dashboards analíticos no **Qlik (Qlik Sense / Qlik Cloud)** — última etapa pendente.

> **Documentação e Aprendizados:**
> * [catalogo_de_dados.md](catalogo_de_dados.md) — **Catálogo oficial e dicionário de dados** com esquemas, tipos, métricas de negócio e mapa completo do dashboard.
> * [aprendizados.md](aprendizados.md) — Documento com decisões técnicas, desafios arquiteturais e boas práticas de engenharia de dados adotadas no projeto.
> * [orquestracao/](orquestracao/) — DAGs do Airflow, script de disparo via cron e a documentação da camada de orquestração.

---

## Status Atual do Projeto

O projeto está com o pipeline de ponta a ponta **automatizado e orquestrado**. Falta apenas a camada de visualização (Qlik):

* **Landing Raw:** Scraping automatizado coletando snapshots periódicos em HTML.
* **Silver:** Pipeline unificado e modular ([transform_silver.py](transform_silver.py)) tratando os dados brutos, tipando datas/horas padronizadas (`datetime64[us]`) e gerando arquivos Parquet.
* **Gold:** Modelagem dimensional em Star Schema ([transform_gold.py](transform_gold.py)) concluída, gerando tabelas Fato de pontualidade (`fct_manobras_previsto_vs_realizado`), tempo de espera na barra (`fct_tempo_fila_barra`) e Dimensões (`dim_navios`, `dim_bercos`, `dim_calendario`).
* **Orquestração:** ✅ **Em produção no homelab.** Apache Airflow 3.3.2 (LocalExecutor + Postgres) em Docker executando a DAG `maritimo_transform` (silver → gold). O agendamento fica no cron do host, que dispara a DAG de forma desacoplada — ver [orquestracao/](orquestracao/).
* **Governança & BI:** Catálogo de dados detalhado e planejamento funcional do dashboard gerencial no Qlik com 5 abas operacionais.
* **BI / Visualização:** ⏳ **Pendente.** Conectar o Qlik aos Parquets da Gold e construir os visuais.

---

## A Importância do Catálogo de Dados

O arquivo [catalogo_de_dados.md](catalogo_de_dados.md) é o coração da governança deste projeto. Ele atua como um **contrato de dados** entre a Engenharia de Dados e a camada de Business Intelligence (BI):

1. **Dicionário Técnico Completo:** Descreve cada coluna, tipo no Pandas, tipo no Parquet, regras de nulos e descrições de negócio para as camadas Silver e Gold.
2. **Memória de Cálculo dos Indicadores:** Formaliza a lógica de métricas críticas (como a *Taxa de Pontualidade*, *Tempo Médio de Espera na Barra* e *Atraso Efetivo*), garantindo que desenvolvedores e analistas de BI falem a mesma língua.
3. **Diagramas ERD Vivos:** Documenta visualmente o Star Schema usando diagramas como código (Mermaid), rastreando as chaves primárias (PK) e estrangeiras (FK).
4. **Mapa do Dashboard:** Especifica detalhadamente as 5 abas do painel, filtros e a grade de auditoria com 15 colunas para conferência de dados.

---

## Arquitetura Medalhão

```text
Fonte de Dados Portuária (Web)
            ↓
   Web Scraping — Selenium  (cron do host)
            ↓
  Landing Raw — HTML Bruto (Snapshots a cada 4h)
            ↓
  [ cron dispara a DAG do Airflow: `docker exec ... dags trigger` ]
            ↓
  ┌───────────── Apache Airflow (Docker) ─────────────┐
  │  DAG maritimo_transform                            │
  │                                                    │
  │  Transformação Silver ──▶ Modelagem Gold           │
  │  (Python/pandas/PyArrow)   (transform_gold.py)     │
  └────────────────────────────────────────────────────┘
            ↓
  Silver — Parquet Normalizado e Tipado
            ↓
  Gold — Parquets Dimensionais (Fatos e Dimensões)
            ↓
  Dashboard Executivo & Operacional — Qlik (Qlik Sense / Cloud)  ⏳
```

### 1. Landing Raw (`landing_raw/`)
* Armazenamento dos dados brutos coletados via Selenium;
* Preservação do dado original para auditoria e histórico de snapshots;
* Base para reprocessamento completo do pipeline.

### 2. Camada Silver (`silver/`)
* Normalização e limpeza de texto (remoção de acentos, padronização snake_case);
* Extração e unificação de datas/horas operacionais (`data_hora_*`);
* Conversão colunar para Apache Parquet de alta performance;
* Tipagem defensiva contra dados nulos e horários suspensos (`TBC`).

### 3. Camada Gold (`gold/`)
* Consolidação e deduplicação de múltiplos snapshots em um Star Schema limpo;
* **Dimensões:** `dim_navios`, `dim_bercos` (com operador portuário) e `dim_calendario`;
* **Fatos:** `fct_manobras_previsto_vs_realizado` (cálculo de atrasos em minutos e SLA) e `fct_tempo_fila_barra` (tempo de espera em fundeio).

---

## Orquestração com Apache Airflow

As transformações (silver → gold) são executadas por uma **DAG do Airflow** (`maritimo_transform`), rodando em containers Docker no homelab. A pasta [orquestracao/](orquestracao/) contém as DAGs e o script de disparo; a documentação detalhada está no [README da orquestração](orquestracao/README.md).

Decisões de arquitetura em resumo:

* **Airflow 3.3.2 com LocalExecutor + Postgres** — leve o suficiente para os recursos do homelab (sem Redis/Celery). O Postgres guarda apenas os metadados do Airflow.
* **Agendamento no cron do host, não no Airflow** (`schedule=None`). A coleta (Selenium) depende de site externo e roda no host; o cron dispara a DAG via `docker exec` de forma **desacoplada**. Se a coleta falhar, a transformação simplesmente não acha dado novo — em vez de a DAG quebrar por falta de insumo.
* **Idempotência:** a DAG só processa os HTML que ainda não viraram Parquet, então disparar sem dado novo é inofensivo.

---

## Volumes no Docker (como o Airflow enxerga o código e os dados)

Esta é a parte que costuma gerar confusão em quem está começando, então vale explicar com calma usando o caso real deste projeto. O arquivo de referência é o [`compose.yaml` do Airflow](../../apps/airflow/compose.yaml).

### O problema que os volumes resolvem

Um container é **efêmero e isolado**: o que está dentro dele não enxerga o sistema de arquivos do host, e tudo que ele grava internamente **some quando o container é recriado**. Isso é ruim para dois casos:

1. **Código e dados que estão no host** e precisam ser vistos de dentro do container (as DAGs, os scripts `transform_*.py`, os Parquets).
2. **Estado que precisa sobreviver** a um `docker compose down` (o banco de metadados do Airflow).

Volumes são a ponte entre o mundo de dentro (container) e o mundo de fora (host/Docker). Existem dois tipos usados aqui.

### Tipo 1 — Bind mount (pasta do host → pasta do container)

Um bind mount "espelha" uma pasta do host para dentro do container. É uma janela: o que muda de um lado, muda do outro em tempo real. No nosso `compose.yaml`:

```yaml
volumes:
  - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags        # DAGs
  - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs        # logs
  - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config    # config/senhas
  - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins  # plugins

  # CÓDIGO do pipeline — somente leitura (:ro)
  - ../../workspace/maritimo-data-pipeline:/opt/airflow/workspace/maritimo-data-pipeline:ro
  # DADOS do pipeline — leitura e escrita
  - ../../data/maritimo:/opt/airflow/data/maritimo
```

A sintaxe é `caminho_no_host:caminho_no_container[:opções]`. Dois pontos merecem destaque:

* **`:ro` (read-only) no código.** O Airflow só precisa **ler/importar** os módulos `transform_silver.py` e `transform_gold.py`. Montar como somente leitura garante que um container jamais altere seu código-fonte por acidente — o container consome o código, não o edita.
* **Dados sem `:ro` (read-write).** A DAG **grava** os Parquets de silver e gold, então essa pasta precisa ser gravável. É aqui que o resultado do pipeline efetivamente "sai" do container e fica salvo no host, em `~/homelab/data/maritimo`.

Por que bind mount e não copiar os arquivos para dentro da imagem: você edita o código/DAG no host com seu editor normal e a mudança aparece no container **sem rebuild**. É o que torna o ciclo de desenvolvimento rápido.

### Tipo 2 — Named volume (volume gerenciado pelo Docker)

Para o banco de metadados do Airflow (Postgres) não usamos uma pasta do host, e sim um **volume nomeado** gerenciado pelo Docker:

```yaml
services:
  postgres:
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
# ...
volumes:
  postgres-db-volume:
```

Diferença prática em relação ao bind mount:

* O Docker guarda esses dados numa área própria dele (você não aponta uma pasta do host).
* **Sobrevive a `docker compose down`** (parar/recriar os containers não apaga os metadados).
* Só é apagado de propósito, com `docker compose down --volumes`.

Isso é ideal para estado de banco de dados: você não quer ficar mexendo nesses arquivos na mão, só quer que eles **persistam** entre reinícios.

### O detalhe de permissões (`user` e UID)

```yaml
user: "${AIRFLOW_UID:-50000}:0"
```

Como o bind mount de dados é read-write, os arquivos que o container cria (os Parquets) nascem no host com o dono definido por esse UID. Rodando o container com o **UID do host (1000)**, os Parquets gerados pertencem ao seu usuário (`rafa`), e não ao `root` — senão você teria que usar `sudo` para mexer nos próprios dados de saída. É um detalhe pequeno que evita muita dor de cabeça de permissão.

### Resumo mental

| Precisa que...                                             | Use          | Exemplo aqui                     |
|------------------------------------------------------------|--------------|----------------------------------|
| Container leia código/DAGs que você edita no host          | Bind mount `:ro` | `transform_*.py`, `dags/`     |
| Container grave resultados de volta no host                | Bind mount (rw)  | `data/maritimo` (silver/gold) |
| Estado de banco persista entre `down`/`up`, sem você gerenciar a pasta | Named volume | metadados do Postgres      |

---

## Tecnologias Utilizadas

* **Linguagem:** Python 3.12
* **Coleta:** Selenium WebDriver
* **Processamento & Engenharia:** pandas, PyArrow, NumPy
* **Armazenamento:** Apache Parquet (colunar)
* **Modelagem:** Star Schema
* **Orquestração:** Apache Airflow 3.3.2 (LocalExecutor + Postgres) em Docker — DAG `maritimo_transform` (silver → gold), ver [orquestracao/](orquestracao/)
* **Infraestrutura:** Docker / Docker Compose (homelab), disparo agendado via cron do host
* **Governança & Documentação:** Data Documentation as Code (Markdown / Mermaid)
* **Consumo / BI:** Qlik Sense / Qlik Cloud
* **Controle de Versão:** Git & GitHub

---

## Próximos Passos

* [x] Criar o catálogo e dicionário de dados oficial ([catalogo_de_dados.md](catalogo_de_dados.md)).
* [x] Refatorar os scripts de transformação da Silver em um módulo único e modular ([transform_silver.py](transform_silver.py)).
* [x] Criar gerador de amostras controladas ([prototype/04_transform_examples.py](prototype/04_transform_examples.py)).
* [x] Estruturar a camada Gold em Star Schema com métricas analíticas ([transform_gold.py](transform_gold.py)).
* [x] Criar métricas de pontualidade, cálculo de atrasos e tempo de fila na barra.
* [x] Planejar a arquitetura visual e mapa de dados do Dashboard (5 abas operacionais).
* [x] Implementar a orquestração das transformações via Apache Airflow (DAG: Silver $\rightarrow$ Gold) — ver [orquestracao/](orquestracao/). *O scraper permanece no cron do host por depender de Selenium/site externo; o cron dispara a DAG de forma desacoplada.*
* [x] Colocar a orquestração em execução no homelab (Airflow em Docker: api-server + scheduler + dag-processor + Postgres).
* [ ] Conectar o Qlik Sense / Qlik Cloud aos arquivos Parquet da Camada Gold.
* [ ] Desenvolver os visuais, gráficos e KPIs no Qlik conforme o mapa do dashboard.
