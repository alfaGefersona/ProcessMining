# Seminário NoSQL -  Elasticsearch

> **Tema:** Search Engine — Busca textual complexa (Full-text search) e ecossistema ELK
> **Base de dados:** Processos judiciais do TJPR via API pública Datajud (CNJ)

> Disciplinha: de Gerenciamento De Dados Não Estruturados E Semiestruturados

> Alunos: Geferson Artuzo e Luiz Henrique Oliveira Neckel 

---

## Contexto

O projeto de Process Mining já consome a API pública do CNJ (**Datajud**), que é um cluster
Elasticsearch gerenciado pelo próprio CNJ. O pipeline extrai processos via Query DSL do ES,
pagina com `search_after` e gera event logs no formato IEEE XES.

Para o seminário, foi criada uma camada adicional que:

1. Sobe um **ES local** via Docker
2. Re-indexa os dados extraídos com mapping explícito
3. Demonstra as features do ES diretamente

---

## Pré-requisitos

| Ferramenta | Versão | Como instalar |
|---|---|---|
| Python | ≥ 3.11 | [python.org](https://python.org) |
| Docker Desktop | ≥ 4.x | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Dependências Python | — | `pip install -r requirements.txt` |

---

## Arquivos criados para o seminário

```
ProcessMining/
├── docker-compose.yml          # ES 8.13 + Kibana 8.13 (single-node)
└── elasticsearch/
    ├── es_indexer.py           # cria índice com mapping + bulk index do CSV
    └── es_demo.py              # demonstração das 6 features do ES
```

---

## Ordem de execução

### 1. Ativa o ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Ajusta o limite de extração (para demo)

Em `datajud/config.py`, reduza o limite para extrações rápidas:

```python
MAX_PROCESSOS = 500
```

> Para análise completa de Process Mining, volte para `50000`.

### 3. Extrai os dados do Datajud

```bash
python main.py
```

Saída gerada em `output/TJPR_YYYYMMDD_HHMMSS.csv`.

### 4. Sobe o ELK Stack

```bash
docker compose up -d
```

Aguarda ~30 segundos. Verifica saúde:

```bash
curl http://localhost:9200/_cluster/health
```

Esperado: `"status":"yellow"` ou `"status":"green"`.

### 5. Indexa os dados no ES local

```bash
python elasticsearch/es_indexer.py
```

O indexador:
- Lê o CSV mais recente de `output/`
- Agrupa eventos por processo (1 doc por processo)
- Cria índice `processos_judiciais` com mapping explícito
- Faz bulk index de todos os processos

Para reindexar do zero:
```bash
python elasticsearch/es_indexer.py --reset
```

### 6. Executa a demo

```bash
python elasticsearch/es_demo.py
```

---

## Features demonstradas no es_demo.py

### Demo 1 — Full-text Search

Busca com relevância automática (algoritmo BM25). O ES tokeniza o texto, aplica
stemmer em português e retorna documentos ordenados por score de relevância.

```python
{"match": {"assunto_principal": {"query": "violência doméstica", "operator": "or"}}}
```

**Diferencial vs SQL:** `LIKE '%violência%'` não ranqueia resultados. ES retorna o mais
relevante primeiro.

---

### Demo 2 — Multi-match com Boost

Busca em múltiplos campos simultaneamente, com peso diferente por campo.

```python
{"multi_match": {"query": "homicídio feminicídio", "fields": ["assunto_principal^2", "classe"]}}
```

`^2` dobra o peso do campo `assunto_principal` no cálculo do score.

---

### Demo 3 — Bool Query

Combina condições lógicas com impacto diferente no score:

| Cláusula | Efeito no score | Obrigatório |
|---|---|---|
| `must` | Sim | Sim |
| `should` | Sim | Não (mas aumenta score) |
| `filter` | Não | Sim (filtra sem afetar rank) |

---

### Demo 4 — Highlight

Retorna o trecho exato do documento que casou com a busca, com marcadores ao redor.

```json
"highlight": {"assunto_principal": [">>> estupro <<<  de vulnerável"]}
```

Útil para interfaces de busca que mostram snippet de contexto.

---

### Demo 5 — Aggregations

Analytics diretamente no ES, sem exportar dados:

- **terms:** contagem por valor de campo (`GROUP BY` distribuído)
- **date_histogram:** distribuição temporal por ano/mês
- Combinável com queries (agrega só sobre o subconjunto filtrado)

---

### Demo 6 — search_after

Paginação eficiente para grandes volumes. Usa o valor de `sort` do último documento
como cursor para a próxima página.

**Por que não `from/size`:** `from: 10000` obriga o ES a carregar e descartar 10k docs.
`search_after` vai direto ao próximo ponto — O(log n).

> Esta é exatamente a técnica usada em `datajud/client.py` para extrair 50k+ processos.

---

## Kibana (o "K" do ELK)

Acessa `http://localhost:5601`.

**Criar Data View:**
1. Stack Management → Data Views → Create data view
2. Index pattern: `processos_judiciais`
3. Timestamp field: `data_ajuizamento`

**Dashboard sugerido:**
- Gráfico de pizza: processos por `tribunal`
- Histograma: ajuizamentos por ano (`data_ajuizamento`)
- Tabela: top classes processuais
- Barra de busca: full-text sobre `assunto_principal`

---

## Kibana — Discover (barra de busca KQL)

> Menu lateral → **Discover** → digita na barra de busca no topo

KQL (Kibana Query Language) é mais simples que Query DSL. Filtra em tempo real.

```kql
# Processos com violência doméstica
assunto_principal : "violência doméstica"
```

```kql
# Homicídio OU feminicídio
assunto_principal : "homicídio" OR assunto_principal : "feminicídio"
```

```kql
# Grau G1 com mais de 10 eventos
grau : "G1" AND total_eventos > 10
```

```kql
# Qualquer assunto com "lesão" — busca parcial
assunto_principal : lesão*
```

```kql
# Combinado: classe ordinário + assunto violência + ajuizado depois de 2022
classe : "Ordinário" AND assunto_principal : "violência" AND data_ajuizamento > "2022-01-01"
```

> **Na apresentação:** altera o filtro KQL → os painéis do Dashboard atualizam juntos. Mostra o poder do ELK como stack integrada.

---

## Queries para Dev Tools (Kibana → Dev Tools → Console)

### Bloco 1 — Entendendo o índice

```json
# Ver mapping completo (estrutura dos campos)
GET processos_judiciais/_mapping

# Estatísticas do índice (tamanho, docs, segmentos)
GET processos_judiciais/_stats

# Quantos documentos
GET processos_judiciais/_count
```

---

### Bloco 2 — Full-text vs Keyword (impacto do analyzer)

```json
# text + analyzer portuguese: "violência" casa "violento", "violências"
GET processos_judiciais/_search
{
  "query": { "match": { "assunto_principal": "violência" } },
  "size": 3,
  "_source": ["assunto_principal", "tribunal"]
}
```

```json
# keyword: busca EXATA — maiúscula diferente, acento diferente = sem resultado
GET processos_judiciais/_search
{
  "query": { "term": { "assunto_principal.keyword": "Violência Doméstica Contra a Mulher" } },
  "size": 3,
  "_source": ["assunto_principal"]
}
```

> **Ponto de apresentação:** mesmo dado, campo diferente, comportamento oposto.
> `text` = busca semântica. `keyword` = filtro exato (usado em aggregations).

---

### Bloco 3 — Explain (decomposição do score BM25)

```json
# Por que este documento tem este score?
# Substitui <ID> pelo _id retornado em qualquer busca anterior
GET processos_judiciais/_explain/<ID>
{
  "query": { "match": { "assunto_principal": "homicídio" } }
}
```

Retorna decomposição: `tf` (frequência do termo), `idf` (raridade), `fieldNorm` (tamanho do campo).

---


### Bloco 4 — Aggregations aninhadas

```json
# Por tribunal → por ano → média de eventos por processo
GET processos_judiciais/_search
{
  "size": 0,
  "aggs": {
    "por_tribunal": {
      "terms": { "field": "tribunal", "size": 5 },
      "aggs": {
        "por_ano": {
          "date_histogram": {
            "field": "data_ajuizamento",
            "calendar_interval": "year",
            "format": "yyyy"
          },
          "aggs": {
            "media_eventos": {
              "avg": { "field": "total_eventos" }
            }
          }
        }
      }
    }
  }
}
```

> **Ponto de apresentação:** 3 níveis de agregação, zero JOINs, responde em milissegundos.

---

### Bloco 5 — Highlight em múltiplos campos

```json
GET processos_judiciais/_search
{
  "query": {
    "multi_match": {
      "query": "lesão corporal doméstica",
      "fields": ["assunto_principal^3", "classe", "atividades"]
    }
  },
  "highlight": {
    "fields": {
      "assunto_principal": { "pre_tags": ["**"], "post_tags": ["**"] },
      "atividades":        { "pre_tags": ["**"], "post_tags": ["**"], "number_of_fragments": 2 }
    }
  },
  "_source": ["assunto_principal", "classe", "total_eventos"],
  "size": 3
}
```

---

### Bloco 6 — Performance: índice invertido vs varredura

```json
# RUIM: wildcard força varredura completa O(n)
GET processos_judiciais/_search
{
  "query": { "wildcard": { "assunto_principal.keyword": "*violência*" } },
  "size": 3
}
```

```json
# CERTO: match usa índice invertido ~O(1)
GET processos_judiciais/_search
{
  "query": { "match": { "assunto_principal": "violência" } },
  "size": 3
}
```

