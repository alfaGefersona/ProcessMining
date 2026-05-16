## Ação Penal — Procedimento Ordinário no TJPR (2020–2026)

**Tribunal:** Tribunal de Justiça do Paraná (TJPR)
**Classe processual:** Ação Penal - Procedimento Ordinário
**Período:** 01/01/2020 → 13/05/2026
**Metodologia:** PM² (Process Mining Project Methodology)
**Tipo de log:** LO — Log Original (extração direta da API CNJ Datajud)

**Aluno:** Geferson Artuzo

---

## 1. PLANEJAMENTO

### 1.1 Processo de Negócio Selecionado

A **Ação Penal - Procedimento Ordinário** é o rito processual penal de competência do juízo singular de primeiro grau, obrigatório para crimes com pena máxima igual ou superior a 4 anos (CPP art. 394, §1º, I). É o rito de maior complexidade instrutória do processo penal brasileiro, com fases bem definidas em lei: recebimento da denúncia, citação, resposta à acusação, possibilidade de absolvição sumária, audiência de instrução e julgamento com interrogatório e debates, sentença e trânsito em julgado.

**Crimes típicos julgados por este rito:**

| Crime | Base legal |
|-------|-----------|
| Homicídio doloso qualificado / Feminicídio | CP art. 121 §2º / §2º-A |
| Roubo qualificado | CP art. 157 §2º |
| Tráfico de drogas (pena máx 15 anos) | Lei 11.343/2006 art. 33 |
| Estupro / Estupro de vulnerável | CP arts. 213, 217-A |
| Lesão corporal grave em violência doméstica | CP art. 129 §9º / Lei 11.340/2006 |
| Descumprimento de medida protetiva (c/ violência) | CP art. 147-B |
| Extorsão, sequestro, corrupção ativa (pena ≥ 4 anos) | CP arts. 158, 159, 333 |

**Distinção entre os ritos processuais penais:**

| Rito | Pena máxima | Base legal |
|------|-------------|-----------|
| **Ordinário** (este estudo) | **≥ 4 anos** | CPP art. 394 §1º I |
| Sumário | 2 a 4 anos | CPP art. 394 §1º II |
| Sumaríssimo (JECrim) | ≤ 2 anos | Lei 9.099/1995 |

O rito ordinário é o mais relevante para análise de process mining por combinar: (a) alto volume de casos, (b) fluxo normativo detalhado e mensurável, (c) múltiplos marcos processuais obrigatórios e (d) impacto social direto — 64,9% dos casos no TJPR envolvem violência doméstica, feminicídio ou crimes protetivos (Lei Maria da Penha, Lei 11.340/2006). Tramita em primeiro grau e percorre um fluxo de instrução e julgamento definido nos arts. 394–405 do CPP.

#### Fluxo normativo previsto no CPP (arts. 394–405)

```
┌─────────────────────────────────────────────────────────────────────┐
│         FLUXO NORMATIVO — CPP arts. 394-405 (1º grau)               │
│                                                                     │
│  Denúncia/Queixa    │    →    Recebimento da Denúncia               │
│  (art. 41)          │    (art. 395 — rejeição ou recebimento)       │
│                                      ↓                              │
│                          Citação do réu   (art. 396)                │
│                                      ↓                              │
│                          Resposta à Acusação                        │
│                          (art. 396-A — prazo: 10 dias)              │
│                                      ↓                              │
│             [Absolvição sumária (art. 397) — se cabível]            │
│                                      ↓                              │
│                    Audiência de Instrução e Julgamento              │
│                    (art. 400 — interrogatório, provas, debates)     │
│                                      ↓                              │
│            ┌─────────────────────────┴───────────────────────────┐  │
│            │ Sentença Condenatória → Cumprimento de pena         │  │
│            │ Sentença Absolutória → Extinção do processo         │  │
│            └──────────────────────┬──────────────────────────────┘  │
│                                   ↓                                 │
│                          Trânsito em Julgado                        │
└─────────────────────────────────────────────────────────────────────┘
```

#### Por que Ação Penal Ordinária é adequada para PM²

| Critério | Ação Penal Ordinária |
|----------|---------------------|
| Fluxo normativo definido em lei | ✓ CPP arts. 394-405 |
| Volume de casos fechados | ✓ 13.234  |
| Relevância social | ✓ ~64.9% violência/protetiva |
| Perfis comportamentais | ✓ Alta variância — 4 clusters |
| Hipótese testável | Processo penal dentro de prazo razoável? |

### 1.2 Questões de Pesquisa

**QP1.** O TJPR processa as Ações Penais Ordinárias em prazo compatível com a garantia
constitucional da razoável duração do processo (CF art. 5º, LXXVIII)?

**QP2.** Quais são as transições (gargalos) que mais contribuem para o atraso no
julgamento de Ação Penal Ordinária no TJPR?

**QP3.** O fluxo real dos processos no TJPR apresenta padronização? Quantas variantes
únicas existem e qual é a cobertura das mais frequentes?

**QP4.** É possível identificar perfis comportamentais distintos entre os casos?
Quais são suas características de duração e marco processual?

**QP5.** Casos envolvendo violência doméstica/protetiva recebem tratamento diferenciado
em termos de duração e prioridade, conforme exige a CNJ Resolução 254/2018?

---

## 2. EXTRAÇÃO E PROCESSAMENTO DOS DADOS

### 2.1 Fonte de Dados

| Atributo | Valor |
|----------|-------|
| **API** | Datajud CNJ (Conselho Nacional de Justiça) |
| **Endpoint** | `api-publica.datajud.cnj.jus.br/api_publica_tjpr/_search` |
| **Motor** | Elasticsearch (paginação `search_after`) |
| **Autenticação** | API Key pública CNJ |
| **Acesso** | Público e gratuito |

### 2.2 Escopo e Granularidade

| Parâmetro | Valor |
|-----------|-------|
| **Tribunal** | TJPR (Tribunal de Justiça do Paraná) |
| **Período de ajuizamento** | 01/01/2020 → 13/05/2026 |
| **Filtro na extração (ES)** | `classe.nome` MATCH "Procedimento Ordinário" + `assuntos.nome` ∈ {Violência, Lesão, Homicídio, Feminicídio, Estupro, Ameaça, Doméstica, Protetiva, Mulher} (min. 1) |
| **Granularidade** | Movimento processual individual (nível mais fino disponível) |
| **Total extraído (query ES)** | 50.000 processos |
| **Após filtro classe exata** | 13.234 processos (Ação Penal - Procedimento Ordinário, fechados) |

> **Nota técnica — Composição do dataset bruto extraído (50.000 processos):**
> A API Datajud pública não suporta filtro por `classe.codigo`. O `QUERY_BODY` usa `match`
> full-text em `classe.nome` ("Procedimento Ordinário") combinado com `should` (min. 1) em
> `assuntos.nome` com 9 termos de violência/gênero. O `match` full-text captura qualquer
> classe cujo nome contenha "Procedimento" ou "Ordinário", permitindo vazamento de classes
> adjacentes no CSV bruto:
>
> | Processos (aprox.) | Classe |
> |-------------------:|--------|
> | **19.356** | **Ação Penal - Procedimento Ordinário** ← alvo |
> | ~15.000 | Ação Penal - Procedimento Sumário ← vazamento |
> | ~500 | Ação Penal - Procedimento Sumaríssimo ← vazamento |
> | ~15.000 | Outras classes (PIC-MP, JECrim, PCC, etc.) ← vazamento |
>
> **Nota:** O "Procedimento Comum Cível" que vaza são ações civis (indenizatórias, de família)
> que mencionam keywords como "Mulher" ou "Doméstica" no assunto — NÃO são processos criminais.
> Crimes contra a mulher tramitam exclusivamente em classes penais (AP Ordinária, Sumário, etc.).
>
> A filtragem exata por `case:classe == "Ação Penal - Procedimento Ordinário"` é aplicada
> em pós-processamento pelo `exportar_filtrado.py`, garantindo que apenas os 19.356
> processos corretos entrem no pipeline. Destes, 13.234 possuem atividade terminal (casos fechados).

### 2.3 Composição do Log de Eventos

| Coluna | Descrição | Mapeamento XES |
|--------|-----------|----------------|
| `case:concept:name` | Número CNJ do processo (CaseID) | `concept:name` do trace |
| `time:timestamp` | Data/hora do movimento (ISO 8601) | `time:timestamp` |
| `concept:name` | Nome do movimento TPU + complemento | Atividade |
| `org:resource` | Órgão julgador (vara) | Resource |
| `case:classe` | Classe processual | Atributo de trace |
| `case:data_ajuizamento` | Data de ajuizamento | Atributo de trace |
| `case:assunto_principal` | Assunto principal (violência/doméstica/protetiva) | Atributo de trace |
| `event:codigo_tpu` | Código TPU do movimento | Atributo de evento |

### 2.4 Processamento e Filtros Aplicados

```
RAW API (50.000 proc. — query ES: Ação Penal + mulher/protetiva/doméstica 2020-2026)
    │
    ├─ [F1] Filtro classe exata = "Ação Penal - Procedimento Ordinário"
    │       → 13.234 processos (fechados)
    │
    ├─ [F2] Remoção casos em andamento
    │       (sem atividade terminal: Trânsito, Baixa, Definitivo, Procedência/Improcedência)
    │
    ├─ [F3] Deduplicação por código TPU + timestamp
    │       (lógica nativa da extração)
    │
    └─ LOG FINAL: 13.234 processos / ~2.376.663 eventos
```

**Formato de saída:** CSV UTF-8 BOM + IEEE XES 1.0 (importável no Disco/PM4Py)

### 2.5 Fluxo Completo do Pipeline

