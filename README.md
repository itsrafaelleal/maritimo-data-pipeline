#  Marítimo Data Pipeline

> 🚧🚧🚧 **Projeto em construção**🚧🚧🚧

Pipeline de dados desenvolvido para coletar, transformar e organizar informações operacionais de um porto, com foco em **manobras previstas, navios atracados, navios fundeados e operações realizadas**.

O pipeline realiza a coleta de dados por meio de **Web Scraping com Selenium**, processa e normaliza as informações em Python e gera **snapshots a cada 4 horas**, permitindo análises de **previsão vs. realizado** ao longo do tempo.

> **📚 Leia :** [aprendizados.md](aprendizados.md) — Documento com todos os aprendizados, desafios e decisões técnicas do projeto. **Essencial para entender a evolução do pipeline.**

##  Arquitetura

Atualmente, o projeto trabalha com arquitetura medalhão:

### 🟤 Landing

Responsável pelo armazenamento dos dados brutos coletados durante o Web Scraping.

* Dados no formato HTML;
* Preservação do dado original;
* Snapshots periódicos;
* Base para reprocessamento e auditoria.

### ⚪ Silver

Responsável pelo tratamento e normalização dos dados.

* Limpeza e padronização;
* Transformações utilizando Python e pandas;
* Conversão para Parquet;
* Estruturação dos dados para consumo analítico.

### 🟡 Gold — em desenvolvimento

A próxima etapa será criar uma camada analítica com métricas e indicadores, permitindo comparar o **planejado vs. realizado** e sobre a operação portuária.

## 🛠️ Tecnologias

* **Python**
* **Selenium**
* **pandas**
* **Parquet**
* **Apache Airflow**
* **Qlik**
* **Git / GitHub**
* **VS Code**
* **Cloud Computing**

## 🔄 Fluxo do Pipeline

```text
Fonte de dados
      ↓
Web Scraping — Selenium
      ↓
Landing — HTML bruto
      ↓
Transformação — Python / pandas
      ↓
Silver — Parquet normalizado
      ↓
Gold — Métricas e modelos analíticos
      ↓
Dashboard — Qlik
```

## 📊 Análises previstas

Com a evolução do projeto, os dados poderão ser utilizados para analisar:

* Manobras previstas vs. realizadas;
* Confiabilidade das previsões;
* Atrasos e antecipações;
* Volume de operações ao longo do tempo;
* Movimentação de navios;
* Indicadores operacionais;
* Tendências e padrões das operações portuárias.

## 🚧 Próximos passos

* [ ] Refatorar os 5 scripts atuais de transformação em uma estrutura única, utilizando funções e módulos reutilizáveis.
* [ ] Criar o `process.py`, responsável por identificar quais dados já foram processados na camada Silver e quais ainda precisam ser processados.
* [ ] Implementar a orquestração do pipeline utilizando Apache Airflow.
* [ ] Estruturar a camada Gold com métricas analíticas.
* [ ] Criar métricas de confiabilidade entre previsão e realizado.
* [ ] Estudar e definir a melhor estratégia para visualização dos dados utilizando Qlik.
* [ ] Desenvolver o dashboard de acompanhamento das operações portuárias.

> 🚧 **Projeto em desenvolvimento.**
> Novas etapas, métricas e visualizações serão adicionadas conforme a evolução do pipeline.
