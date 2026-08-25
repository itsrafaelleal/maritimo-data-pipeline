# Aprendizados do Projeto

Este arquivo reúne aprendizados, decisões técnicas e problemas encontrados durante o desenvolvimento do projeto.


## 1. Arquivos com prefixos numéricos na raiz

Exemplos iniciais de arquivos:
- `01_scrapy.py`
- `02_transform_silver.py`

### Problema
No Python, nomes de módulos que começam com números não podem ser importados diretamente. Por exemplo, tentar executar o comando abaixo resulta em um erro de sintaxe (`SyntaxError`), pois o nome do arquivo não é um identificador válido na linguagem:

```python
from 02_transform_silver import processar_arquivo_html
```

Para que ferramentas como o Airflow ou outros scripts consigam importar funções diretamente desses arquivos, os nomes devem seguir as regras de identificadores do Python (ex: `extract.py`, `transform.py`, `silver.py`).

### Aprendizado
A ordem lógica de um pipeline de dados não precisa ser representada numericamente no nome dos arquivos físicos. 

Em vez de estruturar assim:
- `01_scrapy.py`
- `02_transform.py`
- `03_load.py`

Podemos adotar nomes descritivos e padronizados:
- `scraping.py`
- `transform.py`
- `load.py`

A ordem de execução do pipeline deve ser controlada explicitamente pelo orquestrador ou pelo script principal de execução.

---

## 2. Princípio DRY — Don't Repeat Yourself

### Contexto
Durante o desenvolvimento, cogitou-se criar múltiplos arquivos de transformação separados por etapas ou tabelas:
- `02_01_transform.py`
- `02_02_transform.py`
- `02_03_transform.py`
- `02_04_transform.py`
- `02_05_transform.py`

### Problema
Se esses arquivos compartilham cerca de 90% de código idêntico, cria-se um gargalo de manutenção severo. Caso seja necessário alterar uma regra comum — como o formato de salvamento de pastas, o tratamento de acentos ou uma limpeza específica —, a alteração precisaria ser replicada manualmente em todos os arquivos.

### Aprendizado
Sempre que houver lógica duplicada entre módulos, deve-se aplicar o princípio DRY. Uma abordagem mais sustentável consiste em centralizar a lógica comum em uma função ou classe de transformação genérica, passando parâmetros ou utilizando funções de callback apenas para as particularidades de cada tabela ou arquivo.

---

## 3. Web Scraping — Selenium vs Requests/BeautifulSoup

### Contexto
O Selenium automatiza um navegador real (como o Chromium), o que demanda mais recursos de memória e processamento. 

### Problema / Comparação
Se a página web alvo não depende de renderização dinâmica pesada em JavaScript (como aplicações em React, Vue ou Angular), abordagens mais leves costumam ser mais diretas:

- Uso de `requests` ou `httpx` em conjunto com `BeautifulSoup`.
- Uso direto do pandas com `pd.read_html()` caso os dados estejam estruturados em tabelas HTML nativas.

### Decisão neste projeto
Mesmo reconhecendo que ferramentas como `requests` ou `httpx` podem ser mais eficientes em termos de performance para páginas estáticas, **optou-se por utilizar o Selenium**. 

A justificativa para essa escolha passa pelo objetivo pedagógico do projeto: praticar e consolidar os conhecimentos adquiridos sobre Selenium (estudados através do material do Dunossauro).

### Aprendizado
Nem toda decisão técnica precisa ser ditada estritamente pela máxima performance ou eficiência computacional. Em projetos de estudo e portfólio, ponderar objetivos de aprendizado pessoal torna perfeitamente válida a escolha de uma ferramenta mais robusta ou complexa.