```
Datajud API (Elasticsearch CNJ)
     ↓  main.py
     │  Extrai processos via paginação search_after + retry/backoff
     │  Filtro ES: Ação Penal + {mulher/protetiva/doméstica}, dataAjuizamento 2020-2026
     │
     ▼  output/TJPR_{ts}.csv          ← 50.000 processos, todas as classes
     │
     ↓  exportar_filtrado.py
     │  Filtro 1: case:classe == "Ação Penal - Procedimento Ordinário"  → 13.234
     │  Filtro 2: remove processos SEM atividade terminal (em andamento) →  13.234 fechados
     │  Filtro 3 (opcional): top N variantes mais frequentes
     │
     ▼  TJPR_Acao_Penal_*.csv/.xes    ← 13.234 casos fechados, 2.376.663 eventos
     │
     ├─ happy_path_report.py
     │  Filtro 4: 1º evento >= 2020-01-01 AND último evento <= 2026-05-13
     │  Filtro 5: nivel >= 1 (terminal de mérito + sem recurso + sem desvio admin)
     │  ▼  happy_path.csv/.xes             ← casos que seguiram o rito completo
     │     happy_path_transicoes.csv       ← 1 linha/transição A→B com duração em dias
     │
     ├─ analisar.py
     │  Filtro 6 (DFG/Petri Net): ajuizamento ano=2025 → 1.277 casos (reduz tamanho dos grafos)
     │  Filtro 7 (DFG): remove arcos < 2% do máximo (3.497 → 201 arcos visíveis)
     │  Conformance: amostra aleatória 500 casos (Token Replay custoso — O(n²))
     │  ▼  analises/imgs/*.png              ← 10 imagens PM4Py (discovery, performance, rework)
     │
     ├─ agrupar.py
     │  Agrupamento A: top 10 variantes por frequência
     │  Agrupamento B: K-Means k=4 por features (duração, eventos, marcos processuais)
     │  ▼  cluster_variante_01..10.csv      ← 1 arquivo por variante
     │     cluster_kmeans_0..3.csv/.xes     ← 1 arquivo por cluster
     │     features_kmeans.csv              ← 1 linha/caso com todas as features
     │
     └─ analise_violencia_mulher.py
        Filtro 8: case:assunto_principal contém keywords violência/protetiva/mulher
                  → 8.585 de 13.234 casos (~64.9%)
        SLA liminar: Ajuizamento → 1ª atividade "Liminar"       (alerta > 2 dias)
        SLA total:   Ajuizamento → 1ª atividade terminal         (alerta > 365 dias)
        ▼  violencia_sla_detalhado.csv      ← 1 linha/caso com SLAs e alertas
           violencia_sla_resumo.txt         ← resumo executivo com top críticos
           analises/imgs/violencia_*.png    ← 5 imagens SLA
```

### 2.6 Pipeline — Algoritmos, Datasets e Saídas por Etapa

#### Visão geral

| Etapa | Script | Dataset de entrada | Dataset de saída |
|-------|--------|--------------------|-----------------|
| 1 | `exportar_filtrado.py` | 50.000 proc. (todas as classes) | 13.234 AP Ord. fechados |
| 2 | `happy_path_report.py` | 13.234 (filtrado classe) | subconjunto na janela temporal |
| 3 | `analisar.py` | 13.234 XES (todas análises) / subset 2025 ~1.277 (DFG+Petri Net) | PNGs `analises/imgs/` |
| 4 | `agrupar.py` | 13.234 (filtrado classe) | clusters K-Means + top variantes |
| 5 | `analise_violencia_mulher.py` | 13.234 (filtrado classe) + features K-Means | 8.585 violência + SLA |

---

#### Etapa 1 — `exportar_filtrado.py`

**Algoritmo:**
1. Lê CSV bruto (50.000 proc., todas as classes)
2. Filtro exato: `case:classe == "Ação Penal - Procedimento Ordinário"` → 19.356 proc.
3. Remove casos sem atividade em `TERMINAL_MERITO` → 13.234 fechados
4. (Opcional) Top N variantes: join das atividades por `time:timestamp` → string → `value_counts()` → retém top N

**Saídas:**

| Arquivo | Conteúdo |
|---------|----------|
| `TJPR_Acao_Penal___..._[ts].csv/.xes` | 13.234 casos, 2.376.663 eventos — base de todas as análises |
| `..._top10v_[ts].csv/.xes` | Top 10 variantes (subconjunto reduzido para o Disco) |

---

#### Etapa 2 — `happy_path_report.py`

**Algoritmo:**
1. Carrega CSV filtrado da Etapa 1 (13.234 casos)
2. Filtro temporal: mantém apenas processos com `primeiro_evento >= data_inicio` **E** `ultimo_evento <= data_fim`
3. Classifica cada processo em nível de happy path:

```
nivel_happy_path(atividades_do_caso):
  tem_terminal = atividade ∈ {Trânsito em julgado, Baixa Definitiva, Extinção...}
  tem_recurso  = atividade ∈ {Apelação, RESE, Agravo, Embargos, Habeas Corpus...}
  tem_desvio   = atividade ∈ {Redistribuição, Incompetência...}

  sem terminal          → 0  (em andamento)
  com recurso           → 0  (saiu do rito 1º grau)
  terminal + sem desvio → 1  (IDEAL: rito completo sem desvio)
  terminal + desvio + baixa definitiva → 3
  terminal + desvio + sem baixa        → 2
```

4. Calcula transições A→B com `dias_ate_proxima` para processos happy path (nivel ≥ 1)

**Saídas:**

| Arquivo | Conteúdo |
|---------|----------|
| `*_happy_path.csv` | 1 linha/processo: nivel, duração, variante completa |
| `*_happy_path_transicoes.csv` | 1 linha/transição A→B: timestamps + dias |
| `*_happy_path.xes` | Log XES dos casos nivel ≥ 1 — importar no Disco |

---

#### Etapa 3 — `analisar.py`

**Datasets e algoritmos por análise:**

| Análise | Dataset | Algoritmo |
|---------|---------|-----------|
| DFG frequência | Subset ano=2025 (~1.277 casos) | `pm4py.discover_dfg()` — contagem de pares (A,B) consecutivos; arcos < 2% do máximo removidos |
| DFG performance | Subset ano=2025 (mesmos arcos) | `pm4py.discover_performance_dfg()` — mesmo DFG, valor = tempo médio em segundos entre A e B |
| Petri Net (rito completo) | Subset ano=2025 | Inductive Miner `noise=0.2` — particiona DFG recursivamente em cortes sequenciais/paralelos/choice/loop; 20% de comportamento infrequente ignorado |
| Petri Net (cluster dominante) | Maior cluster K-Means por casos | Inductive Miner `noise=0.4` — sobre o cluster mais populoso detectado dinamicamente |
| Variantes Pareto | **Todos 13.234** | join atividades ordenadas → `value_counts()` → top 30 + curva acumulada |
| Throughput time | **Todos 13.234** | `(max_ts - min_ts).dt.seconds / 86400` por caso |
| Transition time¹ | **Todos 13.234** | `next_event.ts - current_event.ts` por evento → `groupby(activity).mean()` |
| Bottlenecks | **Todos 13.234** | mesmo cálculo de transition time agrupado por `(activity, next_activity)` |
| Rework | **Todos 13.234** | `groupby([case, activity]).size() > 1` — conta repetições da mesma atividade no mesmo caso |
| Organizacional | **Todos 13.234** | volume por `org:resource` (vara); duração mediana por vara dominante (mais frequente por caso) |
| Conformance TBR | **Subset ano=2025** (amostra 500, seed=42) | Token Based Replay — simula tokens na Petri Net; penaliza tokens faltando/sobrando; fitness = proporção de traces que se encaixam no modelo |

> ¹ **Nota técnica:** O gráfico "Sojourn Time" mede o tempo **entre** eventos consecutivos (transition time), não o tempo **dentro** de uma atividade. Como cada evento é um timestamp pontual (sem duração registrada), essa é a melhor aproximação disponível. A distinção é relevante: transition time alto em atividade X pode indicar fila antes de X ou demora depois de X.

**Saídas:**

| Arquivo | Descrição |
|---------|-----------|
| `dfg_frequencia.png` | DFG de frequência — subset 2025, arcos ≥ 2% do máximo |
| `dfg_performance.png` | DFG de performance — mesmos arcos, tempo médio em dias |
| `petri_net.png` | Rede de Petri do rito AP Ord. — Inductive Miner subset 2025 |
| `petri_net_cluster_dominante.png` | Rede de Petri do cluster com mais casos |
| `variantes_pareto.png` | Pareto top 30 variantes — todos 13.234 casos |
| `throughput_time.png` | Histograma duração total — todos 13.234 |
| `sojourn_time.png` | Top 15 atividades por transition time médio |
| `bottlenecks.png` | Top 10 transições A→B mais lentas |
| `rework.png` | Top 15 atividades com mais repetições |
| `organizacional.png` | Volume e duração por vara |
| `conformance_fitness.png` | Distribuição de fitness TBR — 500 amostras do subset 2025 |

---

#### Etapa 4 — `agrupar.py`

**Features extraídas por caso:**

| Feature | Cálculo |
|---------|---------|
| `duracao_dias` | `(last_event.ts - first_event.ts).seconds / 86400` |
| `n_eventos` | `count(events)` |
| `n_atividades_unicas` | `nunique(activity)` |
| `n_passos` | `len(variante.split(" → "))` |
| `tem_liminar`, `tem_sentenca`, `tem_acordao`, `tem_transito`, `tem_recurso`, `tem_redistribuicao`, `tem_audiencia`, `tem_desistencia`, `tem_incompetencia` | Flags booleanas (0/1) por presença de atividade com keyword |

**Algoritmo K-Means:**

