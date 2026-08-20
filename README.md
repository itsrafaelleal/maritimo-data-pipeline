# Marítimo Data Pipeline

Pipeline de dados que coleta, transforma e modela informações operacionais de um porto (manobras previstas, navios atracados, fundeados e realizados), gerando snapshots a cada 4 horas para análise de previsão vs realizado.

O projeto implementa as camadas landing (HTML bruto) e silver (Parquet normalizado), com transformação em Python/pandas, e está preparado para evoluir para modelos analíticos (gold) e dashboards de operações portuárias.

**Tecnologias:** Python, Selenium, pandas, Parquet, VS Code, Git/GitHub.

**Objetivo:** Servir como portfólio em Engenharia de Dados / Analytics Engineering, demonstrando pipeline ETL, modelagem de dados e capacidade de gerar insights sobre operações portuárias.

> Projeto em construção – em breve: camada gold, métricas de confiabilidade de previsão e dashboard no Power BI.
