# Documentação Técnica — Plataforma de Process Mining Judicial

> **Sistema:** Extração, transformação e análise de processos judiciais via API Datajud (CNJ)
> **Versão:** Python 3.x · PM4Py ≥ 2.7 · IEEE XES 1.0
> **Tribunais cobertos:** TJPR, TJRS (extensível a qualquer tribunal no Datajud)

---

## Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura e Estrutura de Arquivos](#2-arquitetura-e-estrutura-de-arquivos)
3. [Configuração e Instalação](#3-configuração-e-instalação)
4. [Pipeline de Extração — Passo a Passo](#4-pipeline-de-extração--passo-a-passo)
5. [Pipeline de Análises — Passo a Passo](#5-pipeline-de-análises--passo-a-passo)
6. [Estrutura do Event Log](#6-estrutura-do-event-log)
7. [Módulos de Análise — O que Cada Script Faz](#7-módulos-de-análise--o-que-cada-script-faz)
8. [Técnicas de Process Mining Implementadas](#8-técnicas-de-process-mining-implementadas)
9. [Análises Práticas — Perguntas e Respostas](#9-análises-práticas--perguntas-e-respostas)
10. [Artefatos de Saída](#10-artefatos-de-saída)
11. [Customização e Extensibilidade](#11-customização-e-extensibilidade)
12. [Solução de Problemas](#12-solução-de-problemas)

---

## 1. Visão Geral do Projeto

Esta plataforma extrai dados de processos judiciais da **API pública Datajud (CNJ)** e os transforma em **event logs padronizados**, prontos para análise com ferramentas de Process Mining como Disco, ProM, Celonis, Apromore e PM4Py.

### O que é Process Mining aplicado ao Judiciário?

Process Mining é uma disciplina que combina ciência de dados com gestão de processos. Em vez de perguntar "como achamos que o processo funciona?", ele responde "como o processo **realmente** funciona, com base em dados concretos de execução".

No contexto judicial, isso significa:

- **Descobrir** o fluxo real dos processos (não o fluxo prescrito pelo CPC)
- **Medir** o tempo real em cada etapa — identificar gargalos com precisão cirúrgica
- **Verificar** se os processos seguem o rito normativo (conformance checking)
- **Comparar** desempenho entre tribunais, varas e períodos
- **Identificar** retrabalho, loops, redistribuições e desvios anômalos
- **Classificar** processos em "happy path" vs. desvios procedimentais

### Fluxo de Alto Nível

```
Datajud API (CNJ)
      │
      │  Elasticsearch search_after pagination
      │  Retry + exponential backoff
      ▼
datajud/client.py  ─────→  generator de raw hits (JSON)
      │
      │  JSON aninhado → trace estruturado
      │  Deduplica eventos | Ordena cronologicamente
      ▼
datajud/transform.py  ──→  generator de traces {attrs, events}
      │
      │  list() coleta todos os traces em memória
      ▼
      ├─── xes/writer.py       →  {TRIBUNAL}_{ts}.xes   (IEEE XES 1.0 — Disco / PM4Py)
      ├─── tabular/writer.py   →  {TRIBUNAL}_{ts}.csv   (event log plano — Disco / PM4Py)
      └─── dashboard/writer.py →  {TRIBUNAL}_{ts}.html  (dashboard interativo — browser)
                │
                ▼ (análises downstream)
      analises/exportar_filtrado.py   →  Log filtrado por classe
      analises/happy_path_report.py   →  Classificação happy path
      analises/analisar.py            →  Análise PM4Py completa (9 PNGs)
      analises/pm4py_analises.ipynb   →  Notebook interativo (32 células)
```

---

## 2. Arquitetura e Estrutura de Arquivos

```
ProcessMining/
│
├── main.py                    # Ponto de entrada principal — extração completa
├── run_pipeline.py            # Orquestrador — executa as 4 etapas de análise
├── requirements.txt           # requests, openpyxl, pm4py
│
├── datajud/                   # Camada de extração (API → dados brutos)
│   ├── config.py              # TODA a configuração: credenciais, tribunais, campos, query
│   ├── client.py              # Cliente HTTP: paginação search_after + retry/backoff
│   └── transform.py           # Transformação: JSON bruto → traces estruturados
│
├── xes/
│   └── writer.py              # Serialização IEEE XES 1.0 compliant
│
├── tabular/
│   └── writer.py              # Serialização CSV e XLSX (event log plano)
│
├── dashboard/
│   └── writer.py              # Dashboard HTML5 auto-contido (vis.js + Chart.js)
│
├── analises/
│   ├── exportar_filtrado.py   # Filtrar log por classe processual → XES/CSV/XLSX
│   ├── happy_path_report.py   # Análise de happy path (3 níveis) + transições
│   ├── analisar.py            # Análise PM4Py completa de um tribunal → 9 PNGs
│   ├── pm4py_analises.ipynb   # Notebook Jupyter interativo (32 células)
│   └── imgs/                  # PNGs gerados pelos scripts de análise
│
├── docs/
│   └── PROCESSO.md            # Este documento
│
└── output/                    # Artefatos gerados (gitignored)
    ├── TJPR_20260101_120000.xes
    ├── TJPR_20260101_120000.csv
    ├── TJPR_20260101_120000.html
    └── ...
```

### Responsabilidades por camada

| Camada | Módulo | Responsabilidade |
|--------|--------|-----------------|
| Extração | `datajud/client.py` | Comunicação HTTP com a API Datajud. Paginação, retry, backoff. |
| Transformação | `datajud/transform.py` | Converter JSON bruto em estrutura de trace. Deduplicação, ordenação, granularidade de atividades. |
| Configuração | `datajud/config.py` | Único ponto de controle para credenciais, tribunais, campos extraídos e filtros. |
| Serialização XES | `xes/writer.py` | Produzir arquivo XML compatível com IEEE XES 1.0 e extensões concept/time/lifecycle/org. |
| Serialização tabular | `tabular/writer.py` | Produzir CSV (UTF-8 BOM) e XLSX com formatação. Uma linha por evento. |
| Dashboard | `dashboard/writer.py` | Dashboard HTML auto-contido com DFG interativo, gráficos e tabela de eventos. |
| Análise | `analises/` | Scripts especializados e notebook Jupyter para todas as análises de Process Mining. |

---

## 3. Configuração e Instalação

### Pré-requisitos

```bash
# macOS — Graphviz (necessário para gerar PNGs de DFG, Petri Net e BPMN)
brew install graphviz

# Python 3.9+
python3 --version
```

### Instalação (primeira vez)

```bash
# 1. Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependências Python
pip install -r requirements.txt
# Instala: requests>=2.31, openpyxl>=3.1, pm4py>=2.7

# 3. Verificar instalação
python -c "import pm4py; print(pm4py.__version__)"
```

### Parâmetros de configuração (`datajud/config.py`)

Todos os parâmetros de extração estão em um único arquivo. **Não é necessário modificar nenhum outro arquivo** para customizar a extração.

| Parâmetro | O que controla | Valor padrão |
|-----------|---------------|--------------|
| `API_KEY` | Credencial de acesso à API Datajud pública | Chave pública CNJ |
| `BASE_URL` | Endpoint base da API Datajud | `https://api-publica.datajud.cnj.jus.br` |
| `TRIBUNAIS` | Dicionário `{alias_elasticsearch: nome_legível}` | TJPR, TJRS |
| `QUERY_BODY` | Filtro Elasticsearch DSL completo | AP Ordinária + violência (L1) + doméstica/protetiva/mulher (L2) + range 2020–2026 — ver nota abaixo |
| `CAMPOS_TRACE` | Lista de atributos extraídos por processo | 10 campos padrão |
| `CAMPOS_EVENTO_EXTRAS` | Atributos extras por movimento | `event:codigo_tpu` |
| `PAGE_SIZE` | Processos por requisição (máx. 10.000) | 100 |
| `REQUEST_DELAY_SEC` | Pausa entre requisições (evita rate-limit) | 0.5s |
| `MAX_RETRIES` | Tentativas antes de salvar progresso parcial | 3 |
| `MAX_PROCESSOS` | Limite de processos por tribunal (`None` = ilimitado) | `None` |

> **API Key pública atual:**
> `cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==`
>
> Se ocorrer erro 401, a CNJ pode ter rotacionado a chave.
> Consulte: https://datajud-wiki.cnj.jus.br/api-publica/acesso

> **Nota — QUERY_BODY atual (v3 — violência geral + doméstica/protetiva, 2020-2026):**
>
> ```python
> QUERY_BODY = {
>     "query": {"bool": {
>         "must": [
>             {"match": {"classe.nome": "Procedimento Ordinário"}},
>             {"range": {"dataAjuizamento": {
>                 "gte": "20200101000000",   # 2020-01-01
>                 "lte": "20260516235959",   # 2026-05-16
>             }}},
>         ],
>         "should": [
>             # L1 — violência geral
>             {"match": {"assuntos.nome": "Violência"}},
>             {"match": {"assuntos.nome": "Lesão"}},
>             {"match": {"assuntos.nome": "Homicídio"}},
>             {"match": {"assuntos.nome": "Feminicídio"}},
>             {"match": {"assuntos.nome": "Estupro"}},
>             {"match": {"assuntos.nome": "Ameaça"}},
>             # L2 — doméstica/protetiva/mulher
>             {"match": {"assuntos.nome": "Doméstica"}},
>             {"match": {"assuntos.nome": "Protetiva"}},
>             {"match": {"assuntos.nome": "Mulher"}},
>         ],
>         "minimum_should_match": 1,
>     }},
>     "sort": [{"dataHoraUltimaAtualizacao": {"order": "asc"}}],
>     "_source": True,
> }
> ```
>
> **Estratégia de análise em dois níveis:**
> - **L1 — baseline:** toda violência extraída (geral: homicídio, estupro, lesão, etc.)
> - **L2 — subconjunto:** violência doméstica/protetiva/mulher (pós-processamento em `analise_violencia_mulher.py`)
> - **Comparação L2 vs L1** → evidencia prioridade operacional (ou ausência) — CNJ Res. 254/2018
>
> **Histórico de versões do filtro:**
> | Versão | Filtro assunto | Problema/Melhoria |
> |--------|---------------|-------------------|
> | v1 | `Doméstica` OR `Mulher` | Grupo "outros" contaminado |
> | v2 | Sem filtro | Captava crimes sem violência |
> | **v3** | Violência+Lesão+Homicídio+Feminicídio+Estupro+Ameaça+Doméstica+Protetiva+Mulher | L1/L2 corretos |
>
> **⚠️ Filtro de finalizados:** API não expõe campo status/situação — não é possível filtrar
> processos encerrados no Elasticsearch. Filtragem em pós-processamento:
> - `exportar_filtrado.py` → remove sem atividade terminal (em andamento)
> - `happy_path_report.py` → garante 1º evento ≥ data-inicio AND último ≤ data-fim
>
> Filtragem de classe exata: `exportar_filtrado.py` via `case:classe ==`.

---

## 4. Pipeline de Extração — Passo a Passo

Execute a extração completa com:

```bash
source .venv/bin/activate
python main.py
```

Abaixo está o que acontece internamente, etapa por etapa.

---

### Etapa 1 — Leitura da Configuração (`datajud/config.py`)

O sistema carrega os tribunais configurados em `TRIBUNAIS`, o filtro `QUERY_BODY`, e os mapeamentos de campos `CAMPOS_TRACE` e `CAMPOS_EVENTO_EXTRAS`.

Cada entrada em `CAMPOS_TRACE` define:
- O nome do atributo no XES (ex: `"case:tribunal"`)
- O caminho JSON no hit da API (ex: `["tribunal"]`)
- O tipo XES (ex: `"string"`)

---

### Etapa 2 — Busca na API (`datajud/client.py`)

Para cada tribunal, `fetch_all_hits(alias, tribunal_nome)` executa:

```
Página 1:  POST /api_publica_tjpr/_search   { query, sort, size: 100 }
           → recebe até 100 hits + cursor search_after

Página 2:  POST /api_publica_tjpr/_search   { ..., search_after: [cursor] }
           → próximas 100 → novo cursor

... repete até hits retornados < PAGE_SIZE (última página)
```

**Resiliência a falhas:**
- Cada requisição tem até `MAX_RETRIES` tentativas
- Backoff exponencial: 5s → 15s → 45s entre tentativas
- Timeout, erros HTTP e JSON inválido são capturados
- Se todas as tentativas falharem, o progresso até aquele ponto é preservado e a extração encerra graciosamente

**O que é retornado:** um generator Python de hits JSON brutos. Cada hit é um documento Elasticsearch com a estrutura completa do processo judicial.

---

### Etapa 3 — Transformação (`datajud/transform.py`)

Para cada hit bruto, `hit_to_trace(hit, tribunal_nome)` executa 4 operações:

#### 3.1 — Extração de atributos do caso

Navega o JSON aninhado via `get_nested(obj, path)` — função segura que retorna `None` em vez de lançar `KeyError`/`IndexError` quando um campo não existe.

```python
# Exemplo de como o campo "case:assunto_principal" é extraído:
# path = ["assuntos", 0, "nome"]
# get_nested(hit["_source"], ["assuntos", 0, "nome"])
# → "Danos Morais" (ou None se o processo não tiver assuntos)
```

#### 3.2 — Construção dos nomes de atividade

`build_activity_name(mov)` combina o nome do movimento com o primeiro complemento tabular:

```
Movimento: "Juntada de Petição"
Complemento: "Contestação"
→ Atividade: "Juntada de Petição - Contestação"

Movimento: "Sentença"
Complemento: (nenhum)
→ Atividade: "Sentença"
```

Essa granularidade é fundamental: sem o complemento, "Juntada de Petição de Contestação" e "Juntada de Petição de Recurso" aparecem como a mesma atividade no DFG, mascarando diferenças críticas no fluxo.

#### 3.3 — Deduplicação de eventos

`_dedup_events(events)` remove eventos duplicados usando como chave o par `(event:codigo_tpu, time:timestamp)`. Quando o código TPU não está disponível, usa `(concept:name, time:timestamp)`.

Isso é necessário porque a API Datajud pode retornar o mesmo movimento mais de uma vez (ex: movimentos retroativamente registrados que coincidem com registros já existentes).

#### 3.4 — Ordenação cronológica

Os eventos são ordenados por `time:timestamp` (crescente). Essa ordenação garante que o event log reflita a sequência temporal real dos movimentos, independentemente da ordem em que foram indexados na API.

**Resultado final:** um dicionário Python com a estrutura:

```python
{
    "attrs": {
        "concept:name": ("0000001-11.2024.8.16.0001", "string"),
        "case:tribunal": ("TJPR", "string"),
        "case:classe": ("Procedimento Comum Cível", "string"),
        "case:data_ajuizamento": ("20240110000000", "date"),
        ...
    },
    "events": [
        {
            "concept:name": ("Distribuição", "string"),
            "time:timestamp": ("20240110143200", "date"),
            "lifecycle:transition": ("complete", "string"),
            "org:resource": ("1ª Vara Cível de Curitiba", "string"),
            "event:codigo_tpu": (26, "int"),
        },
        ...  # mais eventos, em ordem cronológica
    ]
}
```

---

### Etapa 4 — Coleta e Exportação (`main.py`)

`main.py` coleta todos os traces em memória com `list(traces_gen)` antes de exportar. Isso é necessário porque cada formato de saída precisa percorrer os traces na íntegra — e um generator Python só pode ser percorrido uma vez.

Com os traces em memória, `main.py` chama as 4 funções de escrita **com o mesmo conjunto de dados**:

```python
traces = list(hits_to_traces(fetch_all_hits(alias, nome), nome))

write_xes(traces,  f"output/{nome}_{ts}.xes")   # Disco / PM4Py
write_csv(traces,  f"output/{nome}_{ts}.csv")   # Disco / PM4Py
write_html(traces, f"output/{nome}_{ts}.html")  # dashboard browser
```

---

### Etapa 5 — Serialização XES (`xes/writer.py`)

Produz um arquivo XML conforme **IEEE XES 1.0** com:

- **Extensões declaradas:** `concept`, `time`, `lifecycle`, `org`
- **Globals:** valores padrão para atributos ausentes (ex: `lifecycle:transition = "complete"`)
- **Classifiers:** dois classificadores — `Activity` (por `concept:name`) e `Resource` (por `org:resource`)
- **Normalização de datas:** formato Datajud `"YYYYMMDDHHmmss"` → ISO 8601 com timezone UTC (`"2024-01-10T14:32:00+00:00"`)

O arquivo XES resultante é importável diretamente no Disco, ProM, Celonis, Apromore e PM4Py sem pré-processamento adicional.

---

### Etapa 6 — Serialização Tabular (`tabular/writer.py`)

Produz um **event log plano**: uma linha por evento, com atributos do caso repetidos em cada linha do mesmo processo.

**Ordem das colunas:**
1. `case:concept:name` — identificador do processo (sempre primeiro)
2. Demais atributos do caso (`case:tribunal`, `case:classe`, `case:data_ajuizamento`, etc.)
3. `concept:name` — nome da atividade
4. `time:timestamp` — timestamp do evento
5. `lifecycle:transition`, `org:resource`
6. Atributos extras do evento (`event:codigo_tpu`, etc.)

O CSV usa **UTF-8 com BOM** para compatibilidade com Excel no Windows. O XLSX inclui linha de cabeçalho em negrito com fundo escuro, primeira linha congelada e colunas com largura automática.

---

### Etapa 7 — Dashboard HTML (`dashboard/writer.py`)

Gera um arquivo HTML **completamente auto-contido** (sem servidor necessário). Todas as estatísticas são pré-computadas em Python por `_compute_stats()`:

| Componente | O que mostra |
|-----------|-------------|
| KPI cards | Total de processos, eventos, atividades distintas, duração média |
| DFG interativo | Grafo de fluxo com vis.js — frequência de transições, layout ajustável, slider de filtro |
| Top atividades | Gráfico de barras horizontal (Chart.js) — 25 atividades mais frequentes |
| Eventos por mês | Gráfico de linha com volume de eventos ao longo do tempo |
| Histograma de duração | Distribuição do tempo total de tramitação (buckets de 30 dias) |
| Tabela de eventos | Primeiros 1.000 eventos — pesquisável, com ordenação por coluna |

Para visualizar: abra o arquivo `.html` em qualquer browser. Não requer conexão com internet após gerado (bibliotecas JS são carregadas por CDN apenas uma vez).

---

## 5. Pipeline de Análises — Passo a Passo

Após a extração, execute todas as análises com:

```bash
source .venv/bin/activate
python run_pipeline.py
```

Parâmetros opcionais:

```bash
# Analisar apenas uma classe processual
python run_pipeline.py --classe "Procedimento Comum Cível"

# Restringir a uma janela temporal
python run_pipeline.py --data-inicio 2015-01-01 --data-fim 2020-12-31

# Analisar apenas um tribunal
python run_pipeline.py --tribunal TJPR
```

O pipeline executa 4 etapas em sequência. Uma falha em uma etapa não interrompe as seguintes — o resultado parcial é preservado.

---

### Etapa 1 — Exportar Log Filtrado por Classe (`exportar_filtrado.py`)

**O que faz:** Carrega o XES mais recente de cada tribunal, filtra os processos da classe especificada, e exporta em 3 formatos prontos para importação no Disco.

**Por que filtrar por classe?** Classes processuais diferentes têm fluxos completamente distintos. Misturar "Procedimento Comum Cível" com "Execução Fiscal" em um mesmo DFG gera um modelo fragmentado e sem interpretação prática. Esta etapa cria subconjuntos limpos por classe.

**Saída:**
```
output/TJPR_Procedimento_Comum_Civel_20260101.xes
output/TJPR_Procedimento_Comum_Civel_20260101.csv
```

---

### Etapa 2 — Comparação Cross-Tribunal

> **Não implementado:** `comparar_pcc.py` não existe no projeto atual.
> Para comparação cross-tribunal, use o Disco com dois XES separados ou o notebook Jupyter.

---

### Etapa 3 — Análise de Happy Path (`happy_path_report.py`)

**O que faz:** Classifica cada processo em um dos 4 níveis de conformidade com o rito ordinário do CPC 2015 (arts. 319–512).

#### Definição de Happy Path — CPC 2015, Procedimento Comum Cível

```
Petição inicial
    → Distribuição / Recebimento
    → Audiência de conciliação/mediação (art. 334 CPC)
    → Citação → Contestação
    → Saneamento e organização do processo (art. 357 CPC)
    → Instrução (perícia / audiência de instrução)
    → Sentença de mérito (Procedência / Improcedência / Procedência em Parte)
    → Trânsito em julgado
    → Baixa Definitiva
```

#### Desvios que excluem do happy path

| Categoria | Movimentos TPU |
|-----------|---------------|
| Recursal | Remessa em grau de recurso, Recurso Especial repetitivo |
| Administrativo | Redistribuição, Reativação, Desarquivamento, Cancelamento de Distribuição |
| Sobrestamento | Suspensão/Sobrestamento por IRDR, REsp Repetitivo |

#### Os 4 níveis de classificação

| Nível | Label | Critério |
|-------|-------|---------|
| **1** | `ideal` | Atividade terminal de mérito + sem desvio recursal + sem desvio administrativo |
| **2** | `concluído` | Atividade terminal de mérito + sem desvio recursal (desvio admin permitido) |
| **3** | `baixa` | Possui "Baixa Definitiva" (qualquer caminho) |
| **0** | `em andamento` | Sem atividade terminal, ou com recurso |

#### Janela temporal para comparabilidade

Para comparar TJPR × TJRS é obrigatório usar a **mesma janela temporal** e incluir apenas processos que **iniciaram E encerraram** dentro da janela (usando `filtrar_janela()`).

```bash
# Verificar cobertura antes de re-extrair
python analises/happy_path_report.py \
    --classe "Procedimento Comum Cível" \
    --data-inicio 2015-01-01 \
    --data-fim 2020-12-31
```

**Saída (4 arquivos):**

| Arquivo | Conteúdo |
|---------|---------|
| `*_happy_path.csv` | 1 linha/processo: metadados + variante completa + nível + duração (dias) |
| `*_happy_path.xlsx` | Igual ao CSV, com linhas verdes = Nível 1 (Ideal) |
| `*_happy_path_transicoes.csv` | 1 linha/transição A→B: timestamps + dias de espera + flag recurso |
| `*_happy_path.xes` | Log XES com apenas os processos happy path — importar direto no Disco |

---

### Etapa 4 — Análise PM4Py Completa (`analisar.py`)

**O que faz:** Executa 8 estágios de análise sobre um único arquivo XES, gerando até 10 visualizações em PNG.

| Estágio | Análise | Saída |
|---------|---------|-------|
| 1 | Descoberta: DFG (frequência e performance), Petri Net (Inductive Miner), BPMN | `dfg_frequencia.png`, `dfg_performance.png`, `petri_net.png`, `bpmn.png` |
| 2 | Variantes: Pareto das top 30 variantes + linha de 80% cumulativo | `variantes_pareto.png` |
| 3 | Temporal: throughput + sojourn (15 atividades mais lentas) + bottlenecks (10 transições) | `throughput_time.png`, `sojourn_time.png`, `bottlenecks.png` |
| 4 | Rework: atividades com repetição, top 15 por contagem de loops | `rework.png` |
| 5 | Organizacional: volume por `org:resource` (top 20) + duração mediana por vara | `organizacional.png` |
| 6 | Conformance: token-based replay — histograma de fitness, % abaixo de 0.8 | `conformance_fitness.png` |
| 7 | Comparação: se múltiplos arquivos em `output/`, compara métricas entre tribunais | `comparacao_tribunais.png` |

> **Nota:** DFG, Petri Net e BPMN requerem `graphviz` instalado (`brew install graphviz`). As demais análises funcionam sem ele.

---

## 6. Estrutura do Event Log

O event log segue o padrão **IEEE XES 1.0** com a hierarquia:

```
LOG
├── TRACE (processo judicial)
│   ├── Atributos do caso: concept:name, case:tribunal, case:classe, ...
│   └── EVENTOS (movimentos processuais, em ordem cronológica)
│       ├── concept:name, time:timestamp, lifecycle:transition
│       ├── org:resource, event:codigo_tpu
│       └── ...
├── TRACE
└── ...
```

### Atributos do Caso (`case:*`)

Os atributos do caso descrevem o **processo como um todo** e são repetidos em cada linha do CSV/XLSX.

---

#### `case:concept:name`
**Origem:** campo `numeroProcesso` da API
**Exemplo:** `"0000001-11.2024.8.16.0001"`

O identificador único do processo. É o campo-chave que une todos os eventos de um mesmo caso. No padrão IEEE XES, este campo é obrigatório (`concept:name` do trace). Todas as ferramentas de Process Mining (PM4Py, Disco, ProM) usam este campo para agrupar eventos por processo.

---

#### `case:tribunal`
**Origem:** campo `tribunal` da API
**Exemplo:** `"TJPR"`, `"TJRS"`

Identifica o tribunal de origem. Permite benchmarking direto entre tribunais para a mesma classe processual — o campo habilitador das análises comparativas deste dataset.

---

#### `case:classe`
**Origem:** `classe.nome`
**Exemplo:** `"Procedimento Comum Cível"`, `"Execução Fiscal"`

O tipo processual. **Esta é a variável de segmentação mais crítica do dataset.** Classes diferentes têm fluxos normativos completamente distintos — misturá-las em um mesmo DFG produz um modelo sem interpretação prática.

> **Regra:** sempre filtre ou segmente por `case:classe` antes de gerar qualquer modelo de processo.

---

#### `case:assunto_principal`
**Origem:** `assuntos[0].nome`
**Exemplo:** `"Danos Morais"`, `"IPTU"`, `"Alimentos"`

O tema jurídico principal do processo. Permite segmentação dentro de uma mesma classe. Por exemplo, dentro de "Procedimento Comum Cível", processos de danos morais podem ter comportamento diferente de processos de divórcio litigioso.

Útil para **decision mining**: descobrir quais atributos do processo explicam escolhas como "vai a recurso?" ou "encerra por acordo?".

---

#### `case:orgao_julgador`
**Origem:** `orgaoJulgador.nome`
**Exemplo:** `"1ª Vara Cível de Curitiba"`

A vara ou câmara responsável pelo processo. Diferente de `org:resource` (que pode mudar evento a evento em caso de redistribuição), este campo representa o órgão principal do processo. Permite análise de carga de trabalho e comparação de performance entre varas.

---

#### `case:data_ajuizamento`
**Origem:** `dataAjuizamento` (formato `"YYYYMMDDHHmmss"` → ISO 8601)
**Exemplo:** `"2024-01-10T00:00:00+00:00"`

A data de abertura do processo. Combinado com o timestamp do último evento, permite calcular o **tempo total de tramitação** — o KPI mais fundamental para avaliação de eficiência judicial e comparação com metas CNJ.

---

#### `case:grau`
**Origem:** campo `grau`
**Exemplo:** `"G1"` (primeiro grau), `"G2"` (segundo grau)

A instância processual. G1 = varas de primeiro grau; G2 = câmaras/turmas recursais. Processos em instâncias diferentes têm atores, atividades e tempos completamente distintos. Misturá-los é equivalente a misturar classes processuais.

---

#### `case:nivel_sigilo`
**Origem:** campo `nivelSigilo`
**Exemplo:** `0` (público), `1–5` (progressivamente mais sigiloso)

Indica se o processo é sigiloso. Processos com sigilo podem ter movimentos omitidos na API pública, distorcendo métricas de duração e completude. **Recomenda-se excluir `case:nivel_sigilo > 0`** em análises de performance.

---

### Atributos do Evento

Os atributos do evento descrevem **cada movimento processual individualmente**.

---

#### `concept:name`
**Origem:** `movimentos[].nome` + `movimentos[].complementosTabelados[0].nome`
**Exemplo:** `"Juntada de Petição - Contestação"`, `"Distribuição"`, `"Sentença"`

O nome da atividade — o campo central de qualquer análise de processo. Construído combinando o nome do movimento com o complemento tabular, gerando granularidade suficiente para distinguir `"Juntada - Contestação"` de `"Juntada - Recurso"` no DFG.

---

#### `time:timestamp`
**Origem:** `movimentos[].dataHora` (ISO 8601 com timezone UTC)
**Exemplo:** `"2024-01-10T14:32:00+00:00"`

Quando o evento ocorreu. Habilita toda a **perspectiva temporal** do Process Mining: throughput time, sojourn time, bottlenecks, SLA compliance e análise de sazonalidade.

---

#### `lifecycle:transition`
**Origem:** fixo `"complete"`

Estado do evento no ciclo de vida IEEE XES. Todos os movimentos do Datajud são eventos já concluídos, portanto este campo é sempre `"complete"`. É obrigatório pelo padrão XES.

---

#### `org:resource`
**Origem:** `movimentos[].orgaoJulgador.nome` (fallback: `orgaoJulgador` do processo)
**Exemplo:** `"1ª Vara Cível de Curitiba"`, `"3ª Câmara Cível"`

O órgão responsável por aquele movimento específico. Pode mudar ao longo do processo (ex: redistribuição de vara, recurso para câmara). Habilita a **perspectiva organizacional**: análise de carga de trabalho, handover of work, comparação de performance entre varas.

---

#### `event:codigo_tpu`
**Origem:** `movimentos[].codigo`
**Exemplo:** `26` (Distribuição), `11009` (Juntada de Petição)

O código numérico padronizado da **Tabela Processual Unificada (TPU)** do CNJ. É o identificador oficial e inequívoco de cada tipo de movimento — independente de variações textuais entre tribunais. Por exemplo, "Distribuição" no TJPR e "Ato de Distribuição" no TJRS terão o mesmo código TPU.

Usos:
- **Deduplicação** interna de eventos
- **Normalização** para análises comparativas cross-tribunal
- **Joins** com a tabela oficial TPU do CNJ para enriquecer metadados

---

## 7. Módulos de Análise — O que Cada Script Faz

### `analises/exportar_filtrado.py`

**Propósito:** Filtrar o event log completo por classe processual e exportar em formato compatível com Disco.

**Fluxo interno:**
1. Encontra o XES mais recente em `output/` para cada tribunal (`glob` por padrão)
2. Carrega via `pm4py.read_xes()` e corrige prefixos duplicados `"case:case:"` que o PM4Py às vezes insere
3. Filtra traces onde `case:classe == classe_especificada`
4. Exporta XES, CSV e XLSX com nome `{TRIBUNAL}_{slug_classe}_{timestamp}`

**Uso:**
```bash
python analises/exportar_filtrado.py \
    --classe "Procedimento Comum Cível" \
    --tribunal TJPR  # omitir para processar todos os tribunais
```

---

### `analises/happy_path_report.py`

**Propósito:** Identificar e classificar processos que seguiram o rito ordinário completo, medir conformidade e exportar transições detalhadas.

**Fluxo interno:**
1. Carrega o log filtrado por classe (ou filtra diretamente do XES completo)
2. `filtrar_janela(df, inicio, fim)`: mantém apenas processos onde o **primeiro evento ≥ data_inicio** e o **último evento ≤ data_fim** — garantindo que o processo iniciou E encerrou dentro da janela
3. `classificar_processos(df)`: para cada processo, verifica presença de atividades terminais, recursais e administrativas → atribui nível 0–3
4. `calcular_transicoes(df, casos_hp)`: para os processos happy path, calcula cada transição A→B com timestamps e dias de espera
5. Exporta 4 arquivos (CSV, XLSX com destaque visual, CSV de transições, XES filtrado)

**Uso:**
```bash
python analises/happy_path_report.py \
    --classe "Procedimento Comum Cível" \
    --data-inicio 2015-01-01 \
    --data-fim 2020-12-31 \
    --tribunal TJPR
```

---

### `analises/comparar_pcc.py`

> **Não implementado:** script removido. Comparação cross-tribunal disponível via Disco ou notebook.

---

### `analises/analisar.py`

**Propósito:** Análise PM4Py completa de um único arquivo XES, com todos os 8 estágios do manifesto IEEE.

**Uso:**
```bash
python analises/analisar.py output/TJPR_20260101_120000.xes
```

Se nenhum arquivo for passado, usa o XES mais recente em `output/`.

**Checagem de Graphviz:** antes dos estágios que dependem de `dot` (DFG, Petri Net, BPMN), verifica se o executável está disponível. Se não estiver, pula esses estágios com aviso e continua com os demais.

---

### `analises/pm4py_analises.ipynb`

**Propósito:** Notebook Jupyter interativo para análise exploratória, adaptação de parâmetros e visualização inline.

**Estrutura das 32 células:**

| Seção | Células | Conteúdo |
|-------|---------|---------|
| 0 — Carregamento | 1–3 | Localiza XES mais recente, carrega, corrige prefixos |
| 1 — Discovery | 4–7 | DFG frequência + performance, Petri Net, BPMN |
| 2 — Variantes | 8–9 | Pareto, tabela top 15 variantes |
| 3 — Temporal | 10–13 | Throughput + boxplot por ano, sojourn top 15, bottlenecks |
| 4 — Rework | 14–15 | Self-loops, forward-loops, top atividades com repetição |
| 5 — Organizacional | 16–18 | Volume por vara, duração mediana por vara |
| 6 — Conformance | 19–21 | Token replay fitness, diagnóstico por processo |
| 7 — Filtros | 22–25 | Exemplos PM4Py: filtro temporal, atributos, performance |
| 8 — Comparação | 26–32 | Carrega todos os XES, compara métricas lado a lado |

**Iniciar o notebook:**
```bash
source .venv/bin/activate
pip install jupyter  # se ainda não instalado
jupyter notebook analises/pm4py_analises.ipynb
```

---

## 8. Técnicas de Process Mining Implementadas

Esta plataforma implementa as três categorias e quatro perspectivas do **IEEE Process Mining Manifesto (Van der Aalst et al., 2012)**.

```
                          EVENT LOG
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
         DESCOBERTA       CONFORMIDADE      MELHORIA
         (Discovery)     (Conformance)   (Enhancement)
               │               │               │
        "Qual é o         "O real bate    "Onde e como
        fluxo real?"     com o modelo?"   melhorar?"
```

---

### Tipo 1 — Descoberta de Processo (*Process Discovery*)

**Pergunta central:** Qual é o fluxo real dos processos judiciais, sem suposições prévias?

**Campos necessários:** `case:concept:name`, `concept:name`, `time:timestamp`

O algoritmo lê as sequências de eventos e constrói automaticamente um modelo que representa o comportamento observado nos dados.

#### Algoritmos implementados

| Algoritmo | Quando usar | Característica chave |
|-----------|-------------|---------------------|
| **DFG (Directly Follows Graph)** | Exploração inicial; análise visual rápida | Mostra frequência e performance de todas as transições observadas |
| **Inductive Miner** | Primeira modelagem formal; dados ruidosos | Sempre gera Petri Net válida; `noise_threshold` controla tolerância a desvios raros |
| **BPMN** | Apresentação para stakeholders | Mais legível que Petri Net para audiência não técnica |
| **Alpha Miner** | Fins acadêmicos | Sensível a ruído; não recomendado para dados Datajud reais |

**Código PM4Py (implementado em `analisar.py` e notebook):**
```python
import pm4py

log = pm4py.read_xes("output/TJPR_20260101_120000.xes")

# Filtrar por classe antes — obrigatório
log_civel = pm4py.filter_trace_attribute_values(
    log, "case:classe", ["Procedimento Comum Cível"], retain=True
)

# DFG de frequência
dfg, sa, ea = pm4py.discover_dfg(log_civel)
pm4py.save_vis_dfg(dfg, sa, ea, "dfg_frequencia.png")

# DFG de performance (tempo médio entre atividades)
dfg_perf, sa, ea = pm4py.discover_performance_dfg(log_civel)
pm4py.save_vis_performance_dfg(dfg_perf, sa, ea, "dfg_performance.png")

# Petri Net via Inductive Miner
# noise_threshold=0.2 ignora variantes que ocorrem em < 20% dos casos
net, im, fm = pm4py.discover_petri_net_inductive(log_civel, noise_threshold=0.2)
pm4py.save_vis_petri_net(net, im, fm, "petri_net.png")

# BPMN
bpmn = pm4py.discover_bpmn_inductive(log_civel)
pm4py.save_vis_bpmn(bpmn, "bpmn.png")
```

**Insights esperados:**
- O fluxo real corresponde ao rito normativo do CPC?
- Onde o processo se bifurca (recursos, extinções, mediações)?
- Existem atividades que ocorrem fora da ordem esperada (ex: sentença antes da instrução)?
- Quais são os "atalhos" mais frequentes?

---

### Tipo 2 — Verificação de Conformidade (*Conformance Checking*)

**Pergunta central:** O que aconteceu na prática está de acordo com o que deveria acontecer?

**Campos necessários:** `concept:name`, `time:timestamp`, mais o modelo normativo de referência

Requer um modelo formal (Petri Net) como referência. Pode ser descoberto dos dados ou definido manualmente com base no CPC 2015.

#### Técnicas implementadas

| Técnica | O que detecta | Métrica |
|---------|--------------|---------|
| **Token-based replay** | Etapas puladas (missing tokens) e atividades extras (remaining tokens) | Fitness: 0.0 (completamente desconforme) a 1.0 (perfeito) |
| **Alignments** | O menor conjunto de desvios entre modelo e trace real | Custo de alinhamento (menor = mais conforme) |

**Código PM4Py:**
```python
# Token-based replay — fitness geral
fitness = pm4py.fitness_token_based_replay(log_civel, net, im, fm)
print(f"Fitness médio: {fitness['average_trace_fitness']:.2%}")
print(f"Traces perfeitamente conformes: {fitness['percentage_of_fitting_traces']:.2%}")

# Diagnóstico por processo
diagnostics = pm4py.conformance_diagnostics_token_based_replay(log_civel, net, im, fm)
deviantes = [d for d in diagnostics if d["trace_fitness"] < 0.8]
print(f"{len(deviantes)} processos com fitness < 80%")
```

**Interpretação do fitness:**
- **1.0** — O trace reproduz o modelo sem nenhum desvio
- **0.8–1.0** — Desvios menores; processo substancialmente conforme
- **< 0.8** — Desvios significativos; processo candidato a investigação
- **< 0.5** — Desvios graves; possível subregistro ou erro de lançamento

**Insights esperados:**
- Qual percentual dos processos respeita o fluxo normativo da classe?
- Quais atividades são mais frequentemente puladas?
- Processos sigilosos (`case:nivel_sigilo > 0`) apresentam mais desvios por subregistro?
- Há varas com padrão sistemático de desvio?

---

### Tipo 3 — Melhoria de Processo (*Process Enhancement*)

**Pergunta central:** Com os dados reais, onde e como melhorar o processo?

Implementado em quatro perspectivas:

---

#### Perspectiva de Controle de Fluxo

*Quais atividades ocorrem e em qual ordem?*

**Análise de variantes:**
```python
variants = pm4py.get_variants(log_civel)
# Ordena por frequência decrescente
top_variants = sorted(variants.items(), key=lambda x: -len(x[1]))

# As top 5 variantes tipicamente cobrem 70–80% dos processos
cumulative = 0
for variant, cases in top_variants[:10]:
    pct = len(cases) / len(log_civel) * 100
    cumulative += pct
    print(f"{pct:.1f}% ({cumulative:.1f}% acumulado) — {variant[:80]}...")
```

**Detecção de rework (loops):**

| Tipo de loop | Exemplo | Interpretação |
|-------------|---------|--------------|
| Self-loop | Conclusão → Conclusão | Remessa redundante ao magistrado |
| Forward-loop | Conclusão → Despacho → Conclusão | Magistrado devolve sem resolver; múltiplos despachos protelatórios |
| Loop de citação | Juntada de Citação × N | Dificuldade em localizar a parte |
| Loop de expedição | Expedição de Mandado → Cumprimento tentado → Expedição | Tentativas frustradas de cumprimento |

---

#### Perspectiva Temporal

*Quando as atividades ocorrem e quanto tempo levam?*

**Throughput time (tempo total de tramitação):**
```python
# Tempo do primeiro ao último evento de cada processo
from pm4py.statistics.traces.generic.log import case_statistics

stats = case_statistics.get_kde_caseduration(log_civel, parameters={})
median_days = stats["median"] / 86400
p90_days = stats["p90"] / 86400
print(f"Mediana: {median_days:.0f} dias | P90: {p90_days:.0f} dias")
```

**Sojourn time (tempo de espera por atividade):**
```python
from pm4py.statistics.sojourn_time.log import get as sojourn_time

# Tempo médio entre um evento e o próximo (tempo que o processo "fica" naquela atividade)
sojourn = sojourn_time.apply(log_civel)
for activity, stats in sorted(sojourn.items(), key=lambda x: -x[1]["mean"]):
    print(f"{activity}: {stats['mean']/86400:.1f} dias (média) | {stats['median']/86400:.1f} dias (mediana)")
```

**Bottlenecks (transições mais lentas):**
```python
# Tempo médio da transição A→B
from pm4py.statistics.eventually_follows.log import get as ef_stats

# Ou via DFG de performance
dfg_perf, sa, ea = pm4py.discover_performance_dfg(log_civel)
bottlenecks = sorted(dfg_perf.items(), key=lambda x: -x[1])[:10]
for (a, b), mean_seconds in bottlenecks:
    print(f"{a} → {b}: {mean_seconds/86400:.0f} dias médios")
```

---

#### Perspectiva Organizacional

*Quem faz o quê e como os recursos se relacionam?*

```python
# Volume de eventos por vara
from collections import Counter

resource_counts = Counter(
    event["org:resource"]
    for trace in log_civel
    for event in trace
    if "org:resource" in event
)

for vara, count in resource_counts.most_common(20):
    print(f"{vara}: {count} eventos")

# Duração mediana por vara
from collections import defaultdict
import statistics

duracao_por_vara = defaultdict(list)
for trace in log_civel:
    vara = trace.attributes.get("case:orgao_julgador", "Desconhecido")
    if len(trace) >= 2:
        delta = (trace[-1]["time:timestamp"] - trace[0]["time:timestamp"]).days
        duracao_por_vara[vara].append(delta)

for vara, duracoes in sorted(duracao_por_vara.items(), key=lambda x: -statistics.median(x[1])):
    if len(duracoes) >= 5:  # mínimo de 5 casos para significância
        print(f"{vara}: mediana {statistics.median(duracoes):.0f} dias (n={len(duracoes)})")
```

**Handover of Work:**
```python
from pm4py.algo.organizational_mining.sna import algorithm as sna

hw_values = sna.apply(log_civel, variant=sna.Variants.HANDOVER_LOG)
pm4py.view_sna(hw_values)
```

---

#### Perspectiva do Caso (*Decision Mining*)

*Quais atributos do processo explicam diferentes caminhos no fluxo?*

```python
from pm4py.algo.decision_mining import algorithm as decision_mining

# Treina árvore de decisão para explicar bifurcações no modelo
# Ex: por que alguns processos vão a recurso e outros encerram diretamente?
rules = decision_mining.apply(log_civel, net, im, fm)
```

Atributos mais relevantes para segmentação:
- `case:classe` — o filtro mais básico e necessário
- `case:assunto_principal` — refinamento dentro da classe
- `case:grau` — instância processual
- `case:nivel_sigilo` — qualidade/completude do registro
- `case:tribunal` — benchmarking entre tribunais

---

## 9. Análises Práticas — Perguntas e Respostas

### Mapa do Processo Real — DFG de Frequência

**Pergunta:** Qual é o fluxo real dos processos de Procedimento Comum Cível no TJPR?

**Ferramenta:** Disco → aba Process Map → métrica Frequency

**Procedimento:**
1. Importe o arquivo XES filtrado (gerado por `exportar_filtrado.py`)
2. Em "Process Map", selecione métrica **Frequency**
3. Ajuste os sliders **Activities** e **Paths** — comece com 30% em ambos para ver o happy path
4. Aumente progressivamente para revelar variantes menos frequentes

**Insights esperados:**
- O processo real corresponde ao fluxo CPC 2015?
- Existem "atalhos" — processos que vão de Distribuição direto para Sentença sem audiência?
- Quais atividades ocorrem com frequência inesperada?

---

### Gargalos de Tempo — DFG de Performance

**Pergunta:** Em qual etapa o processo judicial fica parado por mais tempo?

**Ferramenta:** Disco → aba Process Map → métrica Performance

**Procedimento:**
1. Alterne para **Performance** no seletor de métrica
2. Arcos vermelhos/quentes = maior tempo de espera
3. Clique em um arco para ver min/média/max/mediana

**Interpretação dos gargalos:**

| Gargalo observado | Causa possível | Ação sugerida |
|-------------------|---------------|---------------|
| "Conclusão ao Juiz" com média > 30 dias | Sobrecarga do magistrado; acúmulo de processos conclusos | Revisar distribuição de carga; monitorar índice de produtividade |
| "Expedição de Mandado" com média > 60 dias | Gargalo na execução; falta de oficial de justiça | Avaliar citação eletrônica; oficial Ad Hoc |
| "Audiência" com média > 90 dias | Agenda sobrecarregada; pautas longas | Incrementar uso de conciliação pré-processual |
| "Juntada de Citação" com média > 30 dias | Dificuldade em localizar a parte | Priorizar citação eletrônica (art. 246 CPC) |

---

### Análise de Variantes

**Pergunta:** Quais são os caminhos mais comuns e quanta variabilidade existe?

**Ferramenta:** Disco → aba Cases → coluna Variant / PM4Py

**Procedimento no Disco:**
1. Aba **Cases** → ordene por **Variant Count** (decrescente)
2. As top 5 variantes cobrem o comportamento majoritário
3. Clique em uma variante para ver os processos que a seguem

**Interpretação:**

| Padrão observado | Interpretação |
|-----------------|--------------|
| 1 variante cobre > 50% dos casos | Processo bem padronizado — boa conformidade procedimental |
| Top 10 variantes cobrem < 30% | Alta fragmentação — ausência de padronização ou muitos desvios por caso |
| Variante com self-loops dominante | Retrabalho sistêmico — investigar causa raiz |
| Variante curta (2–3 atividades) | Processos extintos precocemente — desistência, indeferimento, incompetência |

---

### Rework e Loops

**Pergunta:** Existe retrabalho sistemático no fluxo judicial?

**Ferramenta:** Disco → Process Map (observe arcos que formam ciclos)

**Exemplos de loops com significado prático:**

| Loop observado | Interpretação | Ação recomendada |
|----------------|--------------|-----------------|
| Conclusão → Despacho → Conclusão (múltiplas vezes) | Magistrado recebe e devolve sem resolver o mérito | Monitorar varas com taxa de despacho/conclusão > 3× |
| Juntada de Citação × N | Parte não localizada; tentativas múltiplas | Priorizar citação eletrônica; contato por WhatsApp judicial |
| Expedição → Cumprimento tentado → Expedição | Mandado não cumprido; tentativas frustradas | Oficial de justiça Ad Hoc; avaliação de fraude de localização |
| Petição → Despacho → Petição (frequente) | Litigância excessiva / partes muito ativas | Candidato para mediação / conciliação judicial |

---

### Performance por Vara

**Pergunta:** Existem varas sistematicamente mais lentas que outras na mesma comarca?

**Ferramenta:** Disco + filtro por `org:resource` + Performance Map / PM4Py

**Procedimento no Disco:**
1. Aba **Cases** → filtro por `org:resource` = vara de interesse
2. Observe o Performance Map filtrado
3. Compare com a média geral do tribunal

**Ação recomendada:** varas com duração mediana acima de 2 desvios padrão da média merecem investigação. Use o DFG da vara isolada para identificar se o gargalo é em uma etapa específica ou distribuído por todo o fluxo.

---

### Comparação entre Tribunais

**Pergunta:** TJPR ou TJRS processa "Procedimento Comum Cível" mais rapidamente? Com o mesmo fluxo?

**Ferramenta:** Disco com dois XES separados ou notebook Jupyter (seção 8 — Comparação)

> **Nota:** `comparar_pcc.py` não existe no projeto atual.

**Pré-condição obrigatória:** ambos os datasets devem usar a mesma janela temporal e conter processos iniciados E encerrados nessa janela. Sem isso, a comparação é inválida.

**Insights esperados:**
- Qual tribunal tem menor throughput time mediano?
- Os DFGs são similares ou há etapas exclusivas de um tribunal?
- O tribunal mais lento tem gargalo pontual ou tempo elevado em todas as etapas?
- Há atividades com tempo de espera muito discrepante entre tribunais (sojourn scatter)?

**Ação recomendada:** use o tribunal mais eficiente como benchmark e proponha alinhamento de boas práticas ao CNJ.

---

### Conformidade com Metas CNJ

**Pergunta:** Qual percentual dos processos respeita o rito normativo e os prazos CNJ?

**Ferramenta:** PM4Py token-based replay (implementado em `analisar.py` e notebook)

**Procedimento:**
```bash
python analises/analisar.py output/TJPR_20260101_120000.xes
# → gera conformance_fitness.png
```

**Interpretação do histograma de fitness:**
- Pico em 1.0 = maioria dos processos segue o rito normativo
- Distribuição bimodal (picos em 0.0 e 1.0) = dois subpopulações distintas (ex: processos com e sem recurso)
- Distribuição uniforme = alta variabilidade; ausência de padronização

---

### Análise de Happy Path

**Pergunta:** Quantos processos completaram o rito ordinário completo (do ajuizamento à baixa definitiva) sem desvios?

**Ferramenta:** `happy_path_report.py`

```bash
python analises/happy_path_report.py \
    --classe "Procedimento Comum Cível" \
    --data-inicio 2015-01-01 \
    --data-fim 2020-12-31
```

**Resultado esperado:**
- % de processos Nível 1 (Ideal): rito completo sem desvios
- % de processos Nível 2 (Concluído): chegaram ao mérito, mas com desvios administrativos
- % de processos Nível 3 (Baixa): apenas baixa definitiva confirmada
- % de processos Nível 0 (Em Andamento): não concluídos dentro da janela

**Arquivo de transições (`*_transicoes.csv`):** permite calcular o tempo médio em cada etapa do happy path — o "tempo ideal" de tramitação de um processo que seguiu o rito normativo completo.

---

## 10. Artefatos de Saída

### Arquivos de extração (`output/`)

| Arquivo | Formato | Para onde exportar |
|---------|---------|-------------------|
| `{TRIBUNAL}_{ts}.xes` | IEEE XES 1.0 XML | Disco, ProM, PM4Py, Celonis, Apromore |
| `{TRIBUNAL}_{ts}.csv` | CSV UTF-8 BOM | Disco, PM4Py, pandas, R, Tableau |
| `{TRIBUNAL}_{ts}.html` | HTML5 auto-contido | Browser (dashboard rápido) |

### Arquivos de análise (`output/`)

| Arquivo | Conteúdo |
|---------|---------|
| `{TRIBUNAL}_{classe}_{ts}.xes` | Log filtrado por classe — Disco/PM4Py |
| `{TRIBUNAL}_{classe}_{ts}.csv` | Log filtrado por classe — Disco/PM4Py |
| `{TRIBUNAL}_{classe}_{ts}_happy_path.csv` | Processos classificados (nível 0–3) + variante + duração |
| `{TRIBUNAL}_{classe}_{ts}_happy_path_transicoes.csv` | Transições A→B: timestamps + dias de espera |
| `{TRIBUNAL}_{classe}_{ts}_happy_path.xes` | Log XES apenas happy path — Disco |

### Visualizações (`analises/imgs/`)

| Arquivo | Análise |
|---------|--------|
| `dfg_frequencia.png` | DFG com contagem de ocorrências por arco |
| `dfg_performance.png` | DFG com tempo médio de espera por arco |
| `petri_net.png` | Petri Net (Inductive Miner) — modelo formal |
| `bpmn.png` | BPMN — modelo legível para stakeholders |
| `variantes_pareto.png` | Pareto das variantes com cobertura cumulativa |
| `throughput_time.png` | Histograma + boxplot do tempo total de tramitação |
| `sojourn_time.png` | Top 15 atividades por tempo de espera |
| `bottlenecks.png` | Top 10 transições A→B mais lentas |
| `rework.png` | Top 15 atividades com maior taxa de repetição |
| `organizacional.png` | Volume + duração mediana por vara |
| `conformance_fitness.png` | Histograma de fitness por processo |
| `comparacao_tribunais.png` | Comparação de métricas entre tribunais |
| `pcc_02_duracao.png` até `pcc_07_*.png` | Série de comparação cross-tribunal |

---

## 11. Customização e Extensibilidade

### Adicionar um novo tribunal

Em `datajud/config.py`, adicione uma entrada em `TRIBUNAIS`:

```python
TRIBUNAIS = {
    "api_publica_tjpr": "TJPR",
    "api_publica_tjrs": "TJRS",
    "api_publica_tjsp": "TJSP",  # ← novo tribunal
}
```

O alias Elasticsearch pode ser encontrado na documentação da API Datajud: https://datajud-wiki.cnj.jus.br

---

### Filtrar por período de ajuizamento

Substitua `QUERY_BODY` em `datajud/config.py`:

```python
QUERY_BODY = {
    "query": {
        "range": {
            "dataAjuizamento": {
                "gte": "20150101000000",   # formato obrigatório: YYYYMMDDHHmmss
                "lte": "20181231235959"
            }
        }
    },
    "sort": [{"dataHoraUltimaAtualizacao": {"order": "asc"}}],
    "_source": True,
}
```

> **Atenção:** o formato de data na query deve ser `YYYYMMDDHHmmss` (14 dígitos sem separadores).

---

### Adicionar campo ao nível do processo

Em `CAMPOS_TRACE` em `datajud/config.py`:

```python
CAMPOS_TRACE = [
    # ... campos existentes ...
    # ("nome_no_xes",        [caminho, json, aninhado],    "tipo_xes"),
    ("case:valor_causa",    ["valorCausa"],               "float"),
    ("case:sistema",        ["sistema", "nome"],          "string"),
    ("case:codigo_classe",  ["classe", "codigo"],         "int"),
]
```

---

### Adicionar campo ao nível do evento

Em `CAMPOS_EVENTO_EXTRAS` em `datajud/config.py`:

```python
CAMPOS_EVENTO_EXTRAS = [
    ("event:codigo_tpu",        ["codigo"],                              "int"),
    # ← novo campo:
    ("event:codigo_complemento", ["complementosTabelados", 0, "codigo"], "int"),
    ("event:complemento_2",     ["complementosTabelados", 1, "nome"],   "string"),
]
```

---

### Filtros Elasticsearch avançados

```python
# Por período + excluindo processos sigilosos
"query": {
    "bool": {
        "must": [
            {"range": {"dataAjuizamento": {"gte": "20150101000000", "lte": "20181231235959"}}}
        ],
        "must_not": [
            {"range": {"nivelSigilo": {"gt": 0}}}
        ]
    }
}

# Por código de classe (não por nome — nome pode variar entre tribunais)
"query": {"term": {"classe.codigo": 7}}   # 7 = Procedimento Comum Cível
```

> **Nota:** filtro por `classe.codigo` nem sempre funciona na API pública.
> Prefira filtrar por classe **após** a extração via `exportar_filtrado.py --classe "..."`.

---

### Enriquecimento com fontes externas

Após a extração, o CSV/XLSX pode ser enriquecido via join antes de reimportar no Disco:

| Fonte | Campo a adicionar | Análise habilitada |
|-------|------------------|--------------------|
| CNJ (Justiça em Números) | Meta de duração por classe | SLA compliance |
| Calendário judicial TJ | Dias úteis entre eventos | Tempo real vs. dias corridos |
| IBGE | Comarca → população / PIB | Carga de trabalho normalizada por habitante |
| Tabela TPU CNJ | Código → categoria do movimento | Agrupamento semântico de atividades |

---

### Campos adicionais recomendados

```python
# Em CAMPOS_TRACE — habilitam analyses adicionais:

# Valor da causa — correlação entre valor e duração ou taxa de recurso
("case:valor_causa",    ["valorCausa"],              "float"),

# Sistema de processamento — PJe lança movimentos de forma diferente do SAJ
("case:sistema",        ["sistema", "nome"],         "string"),

# Código numérico da classe — para joins com tabelas CNJ de metas e prazos
("case:codigo_classe",  ["classe", "codigo"],        "int"),

# Segundo assunto — processos com múltiplos temas jurídicos
("case:assunto_2",      ["assuntos", 1, "nome"],     "string"),
```

---

## 12. Solução de Problemas

| Problema | Causa provável | Solução |
|---------|---------------|---------|
| `HTTP 401 Unauthorized` | API Key expirada ou inválida | Atualizar `API_KEY` em `config.py`. Consultar https://datajud-wiki.cnj.jus.br/api-publica/acesso |
| `HTTP 429 Too Many Requests` | Rate limit atingido | Aumentar `REQUEST_DELAY_SEC` para `1.0` ou mais |
| Arquivo XES sem eventos | Processos sem movimentos registrados | Normal — processos sem eventos são descartados automaticamente |
| DFG muito fragmentado no Disco | Classes processuais misturadas | Filtre por `case:classe` usando `exportar_filtrado.py` antes de importar |
| Tempos negativos ou absurdos | Timestamps fora de ordem no registro original | O pipeline já ordena por `dataHora`; verifique registros com data de lançamento retroativa |
| Disco lento ao abrir o XES | Arquivo grande (> 50k eventos) | Reduzir `MAX_PROCESSOS` em `config.py` ou filtrar por período antes de importar |
| Visualizações DFG/Petri não geradas | Graphviz não instalado | `brew install graphviz` (macOS) ou `apt install graphviz` (Linux) |
| Muitas atividades genéricas no DFG | Complemento não disponível na API | Usar `event:codigo_tpu` para agrupar atividades semanticamente |
| `0%` de happy path na janela escolhida | Processos em andamento na janela | Expandir janela temporal ou re-extrair com filtro de `dataAjuizamento` específico |
| Prefixo `case:case:` duplicado | Bug do PM4Py ao ler XES | Já tratado automaticamente em `exportar_filtrado.py` e no notebook |
| Comparação TJPR × TJRS inválida | Janelas temporais diferentes | Garantir mesma `--data-inicio` e `--data-fim` para ambos os tribunais |
| Processos com 1 único evento | Deduplicação removeu duplicatas | Verificar se o processo realmente tem apenas 1 movimento na origem via API direta |

---

*Documentação gerada a partir da análise completa do código-fonte. Para contribuições ou correções, edite este arquivo e abra um PR.*