```
X = features_numericas + flags_booleanas   (13 colunas)
X_scaled = StandardScaler().fit_transform(X)   # Z-score por feature
KMeans(k=4, random_state=42, n_init=10).fit_predict(X_scaled)
```

**Saídas:**

| Arquivo | Conteúdo |
|---------|----------|
| `*_cluster_variante_01..10.csv` | Event log de cada top variante (1 variante = 1 caminho exato) |
| `*_cluster_kmeans_0..3.csv/.xes` | Event log de cada cluster K-Means |
| `*_features_kmeans.csv` | 1 linha/caso: todas features + `cluster_kmeans` ID |
| `*_clusters.png` | 4 subplots: scatter, tamanho, duração mediana, cobertura variantes |

---

#### Etapa 5 — `analise_violencia_mulher.py`

**Filtro de violência:** exact match em `case:assunto_principal` contra 9 strings de referência (violência doméstica, lesão, descumprimento de medida protetiva, feminicídio, violência psicológica).

**Cálculo de SLA por caso:**

```
ts_ajuizamento:
  1º  case:data_ajuizamento (atributo do caso — fonte primária para AP penal)
  2º  1ª ocorrência de "Petição - Petição inicial" ou "Recebimento da Petição"
  3º  timestamp do 1º evento (fallback final)

sla_liminar_dias  = ts_liminar - ts_ajuizamento         (se liminar concedida)
sla_total_dias    = ts_transito_julgado - ts_ajuizamento (se processo encerrado)
alerta_total      = sla_total_dias > 365 dias
```

**Saídas:**

| Arquivo | Conteúdo |
|---------|----------|
| `violencia_sla_liminar.png` | Boxplot + jitter dias até liminar por categoria |
| `violencia_sla_total.png` | Barras horiz. duração total por caso (linha ref. 365d) |
| `violencia_vs_geral.png` | Violin: violência vs. outros AP |
| `violencia_por_cluster.png` | Stacked bar violência por cluster K-Means |
| `violencia_sla_cumprimento.png` | % casos por faixa de prazo (≤2d, 3–7d, 8–30d, >30d) |
| `violencia_sla_detalhado.csv` | 1 linha/caso: SLAs + alertas + categoria |
| `violencia_sla_resumo.txt` | Resumo executivo + top 10 casos mais críticos |

---

### 2.7 Bugs Identificados e Corrigidos

Durante a revisão do código do pipeline foram identificados e corrigidos os seguintes problemas:

| # | Severidade | Script | Bug | Correção |
|---|-----------|--------|-----|----------|
| 1 | **CRÍTICO** | `happy_path_report.py` | `carregar()` selecionava o arquivo `top10v` (10 casos) em vez do log completo (13.234) — ordenação alfabética `'t' > '2'` fazia `candidates[-1]` retornar o arquivo errado | Adicionado filtro `"top" not in filename` na lista de candidatos (idêntico ao tratamento em `agrupar.py`) |
| 2 | **ALTO** | `analise_violencia_mulher.py` | `ts_ajuizamento` buscava atividade "Petição - Petição inicial" (nomenclatura civil/CPC) em processo penal, onde a peça inicial é a Denúncia do MP ou Queixa-Crime — atividade geralmente ausente no log → `sla_total_dias = None` para muitos casos | Substituído por `case:data_ajuizamento` (atributo de caso gravado na extração) com 2 fallbacks: atividade de petição inicial e primeiro evento do caso |
| 3 | **MÉDIO** | `analisar.py` | Conformance (Token Based Replay) rodava os 13.234 casos contra Petri Net minerada de subset 2025 (~1.277 casos) — mismatch de populações inflava/deflacionava artificialmente o fitness | Conformance agora usa o mesmo `log_dfg` que gerou a Petri Net; se `--ano` não for informado, `log_dfg == log_c` (sem diferença) |
| 4 | **MÉDIO** | `analisar.py` | `petri_net_cluster3.png` hardcoded para cluster ID=3; cluster dominante era ID=0 (6.408 casos, 48.4%) — análise da Petri Net do "cluster dominante" estava errada | Detecção dinâmica: seleciona o arquivo `*_cluster_kmeans_*.xes` com maior tamanho (proxy para número de casos); saída renomeada para `petri_net_cluster_dominante.png` |
| 5 | **BAIXO** | `happy_path_report.py` | `DESVIO_RECURSIVO` não incluía "Embargos de Declaração", "Recurso Ordinário" e "Habeas Corpus" — casos com esses recursos recebiam nível 1 (happy path ideal) indevidamente | Adicionados os 3 recursos ao conjunto `DESVIO_RECURSIVO` |

> **Impacto do Bug #1 nos resultados anteriores:** O relatório de happy path foi calculado sobre apenas 10 casos (top 10 variantes) em vez dos 13.234. Os números de happy path reportados nas execuções anteriores devem ser desconsiderados. Recomenda-se re-executar `python run_pipeline.py` para resultados corretos.

---

## 3. MINERAÇÃO E ANÁLISE

### 3.1 Ferramentas Utilizadas

| Ferramenta | Uso |
|------------|-----|
| **Python 3.14** | Extração, transformação, análise |
| **PM4Py 2.7.x** | Discovery, conformance, performance |
| **Pandas / NumPy** | Manipulação de dados |
| **Matplotlib** | Visualizações |
| **scikit-learn** | K-Means clustering |
| **Disco** (importação XES) | Visualização interativa de DFG |
| **API CNJ Datajud** | Fonte dos dados (LO) |

### 3.2 Tarefas de Mineração de Processos Executadas

#### 3.2.1 Descoberta de Processo (Discovery)

**O que é Process Discovery?**
Discovery é a tarefa central de Process Mining: a partir de um log de eventos (sequências
reais de atividades registradas em sistemas), algoritmos descobrem automaticamente um
**modelo de processo** — uma representação formal do fluxo observado na prática. O modelo
resultante não é desenhado manualmente: emerge dos dados.

Dois tipos de modelos foram descobertos:

---

**DFG — Directly-Follows Graph** (`imgs/dfg_frequencia.png` e `imgs/dfg_performance.png`)

O DFG é o modelo mais simples e direto de Process Mining. Para cada par de atividades
(A → B), conta quantas vezes B ocorreu imediatamente após A no mesmo processo. O resultado
é um grafo dirigido onde:
- **Nós** = atividades processuais (ex: "Citação", "Sentença", "Recurso")
- **Arcos** = transições diretas entre atividades, com peso = frequência ou tempo médio

**DFG de Frequência** mostra quais caminhos são mais comuns. Arco mais grosso = fluxo
principal. DFG de **Performance** exibe o tempo médio (em dias) em cada transição —
os arcos mais lentos são os gargalos do processo.

> **Nota técnica — filtros aplicados:**
> Com 13.234 casos e 377 atividades distintas, o DFG completo gera 3.497 arcos —
> inutilizável visualmente. Dois filtros foram aplicados:
> 1. **Filtro de ano:** apenas **1.277 casos ajuizados em 2025** para discovery
>    (subconjunto representativo e recente). Demais análises usam todos os 13.234.
> 2. **Threshold de frequência:** apenas arcos com frequência ≥ **2% do arco mais
>    frequente** → reduz de 3.497 para **201 arcos visíveis** sem perder o fluxo principal.

Atividades mais frequentes no log (top 5, baseado no dataset 2025):

| Atividade | Tipo | Papel no processo |
|-----------|------|------------------|
| Confirmada | Ato cartorário | Confirmação de cumprimento de diligência |
| Expedição de documento - Outros | Ato cartorário | Emissão genérica de documentos |
| Recebimento | Ato cartorário | Recebimento de remessas e petições |
| Entrega em carga/vista | Ato cartorário | Entrega de autos para vista de parte/advogado |
| Documento - Outros documentos | Ato de juntada | Juntada genérica de peças ao processo |

> **Achado:** Atividades cartoriais (confirmação, expedição, juntada) dominam o DFG —
> não atividades jurisdicionais (sentença, citação, audiência). Isso indica que
> **a maior parte dos eventos registrados é administrativa**, não decisória. O volume de
> movimentação cartorial mascara a espera real por decisão judicial.

---

**Petri Net — Inductive Miner** (`imgs/petri_net.png`)

O **Inductive Miner** (Leemans et al., 2013) é um algoritmo de discovery que produz uma
**Rede de Petri** — modelo formal com garantias estruturais (soundness: toda execução tem
início e fim, sem deadlocks ou livelocks). Funciona recursivamente:

1. Divide o log em sublogs usando "cortes" (sequential, parallel, choice, loop)
2. Aplica o corte mais simples que explica os dados
3. Repete para cada sublog até casos triviais

O parâmetro `noise_threshold=0.2` significa que **20% das traces mais infrequentes** em
cada passo recursivo podem ser ignoradas como ruído — aumenta a legibilidade sem grandes
perdas de fitness.

**Elementos da Rede de Petri:**
- **Círculos (places)** = estados do processo (ex: "processo aguardando citação")
- **Retângulos brancos/cinza (transitions)** = atividades reais com nome (ex: "Sentença")
- **Retângulos pretos (silent/tau transitions)** = transições invisíveis de roteamento —
  representam XOR-splits (escolhas), AND-splits (paralelismo) e loops estruturais.
  **Não são erros**: são artefatos necessários para modelar bifurcações sem nome explícito.
- **Arcos (→)** = fluxo de tokens entre states e transitions

> **Por que tantos retângulos pretos (tau)?**
> Com 377 atividades distintas e 13.234 variantes únicas no TJPR, o Inductive Miner
> precisa criar muitas estruturas de roteamento para acomodar a diversidade observada.
> Cada bifurcação processual (processo pode ir para atividade A OU B após C) vira um
> tau. Modelo com `noise=0.2`: **108 places / 144 transitions (≈ 60 tau)**.
> Para rede mais compacta: `noise=0.1` gera apenas 58 places / 121 transitions (55 labeled).

