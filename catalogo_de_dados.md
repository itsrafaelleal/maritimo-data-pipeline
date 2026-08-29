# 📚 Catálogo de Dados - Marítimo Data Pipeline

Este documento descreve o catálogo de dados da **Camada Silver** do pipeline marítimo.

---

## 🏛️ Informações Gerais da Camada Silver
* **Formato de Armazenamento:** Apache Parquet
* **Frequência de Extração:** 4 vezes ao dia (aproximadamente às 07h, 12h, 16h e 18h).
* **Padrão de Nomenclatura dos Arquivos:** `YYYY-MM-DD_HH-MM-SS.parquet`
* **Metadados de Linhagem (Audit Columns):** Presentes em todas as 5 tabelas:
  * `data_processamento` (`datetime64[us]`): Data e hora exata em que o arquivo foi transformado pelo pipeline.
  * `arquivo_origem` (`string`): Nome do arquivo HTML bruto na Landing Raw de onde o dado se originou.
  * `snapshot_timestamp` (`datetime64[us]`): Timestamp do snapshot extraído do nome do arquivo.

---

## ⚓ Glossário de Siglas e Termos Marítimos
* **ATB (*Actual Time of Berthing*):** Horário real em que a embarcação atracou no berço.
* **ATS (*Actual Time of Sailing*):** Horário real em que a embarcação desatracou e zarpou.
* **ETS (*Estimated Time of Sailing*):** Previsão estimada de saída do navio.
* **BB (*Bombordo*):** Lado esquerdo da embarcação (em relação à proa/frente).
* **BE (*Boreste*):** Lado direito da embarcação (em relação à proa/frente).
* **LOA (*Length Overall*):** Comprimento total do navio, de proa a popa.
* **BOCA (*Beam*):** Largura máxima da embarcação.
* **CALADO (*Draft*):** Distância vertical entre a linha de flutuação e a quilha (fundo) do navio.
* **EK (*Even Keel*):** Calado nivelado (calado de proa igual ao de popa).
* **TBC (*To Be Confirmed*):** Informação ainda a ser confirmada pelo armador/agência.

---

## 1. Tabela: `manobras_previstas`
* **Descrição:** Registra a programação e status das manobras de entrada, saída e movimentação de navios previstas para os berços.
* **Granularidade:** Uma linha por manobra programada em um snapshot específico.

| Coluna | Tipo Pandas | Tipo Parquet | Nulo? | Descrição | Exemplo / Regras |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `data` | `datetime64[us]` | `TIMESTAMP` | Não | Data da manobra | `2026-08-27` |
| `horario` | `string` | `STRING` | Não | Texto original do horário e status | `"16:45 atb"` |
| `manobra` | `string` | `STRING` | Não | Tipo da operação prevista | `"entrada"`, `"saida"`, `"remocao"` |
| `berco` | `string` | `STRING` | Não | Berço de destino/origem da atracação | `"pnave 02"`, `"jbs 1"` |
| `bordo` | `string` | `STRING` | Sim | Lado do navio atracado ao cais | `"bb"` (bombordo), `"be"` (boreste) |
| `navio` | `string` | `STRING` | Não | Nome do navio normalizado | `"cosco shipping mexico"` |
| `rota` | `string` | `STRING` | Sim | Rota/Bacia de evolução utilizada | `"bacia 1"`, `"bacia 2"` |
| `loa` | `Int64` | `INT64` | Sim | Comprimento total da embarcação (*Length Overall*) | `33590` (metros sem pontuação / centímetros) |
| `boca` | `Int64` | `INT64` | Sim | Largura máxima da embarcação (*Beam*) | `5100` |
| `calado` | `string` | `STRING` | Sim | Medida do calado na manobra | `"11,20 ek"`, `"9,15/10,50"` |
| `situacao` | `string` | `STRING` | Sim | Situação operacional do navio | `"no canal"`, `"atracado"`, `"aguardando pratico"` |
| `hora` | `string` | `STRING` | Sim | Horário previsto isolado (HH:MM) | `"16:45"` |
| `status` | `string` | `STRING` | Sim | Sigla do status operacional | `"atb"`, `"ets"`, `"ats"` |
| `data_hora_manobra_prevista` | `datetime64[us]` | `TIMESTAMP` | Sim | Timestamp unificado (`data + hora`) | `2026-08-27 16:45:00` |
| `data_processamento` | `datetime64[us]` | `TIMESTAMP` | Não | Timestamp de ingestão/transformação | `2026-08-27 22:51:35` |
| `arquivo_origem` | `string` | `STRING` | Não | Arquivo HTML de origem | `"2026-08-27_18-00-06_manobras_previstas.html"` |
| `snapshot_timestamp` | `datetime64[us]` | `TIMESTAMP` | Não | Data/hora do snapshot extraído | `2026-08-27 18:00:06` |

