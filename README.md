# Marítimo Data Pipeline

Pipeline de dados desenvolvido para coletar, transformar, modelar e organizar informações operacionais de um porto, com foco em **manobras previstas, manobras realizadas, navios atracados, navios fundeados e chegadas previstas**.

O pipeline realiza a coleta de dados por meio de **Web Scraping com Selenium**, processa e normaliza as informações na camada **Silver** com Python e pandas gerando arquivos **Apache Parquet**, e estrutura a camada **Gold** em **Modelagem Dimensional (Star Schema)** pronta para consumo em dashboards analíticos no **Qlik (Qlik Sense / Qlik Cloud)**.

> **Documentação e Aprendizados:**
> * [catalogo_de_dados.md](catalogo_de_dados.md) — **Catálogo oficial e dicionário de dados** com esquemas, tipos, métricas de negócio e mapa completo do dashboard.
> * [aprendizados.md](aprendizados.md) — Documento com decisões técnicas, desafios arquiteturais e boas práticas de engenharia de dados adotadas no projeto.

---

## Status Atual do Projeto

O projeto avançou significativamente nas camadas de ingestão, transformação e modelagem analítica:

* **Landing Raw:** Scraping automatizado coletando snapshots periódicos em HTML.
* **Silver:** Pipeline unificado e modular ([transform_silver.py](transform_silver.py)) tratando os dados brutos, tipando datas/horas padronizadas (`datetime64[us]`) e gerando arquivos Parquet.
* **Gold:** Modelagem dimensional em Star Schema ([transform_gold.py](transform_gold.py)) concluída, gerando tabelas Fato de pontualidade (`fct_manobras_previsto_vs_realizado`), tempo de espera na barra (`fct_tempo_fila_barra`) e Dimensões (`dim_navios`, `dim_bercos`, `dim_calendario`).
* **Governança & BI:** Catálogo de dados detalhado e planejamento funcional do dashboard gerencial no Qlik com 5 abas operacionais.

---

## A Importância do Catálogo de Dados

O arquivo [catalogo_de_dados.md](catalogo_de_dados.md) é o coração da governança deste projeto. Ele atua como um **contrato de dados (*Data Contract*)** entre a Engenharia de Dados e a camada de Business Intelligence (BI):

1. **Dicionário Técnico Completo:** Descreve cada coluna, tipo no Pandas, tipo no Parquet, regras de nulos e descrições de negócio para as camadas Silver e Gold.
2. **Memória de Cálculo dos Indicadores:** Formaliza a lógica de métricas críticas (como a *Taxa de Pontualidade*, *Tempo Médio de Espera na Barra* e *Atraso Efetivo*), garantindo que desenvolvedores e analistas de BI falem a mesma língua.
3. **Diagramas ERD Vivos:** Documenta visualmente o Star Schema usando diagramas como código (Mermaid), rastreando as chaves primárias (PK) e estrangeiras (FK).
4. **Mapa do Dashboard:** Especifica detalhadamente as 5 abas do painel, filtros e a grade de auditoria com 15 colunas para conferência de dados.

---

## Arquitetura Medalhão

```text
Fonte de Dados Portuária (Web)
            ↓
   Web Scraping — Selenium
            ↓
  Landing Raw — HTML Bruto (Snapshots a cada 4h)
            ↓
  Transformação Silver — Python / pandas / PyArrow
            ↓
  Silver — Parquet Normalizado e Tipado
            ↓
  Modelagem Gold — transform_gold.py (Star Schema)
            ↓
  Gold — Parquets Dimensionais (Fatos e Dimensões)
            ↓
  Dashboard Executivo & Operacional — Qlik (Qlik Sense / Cloud)
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

## Tecnologias Utilizadas

* **Linguagem:** Python 3.12
* **Coleta:** Selenium WebDriver
* **Processamento & Engenharia:** pandas, PyArrow, NumPy
* **Armazenamento:** Apache Parquet (colunar)
* **Modelagem:** Star Schema (Kimball)
* **Governança & Documentação:** Data Documentation as Code (Markdown / Mermaid)
* **Consumo / BI:** Qlik Sense / Qlik Cloud
* **Orquestração:** Apache Airflow *(próxima etapa)*
* **Controle de Versão:** Git & GitHub

---

## Próximos Passos

* [x] Criar o catálogo e dicionário de dados oficial ([catalogo_de_dados.md](catalogo_de_dados.md)).
* [x] Refatorar os scripts de transformação da Silver em um módulo único e modular ([transform_silver.py](transform_silver.py)).
* [x] Criar gerador de amostras controladas ([prototype/04_transform_examples.py](prototype/04_transform_examples.py)).
* [x] Estruturar a camada Gold em Star Schema com métricas analíticas ([transform_gold.py](transform_gold.py)).
* [x] Criar métricas de pontualidade, cálculo de atrasos e tempo de fila na barra.
* [x] Planejar a arquitetura visual e mapa de dados do Dashboard (5 abas operacionais).
* [ ] Implementar a orquestração do ciclo completo via Apache Airflow (DAG: Scrape $\rightarrow$ Silver $\rightarrow$ Gold $\rightarrow$ Qlik Reload).
* [ ] Conectar o Qlik Sense / Qlik Cloud aos arquivos Parquet da Camada Gold.
* [ ] Desenvolver os visuais, gráficos e KPIs no Qlik conforme o mapa do dashboard.