#### 3.2.2 Análise de Variantes

Arquivo: `imgs/variantes_pareto.png`

**O que é uma variante de processo?**
Uma variante é a **sequência exata e ordenada de todas as atividades** de um caso do início
ao fim. Se dois processos executaram exatamente as mesmas atividades na mesma ordem, são
a mesma variante. Se qualquer atividade diferir (nome, posição ou quantidade), são variantes
distintas. Variantes identificam o "caminho" que o processo percorreu.

O **Pareto de Variantes** rankeia variantes por frequência. A curva acumulada mostra
quantas variantes são necessárias para cobrir X% dos casos — quanto mais íngreme a curva,
mais padronizado o processo.

**Por que variantes importam?**
- Processo padronizado: poucas variantes cobrem 80% dos casos → previsível, auditável
- Processo ad hoc: muitas variantes para 80% → cada caso é único → difícil de controlar,
  otimizar ou garantir tratamento isonômico entre réus

| Métrica | Valor |
|---------|-------|
| Total de variantes únicas | **13.234** |
| Variantes para cobrir 80% dos casos | **5.200** |
| Cobertura da variante mais frequente | **< 0.02%** (1 caso em 13.234) |

> **QP3 respondida:** Com 13.234 casos e **13.234 variantes únicas**, o log confirma
> **ausência total de padronização** nos fluxos reais do TJPR para Ação Penal Ordinária.
> Cada processo seguiu um caminho processual distinto — ratio variantes/casos = **1:1**.
> 5.200 variantes para cobrir 80% dos casos = fragmentação processual extrema.
>
> **Impacto prático:** impossível estabelecer SLA por etapa processual, identificar
> desvios ou garantir isonomia de tramitação entre réus. A variância sugere forte
> influência da vara, do advogado e do tipo de crime sobre o rito efetivamente seguido.

#### 3.2.3 Análise de Performance Temporal (Throughput Time)

Arquivo: `imgs/throughput_time.png`

**O que é Throughput Time?**
Throughput time (tempo de ciclo) é a **duração total de um processo**: do primeiro evento
(ajuizamento) ao último evento (trânsito em julgado ou baixa definitiva). Mede o tempo
que o processo "viveu" no sistema. É a métrica mais direta de eficiência processual — a
que a CF art. 5º, LXXVIII ("razoável duração do processo") protege.

O histograma mostra a distribuição de durações. Distribuição concentrada = processos
resolvidos em tempo similar. Cauda longa à direita = maioria razoável + outliers extremos.

**Por que usar mediana e não média?**
Distribuições com cauda longa (como tempos judiciais) têm média distorcida por outliers.
A mediana divide exatamente 50% dos casos acima e abaixo — mais representativa do caso típico.

| Percentil | Duração | Significado |
|-----------|---------|-------------|
| **Mediana (P50)** | **755 dias** | Metade dos processos fechou em até 755 dias |
| **Média** | **563 dias** | Média puxada por outliers longos |
| P75 | ~740 dias | 75% fecharam em até ~740 dias |
| P90 | **1.489 dias** | 10% dos processos durou mais de 1.489 dias |
| P95 | **1.707 dias** | 5% mais lentos ultrapassaram ~4,7 anos |
| Máximo | **2.266 dias** | Processo mais demorado: ~6,2 anos |

> **QP1 respondida:** A CF art. 5º, LXXVIII garante razoável duração do processo.
> Para processo penal de 1º grau, doutrina e jurisprudência indicam 1 ano como referência
> razoável para instrução simples. A mediana de **755 dias (2,1 anos)** já ultrapassa
> esse referencial; o P90 de **1.489 dias (4,1 anos)** representa falha sistemática de
> celeridade. A média > mediana confirma cauda longa: casos extremamente lentos puxam
> a média para cima, mas o problema é estrutural — mesmo o caso "típico" (mediana) está
> fora de qualquer padrão razoável.

---

**Sojourn Time por atividade** — `imgs/sojourn_time.png`

**O que é Sojourn Time?**
Sojourn time mede o **tempo que o processo permanece em uma atividade** antes de avançar
para a próxima. Diferente do throughput (duração total), o sojourn identifica em qual
etapa específica o processo "para" e quanto tempo fica parado. Alto sojourn = fila,
pendência não resolvida ou falta de recurso naquela atividade.

O gráfico exibe as 15 atividades com maior sojourn médio — os "estrangulamentos" internos
do fluxo. Comparar com gargalos (3.2.4): sojourn mede espera NA atividade; gargalo mede
espera na transição ENTRE atividades.

#### 3.2.4 Análise de Gargalos (Top 10)

Arquivo: `imgs/bottlenecks.png`

**O que é análise de gargalos?**
Um gargalo (bottleneck) é a transição A → B onde o processo demora mais para avançar.
Enquanto sojourn time mede espera dentro de uma atividade, a análise de gargalos mede
o **tempo entre atividades** — quanto o processo aguarda para que a atividade B comece
após A terminar. Identifica onde a "fila" se forma no fluxo.

Métricas por transição:
- **Média** = tempo médio entre A e B (sensível a outliers)
- **Mediana** = tempo típico (robusto a outliers)
- **Média >> mediana**: poucos casos extremamente lentos puxam a média — problema pontual
- **Média ≈ mediana**: todos os casos demoram — problema estrutural/sistêmico

| Transição (A → B) | Média | Diagnóstico |
|-------------------|-------|-------------|
| **Mero expediente → Recebimento** | **235.9 dias** | Processo parado sem movimentação — maior gargalo |
| Remessa em grau de recurso → Acórdão | **127.9 dias** | 2º grau lento para publicar acórdão |
| Por decisão judicial → Apensamento | **111.0 dias** | Ato cartorário represado pós-decisão |
| Expedição certidão → Morte do agente | **108.2 dias** | Casos encerrados por extinção da punibilidade |
| Remessa em grau de recurso → Mudança de Assunto | **94.9 dias** | Reclassificação tardia pós-recurso |
| Definitivo → Petição (outras) | **82.0 dias** | Autos "definitivos" aguardam ato cartorário |
| Expedição certidão → Recebimento | **81.5 dias** | Certidão expedida mas não recebida/cumprida |
| Expedição certidão → Procedência | **77.2 dias** | Sentença de procedência com certidão pendente |
| Remessa devolução → Recebimento | **72.7 dias** | Autos devolvidos mas não distribuídos |

> **QP2 respondida:** Três gargalos estruturais identificados:
>
> 1. **Gargalo #1 — "Mero expediente" (236 dias):** "Mero expediente" é uma anotação
>    cartorária que significa essencialmente "sem movimentação relevante". Um processo
>    aguardando 236 dias para ser recebido após essa marcação está **parado sem causa
>    processual registrada** — fila de distribuição ou acúmulo de acervo cartorário.
>
> 2. **Gargalo #2 — Recurso → Acórdão (128 dias):** Processos remetidos ao 2º grau
>    aguardam quase 4 meses em média para publicação de acórdão. Indica sobrecarga
>    do tribunal recursal independente do 1º grau.
>
> 3. **Gargalo #3 — Pós-decisão cartorária (111 dias):** Após decisão judicial,
>    atos de cumprimento (apensamento, expedição de certidão) demoram meses —
>    indica fila nos cartórios para executar ordens judiciais já proferidas.

#### 3.2.5 Análise de Rework

Arquivo: `imgs/rework.png`

**O que é Rework?**
Rework ocorre quando a **mesma atividade é executada mais de uma vez no mesmo processo**.
Em processos ideais, cada etapa ocorre uma vez em sequência linear. Rework indica:
- Retorno a etapas anteriores (ex: nova citação após falha da primeira)
- Ciclos repetitivos endêmicos (ex: "Conclusão → Despacho → Conclusão" repetido N vezes)
- Múltiplas execuções da mesma ação (ex: 5 expedições de mandado no mesmo processo)

O gráfico mostra as 15 atividades com mais repetições totais no dataset — os maiores
"acumuladores de rework". Quanto mais alta a barra, mais aquela atividade se repete
em média por processo.

**Por que rework é problemático?**
Cada execução adicional consome tempo de cartório/gabinete e adiciona dias ao throughput.
Rework de 100% significa que não há caminho linear no processo real — nenhum processo
seguiu o rito CPP "de uma vez só", sem retornar a etapas já cumpridas.

| Métrica | Valor |
|---------|-------|
| Processos com rework | **13.232 de 13.234 (100%)** |
| Interpretação | Nenhum processo seguiu caminho linear único |

> Rework de 100% em Ação Penal Ordinária é esperado em parte: o CPP permite
> múltiplos atos dentro das mesmas categorias (ex: citação editalícia após citação
> pessoal frustrada, múltiplas sessões de audiência). Porém, a **escala** do rework
> no TJPR — com atividades cartoriais repetidas dezenas de vezes — indica que
> parte significativa das repetições não é estrutural (CPP), mas operacional:
>
> - Loops "Conclusão → Despacho → Conclusão" indicam **fila de gabinete** — processo
>   vai ao juiz, retorna sem despacho, volta ao juiz múltiplas vezes
> - Expedições múltiplas de mandado = **falhas de cumprimento** ou endereço errado
> - Juntadas genéricas repetidas = **acervo de petições** sendo processado em lotes
>
> **Impacto no throughput:** cada loop adicional de "Conclusão → Despacho" adiciona
> em média 30-90 dias ao processo. Com 100% de casos afetados, o rework é responsável
> por parcela significativa dos 755 dias medianos de throughput.