---

## 2. Tabela: `manobras_realizadas`
* **Descrição:** Registra o histórico das manobras efetivamente executadas no porto, incluindo rebocadores utilizados.
* **Granularidade:** Uma linha por manobra realizada em um snapshot específico.

| Coluna | Tipo Pandas | Tipo Parquet | Nulo? | Descrição | Exemplo / Regras |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `data` | `datetime64[us]` | `TIMESTAMP` | Não | Data em que a manobra foi realizada | `2026-08-27` |
| `navio` | `string` | `STRING` | Não | Nome do navio normalizado | `"maersk pangani"` |
| `manobra` | `string` | `STRING` | Não | Tipo da operação executada | `"entrada"`, `"saida"` |
| `berco` | `string` | `STRING` | Não | Berço onde a manobra foi concluída | `"jbs 1"`, `"pnave 01"` |
| `loa` | `Int64` | `INT64` | Sim | Comprimento total da embarcação | `23780` |
| `boca` | `Int64` | `INT64` | Sim | Largura máxima da embarcação | `3879` |
| `horario` | `string` | `STRING` | Não | Texto original do horário e status | `"15:15 atb"` |
| `calado` | `string` | `STRING` | Sim | Calado da embarcação na operação | `"11,80 ek"` |
| `rota` | `string` | `STRING` | Sim | Rota de navegação interna | `"bacia 2"` |
| `bordo` | `string` | `STRING` | Sim | Lado atracado | `"bb"`, `"be"` |
| `rebocadores` | `string` | `STRING` | Sim | Rebocadores que auxiliaram a manobra | `"aries/renaud"` |
| `hora` | `string` | `STRING` | Sim | Horário de conclusão isolado (HH:MM) | `"15:15"` |
| `status` | `string` | `STRING` | Sim | Sigla do status | `"atb"`, `"ats"` |
| `data_hora_manobra_realizada` | `datetime64[us]` | `TIMESTAMP` | Sim | Timestamp unificado (`data + hora`) | `2026-08-27 15:15:00` |
| `data_processamento` | `datetime64[us]` | `TIMESTAMP` | Não | Timestamp de ingestão | `2026-08-27 22:51:35` |
| `arquivo_origem` | `string` | `STRING` | Não | Arquivo HTML de origem | `"2026-08-27_18-00-06_manobras_realizadas.html"` |
| `snapshot_timestamp` | `datetime64[us]` | `TIMESTAMP` | Não | Data/hora do snapshot | `2026-08-27 18:00:06` |

---

## 3. Tabela: `navios_atracados`
* **Descrição:** Registra a foto operacional de quais navios estavam atracados nos berços no momento do snapshot.
* **Granularidade:** Uma linha por navio atracado em um snapshot.