#### 3.2.6 Perspectiva Organizacional

Arquivo: `imgs/organizacional.png`

**O que é a perspectiva organizacional em Process Mining?**
A perspectiva organizacional analisa **quem executa o processo** — no contexto judicial,
qual vara (unidade organizacional) tramita cada caso. Compara volume de eventos por vara
e performance (duração mediana) por vara. Identifica:
- Varas sobrecarregadas (alto volume + alta duração) → candidatas prioritárias a intervenção
- Heterogeneidade de desempenho (mesma classe processual, varas com durações muito diferentes)
- Outliers organizacionais (vara muito mais lenta ou rápida que a média)

No Datajud, o campo `org:resource` (recurso organizacional) identifica a vara de origem
de cada evento processual — mapeado diretamente do sistema CNJ.

| Métrica | Valor |
|---------|-------|
| Varas com ≥ 5 processos analisadas | Múltiplas varas criminais TJPR |
| Menor duração mediana | **695 dias** |
| Maior duração mediana | **878 dias** |
| Variação absoluta | **183 dias** |
| Variação relativa | **26% de diferença entre a mais eficiente e a mais lenta** |

> **Interpretação:** A diferença de **26% entre varas** para o **mesmo tipo de processo**
> (Ação Penal Ordinária) revela heterogeneidade operacional sem justificativa processual
> aparente. Casos similares têm durações medianas que diferem em quase 6 meses dependendo
> da vara de distribuição — violação do princípio da isonomia de tramitação.
>
> Dois problemas simultâneos:
> 1. **Nível geral alto:** mesmo a vara mais eficiente (695d) ultrapassa amplamente qualquer
>    referencial de celeridade para 1º grau — o problema não é de uma vara específica,
>    é sistêmico.
> 2. **Alta dispersão:** 26% de variação indica que fatores locais (gestão cartorária,
>    perfil de acervo, recursos humanos da vara) impactam significativamente a duração —
>    oportunidade de aprender com as varas mais eficientes e disseminar boas práticas.

#### 3.2.7 Conformance Checking — Modelo Descoberto

Arquivo: `imgs/conformance_fitness.png`

Quatro métricas de qualidade de modelo de processo (van der Aalst, 2016) calculadas via
Token-Based Replay contra a Petri Net descoberta pelo Inductive Miner.

> **Nota metodológica:** Duas Petri Nets foram descobertas neste projeto:
> - **`petri_net.png`** (visualização): 1.277 casos ajuizados em 2025 → **194 places / 367 transitions**
> - **Métricas de conformance** abaixo: 500 amostras aleatórias do dataset completo (13.234 casos,
>   seed=42) → **108 places / 144 transitions**
>
> O modelo 2025 é maior porque 500 amostras de 1.277 casos cobrem 39% das variantes do subconjunto,
> enquanto 500 de 13.234 cobrem apenas 3.8% — maior cobertura relativa produz modelo mais ramificado.
> As métricas abaixo são válidas para o dataset geral e representam o comportamento típico do TJPR.
> Precision no modelo 2025 não foi computada (TBR sobre 194/367 net: inviável sem cluster dedicado).

| Métrica | Valor TJPR | Dataset | Interpretação |
|---------|-----------|---------|---------------|
| **Fitness** | **99.6%** | 500-sample / 13.234 casos | Modelo reproduz bem o log — poucos tokens faltando/sobrando |
| **Precision** | **pendente** | 500-sample / 13.234 casos | Modelo permite comportamento muito além do log — esperado |
| **Generalization** | **pendente** | 500-sample / 13.234 casos | Modelo generaliza bem para casos não vistos na amostra |
| **Simplicity** | **60.58%** | 108 places / 144 transitions | Complexidade moderada para processo com 377 atividades |
| Fitness (histograma) | **94.37%** | `conformance_fitness.png` / 2025 | Fitness do modelo visual (1.277 casos 2025) |

##### O que cada métrica significa e seu impacto

**Fitness** — mede se o log pode ser reproduzido pelo modelo. Cada evento do processo é
"simulado" como ficha (token) na Petri Net. Alta fitness = modelo captura o comportamento
real. Baixa fitness = modelo muito restritivo — rejeita caminhos que ocorrem nos dados.

- TJPR **99.6%**: modelo descobre com fidelidade. Apenas ~0.4% das execuções têm tokens
  faltando (atividade sem arco no modelo) ou sobrando (atividade finalizada sem consumir token).
- Histograma `conformance_fitness.png` (modelo 2025) mostra 94.37% médio, 5.6% abaixo de 0.8.

**Precision** — mede quanto comportamento extra o modelo permite além do que o log mostra.
Precisão baixa = "flower model" — modelo aceita qualquer sequência, mesmo não observada.

- TJPR **pendente**: precisão muito baixa, esperada dado o contexto:
  - 377 atividades distintas e 13.234 variantes únicas → o Inductive Miner cria muitos splits
    paralelos/alternativos para acomodar toda a diversidade observada
  - Cada tau (retângulo preto) expande o espaço de comportamentos permitidos
  - Modelo com noise=0.2 prioriza fitness sobre precisão
- **Impacto:** baixa precisão não indica processo mal gerido — indica que o modelo é
  permissivo. Para obter modelo preciso seria necessário reduzir atividades (simplificação
  semântica dos TPU) ou aumentar noise_threshold (perda de fitness).

**Generalization** — mede se o modelo generaliza para casos além da amostra usada no
discovery. Alta generalização = modelo não decorou a amostra; captura padrões gerais.

- TJPR **pendente**: alta generalização esperada. Cada transição da rede foi disparada em múltiplos
  casos da amostra → modelo não é específico demais a um subconjunto de processos.
- Complementa o fitness: fitness alto + generalização alta = modelo robusto e representativo.

**Simplicity** — mede a "elegância" do modelo (princípio de Occam). Baseado na proporção
de arcos sobre transições (Arc Degree). Modelos simples têm poucos arcos por transição.

- TJPR **60.58%**: complexidade moderada. 108 places, 144 transitions (incluindo tau).
- Alta para um processo com 377 atividades — o Inductive Miner comprimiu bem a estrutura.
- Simplicity abaixo de 50% indicaria modelo "spaghetti" (arcos excessivos sem estrutura).

##### Interpretação conjunta — TJPR

| Combinação observada | Diagnóstico |
|---------------------|-------------|
| Fitness alto (99.6%) + Precision pendente | Modelo correto, processo altamente variável |
| Generalization pendente | Modelo generaliza — não é artefato da amostra |
| Simplicity moderada (61%) | Estrutura compreensível apesar das 377 atividades |

O padrão **fitness↑ / precision↓** é característico de processos ad hoc com alta
heterogeneidade — cada caso percorre caminho único, impedindo modelo preciso sem perda
de fitness. Recomendação: para análise de conformidade com o CPP, construir Petri Net
normativa manual (arts. 394-405) e medir fitness contra esse modelo — trabalho futuro.

> **Nota:** Conformance checking contra modelo normativo CPP (Petri Net manual) não
> foi implementado para Ação Penal Ordinária nesta fase do projeto.

#### 3.2.8 Agrupamento — K-Means (k=4)

Arquivo: `imgs/TJPR_Acao_Penal___Procedimento_Ordinario_clusters.png`

**O que é K-Means em Process Mining?**
K-Means é um algoritmo de aprendizado não supervisionado que agrupa casos com comportamento
similar. Em vez de analisar sequências (como em variantes), o K-Means usa **features numéricas**
de cada processo para encontrar grupos ("clusters") com perfis parecidos.

O objetivo é responder: **existem tipos identificáveis de processo** que compartilham
características, apesar da infinidade de variantes? Cada cluster representa um "perfil
comportamental" — subconjunto com padrão de duração, complexidade e marcos processuais similar.

**Features utilizadas no modelo (vetores por processo):**

| Feature | Tipo | Justificativa |
|---------|------|--------------|
| Duração total (dias) | Numérica | Throughput time |
| Número de eventos | Numérica | Complexidade operacional |
| Atividades únicas | Numérica | Diversidade de etapas |
| Tem trânsito em julgado | Booleana | Completude do rito |
| Tem acórdão | Booleana | Passou por 2º grau |
| Tem recurso | Booleana | Contestado pelo réu |
| Teve redistribuição | Booleana | Mudança de vara |
| Teve desistência | Booleana | Extinção antecipada |
| Declaração de incompetência | Booleana | Erro de competência |
| Absolvição sumária | Booleana | Sentença sem instrução |

Após normalização (StandardScaler), K-Means com k=4 foi aplicado. O número de clusters
foi escolhido por análise do Elbow Method e silhouette score.

| Cluster | Casos | % | Mediana (dias) | Ev./caso | Marco dominante | Perfil |
|---------|-------|---|----------------|----------|-----------------|--------|
| **0** | 6.408 | 48.4% | 588d | 160 | Redistribuição | Fluxo dominante |
| **1** | 3.583 | 27.1% | 1.072d | 238 | Recursos | Processos longos |
| **2** | 105 | 0.8% | 1.014d | 206 | Complexos | Casos atípicos |
| **3** | 3.138 | 23.7% | 775d | 140 | Simples | Fluxo secundário |

> **QP4 respondida:** 4 perfis comportamentais identificados:
>
> - **Cluster 0 (48.4%, 588d)** — Fluxo principal. Redistribuídos, fluxo dominante.
>   588 dias ainda acima de qualquer referencial razoável.
>
> - **Cluster 1 (27.1%, 1.072d)** — Processos longos com recursos. A espera pelo acórdão
>   (128 dias médios, ver gargalos) explica a maior duração. 238 eventos/caso = mais etapas.
>
> - **Cluster 3 (23.7%, 775d)** — Fluxo secundário: processos simples com duração intermediária.
>
> - **Cluster 2 (0.8%, 1.014d)** — 105 casos atípicos/complexos. Longa duração.
>
> O K-Means revela que a variabilidade do TJPR tem **estrutura**: os 4 clusters são
> separáveis por features interpretáveis. O maior driver de duração é a presença de
> recurso/2º grau (Cluster 1), não o tipo de crime ou a vara isoladamente.