| Coluna | Tipo Pandas | Tipo Parquet | Nulo? | Descrição | Exemplo / Regras |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `berco` | `string` | `STRING` | Não | Berço de atracação | `"jbs 1"`, `"teporti"` |
| `bordo` | `string` | `STRING` | Sim | Lado atracado | `"bb"`, `"be"` |
| `navio` | `string` | `STRING` | Não | Nome do navio atracado | `"maersk pangani"` |
| `rota` | `string` | `STRING` | Sim | Rota de navegação | `"bacia 1"` |
| `data_hora_atracagem` | `datetime64[us]` | `TIMESTAMP` | Sim | Data e hora em que o navio atracou | `2026-08-27 17:12:00` |
| `situacao` | `string` | `STRING` | Não | Situação operacional do navio | `"atracado"` |
| `data_processamento` | `datetime64[us]` | `TIMESTAMP` | Não | Timestamp de ingestão | `2026-08-27 22:51:35` |
| `arquivo_origem` | `string` | `STRING` | Não | Arquivo HTML de origem | `"2026-08-27_18-00-06_navios_atracados.html"` |
| `snapshot_timestamp` | `datetime64[us]` | `TIMESTAMP` | Não | Data/hora do snapshot | `2026-08-27 18:00:06` |

---

## 4. Tabela: `navios_fundeados`
* **Descrição:** Registra os navios que estão aguardando na área de fundeio (barra externa) antes de atracar.
* **Granularidade:** Uma linha por navio fundeado no momento do snapshot.

| Coluna | Tipo Pandas | Tipo Parquet | Nulo? | Descrição | Exemplo / Regras |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `navio` | `string` | `STRING` | Não | Nome do navio fundeado | `"agios porfyrios"` |
| `loa` | `string` | `STRING` | Sim | Comprimento total da embarcação | `"15515"` |
| `posicao` | `string` | `STRING` | Sim | Coordenadas geográficas do ponto de fundeio | `"26 52,64 s / 048 31,29 w"` |
| `calado` | `string` | `STRING` | Sim | Calado informado na barra | `"3,67/5,11"` |
| `rota` | `string` | `STRING` | Sim | Rota de navegação | `null` |
| `data_hora_fundeado` | `datetime64[us]` | `TIMESTAMP` | Sim | Data e hora em que o navio entrou em fundeio | `2026-08-15 22:09:00` |
| `situacao` | `string` | `STRING` | Não | Situação operacional do navio | `"fundeado"` |
| `data_processamento` | `datetime64[us]` | `TIMESTAMP` | Não | Timestamp de ingestão | `2026-08-27 22:51:35` |
| `arquivo_origem` | `string` | `STRING` | Não | Arquivo HTML de origem | `"2026-08-27_18-00-06_navios_fundeados.html"` |
| `snapshot_timestamp` | `datetime64[us]` | `TIMESTAMP` | Não | Data/hora do snapshot | `2026-08-27 18:00:06` |

---

## 5. Tabela: `navios_previstos`
* **Descrição:** Registra a lista de navios esperados para chegar ao porto nos próximos dias (previsão de longo/médio prazo).
* **Granularidade:** Uma linha por navio esperado no momento do snapshot.

| Coluna | Tipo Pandas | Tipo Parquet | Nulo? | Descrição | Exemplo / Regras |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `navio` | `string` | `STRING` | Não | Nome do navio previsto | `"msc barcelona vi"` |
| `loa` | `string` | `STRING` | Sim | Comprimento total do navio | `"27040"` |
| `calado` | `string` | `STRING` | Sim | Calado estimado | `"tbc"` (*to be confirmed*), `"10,50"` |
| `rota` | `string` | `STRING` | Sim | Rota esperada | `null` |
| `data_hora_previsao_de_chegada` | `datetime64[us]` | `TIMESTAMP` | Sim | Data e hora estimada para a chegada | `2026-08-29 02:00:00` |
| `rebocadores` | `string` | `STRING` | Sim | Rebocadores previstos | `null` |
| `situacao` | `string` | `STRING` | Não | Situação operacional do navio | `"chegada_prevista"` |
| `data_processamento` | `datetime64[us]` | `TIMESTAMP` | Não | Timestamp de ingestão | `2026-08-27 22:51:35` |
| `arquivo_origem` | `string` | `STRING` | Não | Arquivo HTML de origem | `"2026-08-27_18-00-06_navios_previstos.html"` |
| `snapshot_timestamp` | `datetime64[us]` | `TIMESTAMP` | Não | Data/hora do snapshot | `2026-08-27 18:00:06` |