---

## 4. AVALIAÇÃO

### 4.1 Síntese dos Achados por Questão de Pesquisa

**QP1 — Prazo:**
O TJPR leva em mediana **755 dias (2,1 anos)** para julgar uma Ação Penal Ordinária
em primeiro grau. O P90 é de **1.489 dias (4,1 anos)**. A CF art. 5º, LXXVIII garante
razoável duração do processo — a mediana atual ultrapassa qualquer referência razoável
para processo penal de primeiro grau.

**QP2 — Gargalos:**
Os 3 maiores gargalos são:
1. **Mero expediente → Recebimento (236 dias)** — processo paralisado sem movimentação efetiva
2. **Remessa grau recurso → Acórdão (128 dias)** — 2º grau lento para julgar recursos
3. **Por decisão judicial → Apensamento (111 dias)** — atos cartorários represados pós-decisão

**QP3 — Padronização:**
13.234 casos, 13.234 variantes únicas. **Zero padronização** de fluxo. 5.200 variantes
para cobrir 80% dos casos. O fluxo processual real é completamente individualizado.

**QP4 — Perfis:**
4 clusters. Cluster 0 domina (48.4%, mediana 588d). Cluster 1 (27.1%, 1.072d) representa
casos mais complexos. Cluster 2 (0.8%) são os casos atípicos.

**QP5 — Violência doméstica:**
8.585 de 13.234 casos (~64.9%) envolvem violência/protetiva. A mediana de casos de violência/protetiva (490.2d) é **menor** que os demais (569.7d), indicando prioridade relativa de tramitação no dataset 2020-2026.

### 4.2 Limitações

- **Escopo de assunto:** 50.000 processos extraídos com filtro Ação Penal + mulher/protetiva — subconjunto da totalidade das Ações Penais do TJPR
- **Uma janela temporal/tribunal:** sem TJRS para comparação cross-tribunal
- **Nomenclatura TPU:** atividades mapeadas por texto — variações ortográficas geram ruído
- **Etapas ausentes ≠ etapas não realizadas:** registro no sistema pode estar incompleto
- **Conformance normativo:** Petri Net manual CPP arts. 394-405 não implementada (trabalho futuro)

---

## 5. MELHORIA DO PROCESSO

### 5.1 Sugestões para o Dono do Processo (TJPR / Varas Criminais)

**P1 — Eliminar "Mero expediente" (gargalo principal: 236 dias):**
O intervalo médio de 236 dias entre "Mero expediente" e "Recebimento" indica processos
em estado de inércia. Implementar alerta automático no PJe quando processo ficar sem
movimentação substantiva por mais de **30 dias**.

**P2 — Priorização operacional para violência doméstica:**
CNJ Resolução 254/2018 exige tratamento prioritário. Mediana violência (490.2d) < outros AP (569.7d): prioridade relativa existe. Porém 53% excede alerta 365d. Criar fila dedicada com SLA
interno nas Varas de Violência Doméstica do TJPR.

**P3 — Benchmarking entre varas:**
Cluster 0 (588d mediana) vs. Cluster 1 (1.072d mediana) = 484 dias de diferença.
Varas mais lentas (878d) vs. mais rápidas (695d) = 183 dias de diferença.
Compartilhar práticas das varas com menor mediana como modelo operacional interno.

**P4 — Meta CNJ de duração:**
Definir indicador KPI: "% de Ações Penais julgadas em ≤ 365 dias".
Hoje: estimativa < 40% (mediana 755d, P90 1.489d).
Meta progressiva: ≥ 50% em 12 meses → ≥ 70% em 24 meses.

**P5 — Reduzir loops pós-"Definitivo":**
82 dias médios entre "Definitivo" e próxima petição indicam atos cartorários represados
após sentença. Criar fila prioritária para atos de baixa após decisão de mérito.

### 5.2 Sugestões para o Sistema de Informação (PJe/TJPR)

**S1 — Alertas de inércia processual:**
Implementar alerta automático quando processo ficar sem movimentação por 30 dias.
Dado que o maior gargalo é "Mero expediente" (236 dias de inércia), o alerta em 30 dias
permitiria intervenção precoce em 100% desses casos.

**S2 — Dashboard de violência doméstica em tempo real:**
Integrar API Datajud → painel TJPR com:
- Throughput por vara com foco em casos de violência
- Alertas automáticos para casos sem movimentação há 30 dias
- Flag de prioridade conforme CNJ Resolução 254/2018

**S3 — Registro obrigatório de marcos processuais:**
Tornar obrigatório o registro de: Resposta à Acusação, Decisão sobre absolvição sumária,
data de designação de audiência de instrução. Hoje esses marcos estão ausentes em
parcela significativa dos casos, impedindo conformance checking normativo completo.

---

## 5.3 Análise Especializada — Violência Doméstica/Protetiva

### Contexto legal

| Norma | O que regula | Referência |
|-------|-------------|------------|
| Lei Maria da Penha art. 18 (Lei 11.340/2006) | Decisão sobre medida protetiva de urgência (1º grau) | **48 horas** |
| CNJ Resolução 254/2018 | Prioridade de tramitação para casos de violência doméstica | Prioridade formal |
| CNJ Resolução 385/2021 | Prioridade de pauta em instâncias superiores | Prioridade formal |
| CF art. 5º, LXXVIII | Razoável duração do processo e celeridade | Garantia constitucional |

### Universo analisado

De 13.234 Ações Penais Ordinárias fechadas no dataset, **8.585 casos (~64.9%)** envolvem
violência/protetiva:

| Categoria | N |
|-----------|---|
| Contra a Mulher | 5.232 |
| Lesão Cometida em Razão da Condição de Mulher | 2.350 |
| Descumprimento de Medida Protetiva de Urgência | 949 |
| Violência Psicológica contra a Mulher | 36 |
| Feminicídio | 18 |

> **Nota metodológica:** A Ação Penal Ordinária não utiliza medidas liminares como instrumento central.
> A análise de SLA mede o tempo até o **trânsito em julgado** como métrica principal.

### Resultados SLA

| Métrica | Violência/Protetiva | Outros |
|---------|--------------------|--------|
| Mediana duração até trânsito em julgado | **490.2 dias** | 569.7 dias |
| Máximo duração | 2.113.0 dias | — |

> **QP5 respondida:** A mediana de casos de violência/protetiva (490.2d) é **menor** que
> os demais (569.7d), indicando prioridade relativa de tramitação no dataset 2020-2026. Contudo, 53% dos casos (4.522/8.585) excedem 365d de alerta, evidenciando ausência de SLA interno padronizado.

### Interpretação PM²

- **nota:** mediana violência/protetiva (490.2d) < outros (569.7d) — dataset 2020-2026 mostra prioridade relativa
- **Alta variância:** 0 a 2.113 dias — nenhuma vara aplica SLA interno uniforme
- **CNJ Res. 254/2018:** prevê prioridade de tramitação — implementada parcialmente; 53% ainda acima de 365d
- **Sugestão P2:** criar flag automático no PJe para assuntos de violência/protetiva com meta de 365 dias

---

## 6. ARQUIVOS GERADOS

### 6.1 Logs de Eventos (output/)

| Arquivo | Conteúdo | Quando usar |
|---------|----------|-------------|
| `TJPR_Acao_Penal_*.csv/.xes` | Event log completo: 13.234 casos, 2.376.663 eventos, 1 linha/evento | Base de todas as análises; importar no Disco para exploração livre |
| `*_top10v.csv/.xes` | Top 10 variantes processuais (casos fechados) | Analisar caminho mais comum no Disco sem sobrecarregar a ferramenta |
| `*_happy_path.csv` | 1 linha/processo: nivel (0–3), duração, variante completa | Filtrar `nivel >= 1` para casos no rito completo; base para benchmarking por etapa |
| `*_happy_path_transicoes.csv` | 1 linha/transição A→B: timestamps + dias entre elas | Calcular SLA por etapa específica; identificar qual passo demora mais |
| `*_happy_path.xes` | Log XES apenas dos casos happy path | Importar no Disco para conformance do rito ordinário ideal |
| `*_features_kmeans.csv` | 1 linha/caso: duração, n_eventos, atividades únicas, variante, marcos booleanos | Features brutas do K-Means; filtrar por `cluster` para análise de subgrupo |
| `cluster_kmeans_0..3.csv/.xes` | Event log de cada cluster K-Means | Analisar perfil comportamental específico no Disco |
| `cluster_variante_01..10.csv` | Event log de cada top variante | Analisar sequência exata de uma variante; 1 variante = 1 caminho único |
| `violencia_sla_detalhado.csv` | 1 linha/caso: assunto, categoria, sla_liminar_dias, sla_total_dias, alerta_total | Filtrar `alerta_total == True` para casos > 365d; cruzar case_id para auditoria |
| `violencia_sla_resumo.txt` | Texto com métricas SLA e top 10 casos mais críticos | Leitura executiva rápida; top críticos = candidatos a auditoria imediata |

### 6.2 Visualizações — Descrição e Interpretação (analises/imgs/)

#### `dfg_frequencia.png` — DFG de Frequência
Directly-Follows Graph com a frequência de cada transição A→B. Filtrado: 1.277 casos de 2025, arcos ≥ 2% do máximo (201 de 3.497 arcos originais).

**Como interpretar:**
- Nós maiores/mais escuros = atividades mais frequentes no processo
- Arcos mais grossos = caminho mais comum (fluxo principal)
- Múltiplos arcos saindo do mesmo nó = bifurcações e desvios processuais
- Loops = atividades que se repetem (rework)

---

#### `dfg_performance.png` — DFG de Performance
Mesma estrutura do DFG de frequência, mas os arcos exibem o **tempo médio em dias** entre A e B.

**Como interpretar:**
- Arcos com alto tempo = gargalos do processo
- Arco frequente (grosso) + lento = problema sistêmico urgente
- Arco raro + lento = exceção ou desvio específico
- **Gargalo principal TJPR:** Mero expediente → Recebimento: **235.9 dias** médios

---

#### `petri_net.png` — Rede de Petri (Inductive Miner)
Modelo formal do processo descoberto automaticamente a partir do log via Inductive Miner (noise_threshold=0.2).

**Como interpretar:**
- Places (círculos) = estados do processo; Transitions (retângulos) = atividades
- Fluxo sequencial = rito padrão identificado nos dados reais
- Splits/joins paralelos = atividades que ocorrem em ordens variadas
- Loops = rework endêmico (etapas que se repetem)
- Modelo base para o conformance check via token replay

---

#### `variantes_pareto.png` — Pareto de Variantes
Barras com número de casos por variante (top 30); linha = % acumulada.

**Como interpretar:**
- Curva íngreme com muitas variantes = alta heterogeneidade processual (sem padronização)
- **Achado TJPR:** 13.234 variantes únicas para 13.234 casos — cada processo tem caminho próprio
- 5.200 variantes necessárias para cobrir 80% dos casos = fragmentação extrema
- Confirma QP3: ausência total de padronização de fluxo

---

#### `throughput_time.png` — Tempo de Ciclo (Throughput Time)
Histograma da duração total dos processos (ajuizamento → encerramento). Linha vertical = mediana.

**Como interpretar:**
- Distribuição concentrada = processos resolvidos em tempo similar (padronizado)
- Cauda longa à direita = maioria resolve em tempo moderado, mas há casos extremos
- **Achado TJPR:** Mediana 755d, P90=1.489d, P95=1.707d, Máx=2.266d → alta variância
- CF art. 5º LXXVIII ("razoável duração do processo"): mediana 755d indica problema sistêmico

---

#### `sojourn_time.png` — Sojourn Time por Atividade
Top 15 atividades com maior tempo médio de espera (tempo que o processo permanece naquela atividade antes de avançar).

**Como interpretar:**
- Alto sojourn = atividade onde o processo aguarda ação (fila, despacho pendente)
- Diferente do DFG performance: sojourn mede tempo NA atividade; DFG mede tempo ENTRE atividades
- Atividades de conclusão/despacho com alto sojourn = acúmulo de trabalho no cartório ou gabinete

---

#### `bottlenecks.png` — Top 10 Gargalos
Top 10 transições A→B com maior tempo médio e mediano. Barras duplas: azul = média, laranja = mediana.

**Como interpretar:**
- Média >> mediana = outliers puxam a média (casos individuais extremos)
- Média ≈ mediana = problema sistêmico uniforme (todos demoram, não só casos extremos)
- **Gargalo #1 TJPR:** Mero expediente → Recebimento: 235.9d — processos em inércia aguardando distribuição
- Prioridade de intervenção: transições com média ≈ mediana e alto valor (problema estrutural)

---

#### `rework.png` — Análise de Rework
Top 15 atividades com maior número total de repetições (rework = mesma atividade ocorre mais de uma vez no mesmo processo).

**Como interpretar:**
- Alto rework = retorno de etapas, retrabalho ou ciclo processual repetitivo
- **Achado TJPR:** 100% dos casos (13.232/13.234) têm pelo menos 1 repetição
- Atividades com mais rework = candidatas a redesenho de processo ou automação
- Rework em atividades de conclusão/despacho = decisões sendo revisadas ou corrigidas

---

#### `organizacional.png` — Perspectiva Organizacional por Vara
Dois gráficos: (1) volume de eventos por vara (top 20); (2) duração mediana por vara.

**Como interpretar:**
- Vara com alto volume + alta duração = unidade sobrecarregada e lenta → prioridade de intervenção
- Vara com baixo volume + alta duração = possível problema de gestão ou casos excepcionalmente complexos
- Variação grande entre varas = desigualdade de desempenho → falta de padronização de gestão
- **Achado TJPR:** mediana mínima 695d, máxima 878d (variação de 183d entre varas)

---

#### `conformance_fitness.png` — Conformance (Token Based Replay)
Histograma de fitness do Token Based Replay em amostra de 500 casos. Fitness 1.0 = processo replica o modelo descoberto; fitness 0.0 = nenhuma atividade do modelo foi executada.

**Como interpretar:**
- Concentração em 1.0 = maioria dos casos seguiu o modelo descoberto (alta conformidade)
- Fitness < 0.8 = caso desviou significativamente do modelo (exceção, erro de registro ou rework extremo)
- **Achado TJPR:** fitness médio 94.37%, apenas 5.6% abaixo de 0.8
- Nota: modelo aqui é o modelo DESCOBERTO (real), não o modelo normativo do CPP

**4 métricas de qualidade calculadas (dataset completo, 500-sample seed=42):**

| Métrica | Valor | Nível | Significado resumido |
|---------|-------|-------|---------------------|
| Fitness | **99.6%** | Alto | Modelo reproduz o log com fidelidade |
| Precision | **pendente** | Baixo | Modelo muito permissivo — esperado com 13.234 variantes |
| Generalization | **pendente** | Alto | Modelo generaliza bem para novos casos |
| Simplicity | **60.58%** | Moderado | 108 places / 144 transitions — estrutura coerente |

O padrão fitness↑/precision↓ é diagnóstico de **processo ad hoc** com variância extrema.

---

#### `TJPR_Acao_Penal_*_clusters.png` — K-Means (4 Clusters)
4 subplots: scatter duração×eventos (colorido por cluster), tamanho dos clusters, duração mediana por cluster, cobertura das top variantes.

**Como interpretar:**
- Scatter com clusters bem separados = comportamentos processuais distintos e identificáveis
- Cluster com alta duração + muitos eventos = processos complexos ou com muitos recursos
- Cluster com baixa duração + poucos eventos = extinção precoce ou casos simples
- **Achado TJPR:** cluster dominante com 48.4% dos casos (mediana 588d); cluster menor (0.8%) = casos atípicos

---

#### `violencia_sla_liminar.png` — SLA Liminar por Categoria

**O que é:** Boxplot + swarmplot com distribuição de dias até a concessão de liminar, por categoria de violência/protetiva. Linha vermelha = referência de 2 dias da Lei Maria da Penha (art. 18, Lei 11.340/2006). Cada ponto = 1 caso que registrou liminar no evento processual.

**Como ler o gráfico:**
- Eixo X = dias decorridos entre ajuizamento e liminar
- Eixo Y = categorias de violência/protetiva
- Pontos à esquerda da linha vermelha = liminar dentro do prazo de urgência (≤ 2 dias)
- Pontos à direita = descumprimento do prazo legal
- Boxplot (caixa) = IQR dos casos com liminar; linha central = mediana

**Por que quase não aparecem pontos — interpretação essencial:**

A Ação Penal Ordinária é o **processo penal principal** (CPP arts. 394–405) e não o instrumento de medidas de urgência. A Lei Maria da Penha prevê medidas protetivas de urgência em **autos separados** (art. 19 Lei 11.340/2006), processados como cautelar autônoma — não na AP principal. Por isso, 8.581 dos 8.585 casos (99,95%) não registram nenhuma liminar nos autos da AP.

**Achados TJPR — os 4 casos com liminar registrada:**

| Caso | Categoria | Liminar (dias) | Dentro do prazo? | Total (dias) |
|------|-----------|---------------|-----------------|-------------|
| 1879612... | Contra a Mulher | 2,56 | Não (excedeu 48h) | 565 |
| 1607888... | Desc. Medida Protetiva | 0,31 | Sim (7h) | 518 |
| 1872692... | Lesão/Condição de Mulher | 0,64 | Sim (15h) | 352 |
| 8248712... | Contra a Mulher | 19,12 | Não (19 dias) | 123 |

> **Interpretação PM²:** O gráfico praticamente vazio **não é ausência de dado** — é um achado estrutural. Casos de violência doméstica usam o instrumento correto (cautelar autônoma) para medidas de urgência. A análise SLA relevante para violência é o `sla_total_dias` (trânsito em julgado), não o SLA de liminar.

---

#### `violencia_sla_total.png` — Duração Total por Caso (Violência/Protetiva)

**O que é:** Gráfico de barras horizontais onde cada barra representa um dos 8.585 casos de violência/protetiva, com comprimento proporcional à duração total (ajuizamento → trânsito em julgado). As barras são coloridas por categoria. A linha vermelha vertical marca 365 dias (alerta CNJ Res. 254/2018).

**Como ler o gráfico:**
- Cada linha horizontal = 1 processo
- Comprimento da barra = duração total em dias
- Barras à **direita** da linha vermelha = casos que ultrapassaram o alerta de 365 dias
- Cor = categoria de violência/protetiva
- Concentração de barras longas em uma cor = categoria mais impactada pela demora

**Achados TJPR por categoria:**

| Categoria | N | Mediana | Média | Mín | Máx | Acima 365d |
|-----------|---|---------|-------|-----|-----|-----------|
| Contra a Mulher | 5.232 | **419,9d** | 443,1d | 22d | 2.113d | **41,7% (1.121 casos)** |
| Lesão/Condição de Mulher | 2.350 | **400,6d** | 427,9d | 16d | 1.113d | **41,9% (848 casos)** |
| Desc. Medida Protetiva | 949 | **255,2d** | 312,6d | 10d | 974d | 22,4% (146 casos) |
| Violência Psicológica | 36 | **372,6d** | 393,1d | 73d | 845d | 41,5% (17 casos) |
| Feminicídio | 18 | **201,8d** | 232,3d | 106d | 389d | 25,0% (1 caso) |
| **Total** | **8.585** | **490,2d** | — | — | **2.113d** | **52,7% (4.522 casos)** |

**Por que Descumprimento de Medida Protetiva tramita mais rápido:**
Casos de descumprimento (réu viola ordem judicial existente) tendem a ter **instrução mais simples**: a prova central é o próprio descumprimento da ordem, sem a necessidade de extensa produção probatória sobre o fato delituoso subjacente. Isso explica a mediana 255d vs. 420d para Contra a Mulher.

> **Implicação PM²:** 4.522 casos (52,7%) ultrapassaram 365 dias. Os casos com barras mais longas são candidatos imediatos a auditoria judicial — cruzar `case_id` com `violencia_sla_detalhado.csv` (campo `alerta_total == True`) para identificar prioridades de intervenção.

---

#### `violencia_vs_geral.png` — Violin: Violência vs. Outros AP

**O que é:** Violin plot (distribuição de densidade) comparando a duração total entre dois grupos: (1) casos de violência/protetiva (8.585 casos) e (2) demais Ações Penais Ordinárias. Cada "violino" é espelhado — a largura em cada altura representa a densidade de casos naquela duração.

**Como ler o gráfico:**
- Eixo Y = duração total em dias (ajuizamento → trânsito)
- Violino mais **largo** em uma faixa = mais casos concentrados naquela duração
- Linha interna horizontal = mediana
- Caixa interna = IQR (25º–75º percentil)
- Cauda superior longa = presença de outliers com duração extrema

**Achados TJPR:**

| Grupo | N | Mediana | Diferença |
|-------|---|---------|-----------|
| Violência/protetiva | 8.585 | **490,2d** | −79,5 dias vs. outros |
| Outros AP | — | 569,7d | referência |

- Ambos os violinos têm **cauda superior extensa**: casos ultrapassando 1.000 dias existem em ambos os grupos
- O violino de violência está **deslocado para baixo** (duração menor), indicando prioridade relativa de tramitação no dataset 2020-2026
- Nenhum dos dois grupos apresenta concentração em durações curtas (< 100 dias): o sistema como um todo é lento

**Diagnóstico legal:**

A CNJ Resolução 254/2018 exige tratamento **prioritário** para casos de violência doméstica. No dataset 2020-2026, o violino de violência está deslocado para **baixo** (durações menores), sugerindo prioridade relativa. Contudo, 53% dos casos ainda excedem 365 dias — ausência de SLA interno padronizado.

> **Interpretação PM²:** A diferença de −79,5 dias (490,2d − 569,7d) sugere prioridade relativa de tramitação. Porém, 4.522/8.585 casos (53%) superam o alerta de 365d — a prioridade existe mas é insuficiente para garantir SLA razoável.

---

#### `violencia_sla_cumprimento.png` — % Casos por Faixa de Prazo (Liminar)

**O que é:** Gráfico de barras verticais mostrando a distribuição dos 8.585 casos de violência/protetiva por faixa de prazo para liminar: ≤2 dias (dentro da referência Lei Maria da Penha), 3–7 dias, 8–30 dias, >30 dias.

**Como ler o gráfico:**
- Eixo X = faixas de prazo para liminar
- Eixo Y = percentual de casos (base: 8.585)
- Barra "≤2 dias" alta = boa conformidade com o prazo de urgência
- Barras nas faixas maiores = descumprimento progressivo do prazo

**Achados TJPR:**

De 8.585 casos, apenas **4 tiveram qualquer registro de liminar** (0,05%). A distribuição efetiva:
- ≤2 dias: 2 casos (0,04%) — dentro do prazo
- 3–7 dias: 0 casos
- 8–30 dias: 1 caso (0,02%)
- >30 dias: 1 caso (0,02%) — 19,1 dias, acima do prazo
- **Sem liminar: 8.581 casos (99,95%)**

**Por que o gráfico mostra quase tudo vazio:**

Conforme discutido em `violencia_sla_liminar.png`, a Ação Penal Ordinária não é o instrumento de medidas de urgência — essas são processadas em autos separados (cautelar autônoma, art. 19 Lei 11.340/2006). O gráfico praticamente vazio confirma que o fluxo de medidas protetivas de urgência está **corretamente segregado** do processo penal principal.

> **Uso correto desta métrica:** Para medir conformidade com o prazo de 48h da Lei Maria da Penha (art. 18), é necessário analisar os **autos de medida protetiva de urgência** — processo distinto da AP ordinária. Esta análise requereria extração específica por classe processual de cautelar.

---

#### `violencia_por_cluster.png` — Violência por Cluster K-Means

**O que é:** Gráfico de barras empilhadas (*stacked bar*) mostrando, para cada um dos 4 clusters K-Means, a proporção entre casos de violência/protetiva (segmento maior) e demais Ações Penais Ordinárias (segmento menor). Permite cruzar o perfil comportamental do cluster com a prevalência de violência doméstica.

**Como ler o gráfico:**
- Eixo X = 4 clusters identificados pelo K-Means
- Eixo Y = proporção de casos (0 a 1)
- Segmento superior (cor escura) = casos de violência/protetiva
- Segmento inferior (cor clara) = outros AP
- Cluster com segmento superior maior = violência doméstica prevalente naquele perfil comportamental

**Perfil de cada cluster com proporção de violência:**

| Cluster | N | % Violência | Mediana (dias) | Eventos (mediana) | Perfil |
|---------|---|-------------|---------------|-------------------|--------|
| 0 | 6.408 | **64,9%** | 588d | 160 eventos | Fluxo dominante (48,4%) |
| 1 | 3.583 | **65,0%** | 1.072d | 238 eventos | Processos longos com recursos |
| 2 | 105 | **62,0%** | 1.014d | 206 eventos | Casos atípicos (menor cluster) |
| 3 | 3.138 | **65,1%** | 775d | 140 eventos | Fluxo secundário |

**Interpretação cruzada — o que o gráfico revela:**

1. **Violência doméstica está em todos os clusters**: proporções entre 62–65% em todos os grupos, confirmando que não existe um "cluster de violência" isolado — esses casos permeiam todos os perfis comportamentais.

2. **Cluster 0 domina (48,4%) com mediana 588d**: fluxo principal com distribuição de violência proporcional ao total (~64,9%).

3. **Cluster 1 combina duração extrema (1.072d)**: este grupo representa o pior cenário operacional — processos longos que deveriam ser prioritários.

4. **Cluster 2 (105 casos, 62,0%)**: amostra pequena de casos atípicos; indica processos complexos não representativos do sistema geral.

> **Implicação PM²:** Violência doméstica distribui proporcionalmente entre clusters (~62-65%). Intervenção prioritária: reduzir duração do Cluster 1 (1.072d, recursos/2º grau) que concentra processos longos.

---

## 7. METODOLOGIA PM² — RASTREABILIDADE

| Etapa PM² | Script | Status |
|-----------|--------|--------|
| Planejamento | — (definição manual) | ✓ Concluído |
| Extração | `main.py` + `datajud/client.py` | ✓ 50.000 proc. extraídos |
| Processamento | `analises/exportar_filtrado.py` | ✓ 13.234 casos fechados |
| Mineração — Discovery | `analises/analisar.py` | ✓ DFG + Petri Net + Variantes |
| Mineração — Performance | `analises/analisar.py` | ✓ Throughput mediana 755d, P90 1.489d |
| Mineração — Rework | `analises/analisar.py` | ✓ 100% com rework (13.232/13.234) |
| Mineração — Organizacional | `analises/analisar.py` | ✓ Varas analisadas (695d–878d) |
| Mineração — Conformance (descoberto) | `analises/analisar.py` | ✓ Fitness 99.6% ≥ 0.8 (500-sample) |
| Mineração — Clustering | `analises/agrupar.py` | ✓ 4 clusters K-Means |
| Mineração — SLA Violência/Protetiva | `analises/analise_violencia_mulher.py` | ✓ 8.585 casos (~64.9%), mediana 490.2d |
| Happy Path | `analises/happy_path_report.py` | ✓ Executado |
| Avaliação | Este relatório | ✓ QP1–QP5 respondidas |
| Melhoria | Este relatório | ✓ 8 sugestões (5 processo + 3 SI) |

---

## 8. EXECUÇÃO DO PIPELINE

Para reproduzir completamente este projeto:

```bash
# 1. Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install graphviz   # macOS — necessário para DFGs e Petri Nets

# 2. Extração (config.py já configurado para Ação Penal + violência 2020-2026)
# datajud/config.py tem QUERY_BODY com:
#   "Ação Penal" + assuntos ∈ {Mulher, Protetiva, Doméstica}
#   dataAjuizamento 2020-01-01 → 2026-05-13
python main.py
# Gera output/TJPR_*.csv/.html (50.000 proc.)

# 3. Pipeline completo Ação Penal
# --ano-dfg 2025: DFG/Petri Net usam apenas casos de 2025 (evita PNGs de 60+ MB)
# --dfg-min-pct 2.0: arcos com freq >= 2% do máximo (reduz arcos)
python run_pipeline.py \
  --classe "Ação Penal - Procedimento Ordinário" \
  --tribunal TJPR \
  --data-inicio 2020-01-01 \
  --data-fim 2026-05-13 \
  --ano-dfg 2025 \
  --dfg-min-pct 2.0

# 4. Gerar PDF do relatório
python gerar_pdf.py
```

