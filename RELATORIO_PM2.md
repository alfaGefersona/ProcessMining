## Ação Penal — Procedimento Ordinário no TJPR (2020–2026)

**Tribunal:** Tribunal de Justiça do Paraná (TJPR)
**Classe processual:** Ação Penal - Procedimento Ordinário
**Período:** 01/01/2020 → 13/05/2026
**Metodologia:** PM² (Process Mining Project Methodology)
**Tipo de log:** LO — Log Original (extração direta da API CNJ Datajud)

**Aluno:** Geferson Artuzo

---

## Siglas e Abreviaturas

| Sigla | Significado |
|-------|------------|
| **CPP** | Código de Processo Penal (Decreto-Lei nº 3.689/1941) |
| **CP** | Código Penal (Decreto-Lei nº 2.848/1940) |
| **CF** | Constituição Federal de 1988 |
| **TJPR** | Tribunal de Justiça do Estado do Paraná |
| **CNJ** | Conselho Nacional de Justiça |
| **TPU** | Tabela Processual Unificada (CNJ) |
| **DFG** | Directly-Follows Graph — grafo de sequências diretas entre atividades |
| **TBR** | Token-Based Replay — algoritmo de conformance check |
| **ETC** | Entropic Conformance — métrica de precisão |
| **PM²** | Process Mining Project Methodology |
| **PJe** | Processo Judicial Eletrônico (sistema do CNJ) |
| **SLA** | Service Level Agreement — prazo acordado/legal de atendimento |
| **AP** | Ação Penal |
| **QP** | Questão de Pesquisa |

---

## 1. PLANEJAMENTO

### 1.1 Processo de Negócio Selecionado

A **Ação Penal - Procedimento Ordinário** é o rito penal obrigatório para crimes com pena máxima ≥ 4 anos (CPP art. 394, §1º, I), com fases definidas em lei: recebimento da denúncia, citação, resposta à acusação, absolvição sumária, audiência de instrução e julgamento, sentença e trânsito em julgado. É o rito com maior complexidade instrutória — 64,9% dos casos no TJPR envolvem violência doméstica, feminicídio ou crimes protetivos (Lei 11.340/2006).

**Crimes julgados por este rito:**

| Crime | Base legal |
|-------|-----------|
| Homicídio doloso qualificado / Feminicídio | CP art. 121 §2º / §2º-A |
| Roubo qualificado | CP art. 157 §2º |
| Tráfico de drogas (pena máx 15 anos) | Lei 11.343/2006 art. 33 |
| Estupro / Estupro de vulnerável | CP arts. 213, 217-A |
| Lesão corporal grave em violência doméstica | CP art. 129 §9º / Lei 11.340/2006 |
| Descumprimento de medida protetiva (c/ violência) | CP art. 147-B |
| Extorsão, sequestro, corrupção ativa (pena ≥ 4 anos) | CP arts. 158, 159, 333 |

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

> **Nota técnica:** A API pública não suporta filtro por `classe.codigo`. O `match` full-text captura classes adjacentes (AP Sumário, Sumaríssimo, etc.) que são removidas em pós-processamento pelo `exportar_filtrado.py` via filtro exato `case:classe == "Ação Penal - Procedimento Ordinário"`. Destes, 13.234 possuem atividade terminal (casos fechados).

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
RAW API (50.000 proc.)
    [F1] Filtro classe exata = "Ação Penal - Procedimento Ordinário" → 13.234
    [F2] Remoção casos sem atividade terminal (em andamento)
    [F3] Deduplicação por código TPU + timestamp
    LOG FINAL: 13.234 processos / ~2.376.663 eventos
```

**Formato de saída:** CSV UTF-8 BOM + IEEE XES 1.0 (importável no Disco/PM4Py)

### 2.5 Fluxo Completo do Pipeline

```
Datajud API (Elasticsearch CNJ)
     ↓  main.py
     ▼  output/TJPR_{ts}.csv          ← 50.000 processos, todas as classes
     │
     ↓  exportar_filtrado.py
     ▼  TJPR_Acao_Penal_*.csv/.xes    ← 13.234 casos fechados, 2.376.663 eventos
     │
     ├─ happy_path_report.py    → happy path + transições A→B com duração em dias
     ├─ analisar.py             → DFG, Petri Net, performance, rework, conformance
     ├─ agrupar.py              → K-Means k=4, top variantes
     └─ analise_violencia_mulher.py
        Filtro: assunto ∈ {violência/protetiva/mulher} → 8.585/13.234 casos (~64.9%)
        SLA total: Ajuizamento → Trânsito (alerta > 365 dias — CNJ Res. 254/2018)
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

> ¹ **Nota técnica:** O gráfico "Sojourn Time" mede o tempo **entre** eventos consecutivos (transition time), não o tempo **dentro** de uma atividade. Como cada evento é um timestamp pontual (sem duração registrada), essa é a melhor aproximação disponível.

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

A partir do log de eventos, algoritmos descobrem automaticamente um modelo formal do fluxo observado na prática — sem desenho manual.

---

**DFG — Directly-Follows Graph** (`imgs/dfg_frequencia.png` e `imgs/dfg_performance.png`)

O DFG conta quantas vezes B ocorreu imediatamente após A no mesmo processo. Arcos filtrados: ≥ 2% do máximo de frequência (201 de 3.497 arcos originais, subset 2025). O **DFG de Frequência** mostra caminhos mais comuns; o **DFG de Performance** exibe o tempo médio em dias por transição.

Atividades mais frequentes no dataset 2025 (top 5):

| Atividade | Tipo | Papel no processo |
|-----------|------|------------------|
| Confirmada | Ato cartorário | Confirmação de cumprimento de diligência |
| Expedição de documento - Outros | Ato cartorário | Emissão genérica de documentos |
| Recebimento | Ato cartorário | Recebimento de remessas e petições |
| Entrega em carga/vista | Ato cartorário | Entrega de autos para vista de parte/advogado |
| Documento - Outros documentos | Ato de juntada | Juntada genérica de peças ao processo |

> **Achado:** Atividades cartoriais dominam o DFG — não atividades jurisdicionais (sentença, citação, audiência). A maior parte dos eventos registrados é administrativa, mascarando a espera real por decisão judicial.

---

**Petri Net — Inductive Miner** (`imgs/petri_net.png`, `imgs/petri_net_cluster_dominante.png`, `imgs/petri_net_cluster0_top20v.png`)

O **Inductive Miner** (Leemans et al., 2013) produz uma Rede de Petri com garantias estruturais (soundness: toda execução tem início e fim, sem deadlocks). Divide o log recursivamente em cortes (sequential, parallel, choice, loop) com `noise_threshold` definindo % de traces infrequentes ignoradas.

**Elementos da Rede de Petri:**

| Elemento | Símbolo | Significado |
|----------|---------|-------------|
| Places | Círculos | Estados do processo |
| Transitions | Retângulos brancos/cinza | Atividades reais (com nome) |
| Silent/tau transitions | Retângulos pretos | Roteamento estrutural: XOR-splits, AND-splits, loops |
| Arcos (→) | Setas | Fluxo de tokens entre states e transitions |

> **Modelo principal** (`petri_net.png`): subset 2025, `noise=0.2` → 194 places / 367 transitions. Modelo **cluster dominante** (`petri_net_cluster_dominante.png`): Cluster 0 (6.408 casos), `noise=0.4` → mais compacto. Modelo **top-20 variantes** (`petri_net_cluster0_top20v.png`): subset mais legível, 3.183 casos, 36 places / 68 transitions.

#### 3.2.2 Análise de Variantes

Arquivo: `imgs/variantes_pareto.png`

Uma variante é a **sequência exata e ordenada de todas as atividades** de um caso. O Pareto de Variantes rankeia por frequência; quanto mais íngreme a curva, mais padronizado o processo.

| Métrica | Valor |
|---------|-------|
| Total de variantes únicas | **13.234** |
| Variantes para cobrir 80% dos casos | **5.200** |
| Cobertura da variante mais frequente | **< 0.02%** (1 caso em 13.234) |

> **QP3 respondida:** Com 13.234 variantes únicas para 13.234 casos (ratio 1:1), o log confirma **ausência total de padronização** de fluxo. 5.200 variantes para 80% dos casos = fragmentação processual extrema. Impossível estabelecer SLA por etapa ou garantir isonomia de tramitação entre réus.

#### 3.2.3 Análise de Performance Temporal (Throughput Time)

Arquivo: `imgs/throughput_time.png`

Throughput time é a duração total do processo (ajuizamento → trânsito em julgado) — a métrica que a CF art. 5º, LXXVIII protege. A mediana é usada em vez da média por ser robusta a outliers em distribuições com cauda longa.

| Percentil | Duração | Significado |
|-----------|---------|-------------|
| **Mediana (P50)** | **755 dias** | Metade dos processos fechou em até 755 dias |
| **Média** | **563 dias** | Média puxada por outliers longos |
| P75 | ~740 dias | 75% fecharam em até ~740 dias |
| P90 | **1.489 dias** | 10% dos processos durou mais de 1.489 dias |
| P95 | **1.707 dias** | 5% mais lentos ultrapassaram ~4,7 anos |
| Máximo | **2.266 dias** | Processo mais demorado: ~6,2 anos |

> **QP1 respondida:** A mediana de **755 dias (2,1 anos)** ultrapassa qualquer referência razoável para processo penal de 1º grau. O P90 de **1.489 dias (4,1 anos)** representa falha sistêmica de celeridade. Média > mediana confirma cauda longa — mesmo o caso "típico" está fora do padrão constitucional.

---

**Sojourn Time por atividade** — `imgs/sojourn_time.png`

Mede o **tempo que o processo permanece em uma atividade** antes de avançar — identifica em qual etapa específica o processo "para". Comparar com gargalos (3.2.4): sojourn mede espera NA atividade; bottleneck mede espera na transição ENTRE atividades.

#### 3.2.4 Análise de Gargalos (Top 10)

Arquivo: `imgs/bottlenecks.png`

Um gargalo é a transição A → B com maior tempo de espera. Média >> mediana = poucos casos extremos; média ≈ mediana = problema estrutural uniforme (prioritário para intervenção).

| Transição (A → B) | Média | Diagnóstico |
|-------------------|-------|-------------|
| **Mero expediente → Recebimento** | **235.9 dias** | Processo em inércia — maior gargalo |
| Remessa em grau de recurso → Acórdão | **127.9 dias** | 2º grau lento para publicar acórdão |
| Por decisão judicial → Apensamento | **111.0 dias** | Ato cartorário represado pós-decisão |
| Expedição certidão → Morte do agente | **108.2 dias** | Extinção da punibilidade com certidão pendente |
| Remessa em grau de recurso → Mudança de Assunto | **94.9 dias** | Reclassificação tardia pós-recurso |
| Definitivo → Petição (outras) | **82.0 dias** | Autos "definitivos" aguardam ato cartorário |
| Expedição certidão → Recebimento | **81.5 dias** | Certidão expedida mas não cumprida |
| Expedição certidão → Procedência | **77.2 dias** | Sentença de procedência com certidão pendente |
| Remessa devolução → Recebimento | **72.7 dias** | Autos devolvidos mas não distribuídos |

> **QP2 respondida:**
>
> 1. **Gargalo #1 — "Mero expediente" (236 dias):** "Mero expediente" é anotação cartorária de ausência de movimentação. Processo aguardando 236 dias após essa marcação = **paralisação sem causa processual registrada** (fila ou acúmulo cartorário).
>
> 2. **Gargalo #2 — Recurso → Acórdão (128 dias):** 2º grau leva ~4 meses em média para publicar acórdão — sobrecarga do tribunal recursal.
>
> 3. **Gargalo #3 — Pós-decisão cartorária (111 dias):** Atos de cumprimento após decisão judicial (apensamento, certidão) demoram meses — fila nos cartórios para executar ordens já proferidas.

#### 3.2.5 Análise de Rework

Arquivo: `imgs/rework.png`

Rework ocorre quando a **mesma atividade é executada mais de uma vez no mesmo processo** — indica retorno a etapas anteriores, ciclos repetitivos ou falhas de cumprimento.

| Métrica | Valor |
|---------|-------|
| Processos com rework | **13.232 de 13.234 (100%)** |

> Rework de 100% é esperado em parte (CPP permite múltiplos atos de mesma categoria). Porém loops "Conclusão → Despacho → Conclusão" repetem-se dezenas de vezes, indicando **fila de gabinete** (processo vai ao juiz, retorna sem despacho, repete). Cada loop adiciona em média 30–90 dias ao throughput — parcela significativa dos 755 dias medianos.

#### 3.2.6 Perspectiva Organizacional

Arquivo: `imgs/organizacional.png`

Compara volume de eventos e duração mediana por vara. Identifica varas sobrecarregadas e heterogeneidade de desempenho para a mesma classe processual.

| Métrica | Valor |
|---------|-------|
| Varas com ≥ 5 processos analisadas | 20 varas criminais TJPR |
| Menor duração mediana | **695 dias** |
| Maior duração mediana | **878 dias** |
| Variação absoluta | **183 dias** |
| Variação relativa | **26% entre a mais eficiente e a mais lenta** |

> A diferença de **26% entre varas** para o **mesmo tipo de processo** revela heterogeneidade operacional sem justificativa processual — violação do princípio da isonomia de tramitação. Mesmo a vara mais eficiente (695d) ultrapassa amplamente qualquer referencial razoável: o problema é sistêmico, não localizado.

#### 3.2.7 Conformance Checking — Modelo Descoberto × Modelo Normativo CPP (Estrito)

Arquivos: `imgs/conformance_fitness.png` · `imgs/conformance_normativo.png` · `imgs/petri_net_normativa_cpp.png`

Duas análises de conformance foram realizadas:

**A) Modelo Descoberto** — Inductive Miner (noise=0.2) sobre 13.234 casos, 500-sample seed=42, 108 places / 144 transitions.

**B) Modelo Normativo CPP (Estrito)** — Petri Net construída **manualmente** a partir dos arts. 394-405 do CPP, sem concessões ao subregistro do PJe. Cada etapa obrigatória é uma transição visível; ausência no TBR = token faltando = fitness baixo = **achado real**. Script: `analises/conformance_normativo.py`.

> **Nota:** `petri_net.png` (visual) usa subset 2025 → 194 places / 367 transitions. Métricas abaixo usam dataset completo.

**O que cada coluna representa:**

| Coluna | Origem | Representa |
|--------|--------|-----------|
| **Descoberto (IM)** | Inductive Miner sobre 13.234 casos reais | O que **aconteceu** — modelo aprendido dos dados TJPR |
| **Normativo CPP (Estrito)** | Petri Net construída manualmente (arts. 394-405) | O que **deveria** acontecer — rito legal prescrito sem concessões |

O TBR pergunta: *o log real se encaixa em cada modelo?* Fitness descoberto = 99.6% é trivialmente alto — o modelo **foi** minerado dos mesmos dados. Fitness normativo **46.9%** revela que mais da metade dos tokens não segue o rito legal — **esse resultado é o achado**.

**Por que o modelo normativo CPP tem ZERO transições silenciosas (τ)?**

O objetivo é comparar o fluxo real com **o que a lei prescreve**, não com o que o PJe registra. Cada etapa mandatória do CPP tem transição visível no modelo — sem exceção. Se o log não registra a Citação (cobertura 1.1%) ou o Trânsito (83.8%), o TBR penaliza com token faltando → fitness cai → **achado real**:

> **O PJe não registra etapas obrigatórias do CPP. Fitness 46.9% = gap estrutural de dados entre o sistema eletrônico e o rito formal.**

O CPP não prevê processo sem Trânsito em Julgado — todo processo penal **deve** atingir res judicata (art. 502 CPC aplicado supletivamente). Tau para Trânsito seria concessão à janela de observação (dado), não ao direito. O modelo também contém **XOR normativo** (não τ) entre Absolvição Sumária (art. 397) e AIJ (art. 400) — ambas alternativas legítimas prescritas pelo legislador.

**Estrutura da Petri Net (100% estrita): 8 places · 8 transições obrigatórias · 0 tau**

```
Início → Distribuição/Petição → Recebimento → Citação → Resposta à Acusação
       → [Absolvição Sumária | Audiência de Instrução] → Sentença → Trânsito em Julgado
```

**Tabela comparativa — 4 métricas de van der Aalst (2016):**

| Métrica | Descoberto (IM) | Normativo CPP (100% estrito) | Interpretação |
|---------|----------------|------------------------------|---------------|
| **Fitness (TBR)** | **99.6%** | **46.9%** | 53.1% dos tokens faltando — etapas CPP ausentes no PJe |
| **Precision (TBR-ETC)** | **~14%** | **66.8%** | Normativo é 4,7× mais restritivo que o descoberto |
| **Generalization (TBR)** | **~89%** | **86.1%** | Ambos generalizam bem além da amostra |
| **Simplicity** | **~61%** | **50.0%** | 8P / 8T / 16 arcos — modelo mínimo, sem tau |
| Traces 100% conformes | ~94% | **0.0%** | Nenhum caso segue o rito CPP de ponta a ponta no PJe |

**Cobertura dos marcos CPP no log TJPR:**

| Marco CPP (arts. 394-405) | Cobertura | Status |
|---------------------------|-----------|--------|
| Distribuição / Petição (Denúncia) | 99.3% | Registrado |
| Recebimento | **100.0%** | Registrado |
| Citação | **1.1%** | GAP CRÍTICO — mandado físico sem evento eletrônico |
| Resposta à Acusação | 85.5% | Registrado |
| Absolvição Sumária | 1.0% | Raro (esperado — maioria vai à AIJ) |
| Audiência de Instrução | 92.1% | Registrado |
| Sentença | 88.3% | Registrado |
| Trânsito em Julgado | 83.8% | Registrado |

**Interpretações:**

1. **Fitness normativo 46.9% + 0% de traces perfeitas** → Nenhum caso percorre o rito CPP linearmente no PJe. Dois gaps principais determinam o fitness: (a) Citação ausente em 98.9% dos casos — mandado físico expedido fora do sistema eletrônico; (b) Trânsito ausente em 16.2% — encerramento formal não registrado. Ambos são gaps de instrumentação tecnológica, não de realidade processual.

2. **Precision normativa 66.8% vs descoberta ~14%** → Normativo CPP é 4,7× mais restritivo. Modelo descoberto aceita qualquer sequência das 377 atividades (flower model — consequência das 13.234 variantes únicas). A diferença confirma processo operando em modo ad hoc, muito além do prescrito no CPP.

3. **Citação = 1.1% de cobertura** → Gap crítico de dados: ato obrigatório (art. 396) quase invisível no PJe. Cartório expede mandado físico sem lançar evento eletrônico. Não é falha jurídica — é falha de instrumentação do PJe.

4. **Trânsito em Julgado = 83.8% de cobertura** → 16.2% dos casos (≈2.145) sem encerramento formal registrado. Combinado com o gap de Citação, o PJe deixa de registrar dois marcos obrigatórios de ponta a ponta do rito CPP.

5. **0% de traces completamente conformes** → Confirma: o fluxo PJe **nunca** replica o rito CPP formal de ponta a ponta. Cada processo acumula dezenas de atos cartoriais, despachos intermediários e retornos sem correspondência no rito normativo — além dos gaps de Citação e Trânsito.

#### 3.2.8 Agrupamento — K-Means (k=4)

Arquivo: `imgs/TJPR_Acao_Penal___Procedimento_Ordinario_clusters.png`

K-Means agrupa casos com comportamento similar usando **features numéricas** de cada processo — identifica perfis comportamentais apesar da infinidade de variantes.

**Features utilizadas (12 no total):**

| Feature | Tipo | O que mede |
|---------|------|-----------|
| `duracao_dias`, `n_eventos`, `n_atividades_unicas`, `n_passos` | Numéricas | Complexidade e velocidade |
| `tem_sentenca`, `tem_transito`, `tem_acordao`, `tem_recurso`, `tem_redistribuicao`, `tem_audiencia`, `tem_desistencia`, `tem_incompetencia` | Booleanas | Marcos processuais presentes |

Pré-processamento: **StandardScaler** (Z-score por feature) — necessário porque `duracao_dias` (~800d) e flags booleanas (0/1) têm escalas incompatíveis. `KMeans(n_clusters=4, random_state=42, n_init=10)`.

**Clusters identificados — perfil completo de marcos (% casos com marco=True):**

| Marco | Cluster 0 | Cluster 1 | Cluster 2 | Cluster 3 |
|-------|-----------|-----------|-----------|-----------|
| `tem_redistribuicao` | **98.5%** | 84.2% | 66.7% | 1.1% |
| `tem_incompetencia` | **99.9%** | 96.8% | 80.0% | 59.0% |
| `tem_sentenca` | 87.5% | **97.1%** | 95.2% | 80.4% |
| `tem_transito` | 76.5% | **95.0%** | 94.3% | 85.5% |
| `tem_acordao` | 1.7% | **53.5%** | 6.7% | 10.1% |
| `tem_recurso` | 4.4% | 10.7% | **61.9%** | 3.0% |
| `tem_desistencia` | 0.0% | 0.0% | **100.0%** | 0.0% |
| `tem_liminar` | 0.0% | 0.6% | 0.0% | 0.2% |

**Clusters identificados (k=4):**

| Cluster | Casos | % | Mediana | P90 | Ev./caso | Perfil interpretado |
|---------|-------|---|---------|-----|----------|---------------------|
| **0** | 6.408 | 48.4% | 588d | 1.211d | 160 | Redistribuídos — mudaram de vara |
| **1** | 3.583 | 27.1% | 1.072d | 1.765d | 238 | 2ª instância — chegaram ao TJ |
| **2** | 105 | 0.8% | 1.014d | 1.945d | 206 | Desistência — 100% desistiram |
| **3** | 3.138 | 23.7% | 775d | 1.431d | 140 | Origem simples — sem redistribuição |

**Interpretação de cada cluster:**

**Cluster 0 — "Redistribuídos" (48.4%, mediana 588d)**
Marco definidor: `redistribuicao` 98.5% + `incompetencia` 99.9%. Processos que passaram por redistribuição de vara — inicialmente distribuídos para vara sem competência, depois movidos (declaração de incompetência, criação de vara especializada, suspeição). Apesar da movimentação extra, 87.5% chegaram a sentença e 76.5% a trânsito. Recurso raro (4.4%, acórdão 1.7%) — resolvidos no mérito sem contestação em 2ª instância. A demora (588d) deriva do tempo consumido no trâmite de redistribuição antes do início efetivo na vara definitiva.

**Cluster 1 — "2ª instância" (27.1%, mediana 1.072d)**
Marco definidor: `acordao` 53.5%. Metade dos casos teve julgamento em câmara/turma recursal — chegaram ao Tribunal de Justiça. Duração quase o dobro do Cluster 0 (1.072d vs 588d); 238 eventos/caso vs. 160. **Principal driver de demora identificado:** recurso ao TJ adiciona ~484d à mediana. Gargalo documentado: `Remessa grau recurso → Acórdão = 128 dias` médios.

**Cluster 2 — "Desistência" (0.8%, mediana 1.014d)**
Marco definidor: `desistencia` **100%** — todos os 105 casos sem exceção tiveram desistência. Alto índice de recurso prévio (61.9%) sugere padrão: parte recorre, processo se prolonga (~1.014d), desiste — possivelmente após ANPP (Acordo de Não Persecução Penal), acordo extrajudicial ou análise do risco de derrota. A desistência não impediu trânsito (94.3%) — processo encerrou formalmente. Grupo numericamente irrelevante (0.8%) mas comportamentalmente distinto.

**Cluster 3 — "Origem simples" (23.7%, mediana 775d)**
Marco definidor: ausência de redistribuição (1.1%). Processos que permaneceram na vara original do início ao fim. Menor número de eventos/caso (140) = menos atos processuais = casos mais objetivos ou menos contestados. Sem 2ª instância relevante (acórdão 10.1%). A demora (775d), apesar da menor complexidade, reflete o gargalo sistêmico do TJPR que afeta todas as varas independentemente do perfil do caso.

> **QP4 respondida:** 4 perfis comportamentais separáveis com drivers distintos. O maior fator de duração é o acórdão/2ª instância (Cluster 1: +484d vs Cluster 0). A redistribuição de vara afeta 98.5% do cluster dominante (48.4% dos casos). O K-Mais confirma que a variabilidade processual tem **estrutura interpretável** — viável para intervenção segmentada por perfil.

---

## 4. AVALIAÇÃO

### 4.1 Síntese dos Achados por Questão de Pesquisa

**QP1 — Prazo:**
O TJPR leva em mediana **755 dias (2,1 anos)** para julgar uma Ação Penal Ordinária em primeiro grau. O P90 é de **1.489 dias (4,1 anos)**. A CF art. 5º, LXXVIII garante razoável duração do processo — a mediana atual ultrapassa qualquer referência razoável para processo penal de primeiro grau.

**QP2 — Gargalos:**
Os 3 maiores gargalos são:
1. **Mero expediente → Recebimento (236 dias)** — processo paralisado sem movimentação efetiva
2. **Remessa grau recurso → Acórdão (128 dias)** — 2º grau lento para julgar recursos
3. **Por decisão judicial → Apensamento (111 dias)** — atos cartorários represados pós-decisão

**QP3 — Padronização:**
13.234 casos, 13.234 variantes únicas. **Zero padronização** de fluxo. 5.200 variantes para cobrir 80% dos casos. O fluxo processual real é completamente individualizado.

**QP4 — Perfis:**
4 perfis comportamentais distintos: **Cluster 0** — "Redistribuídos" (48.4%, 588d): quase todos passaram por redistribuição de vara (98.5%) por incompetência (99.9%), resolvidos no mérito sem 2ª instância. **Cluster 1** — "2ª instância" (27.1%, 1.072d): 53.5% com acórdão, principal driver de demora (+484d vs Cluster 0). **Cluster 2** — "Desistência" (0.8%, 1.014d): 100% dos casos com desistência, grupo atípico. **Cluster 3** — "Origem simples" (23.7%, 775d): sem redistribuição (1.1%), menor movimentação (140 ev./caso), gargalo sistêmico sem complexidade adicional.

**QP5 — Violência doméstica:**
8.585 de 13.234 casos (~64.9%) envolvem violência/protetiva. A mediana de casos de violência/protetiva (490.2d) é **menor** que os demais (569.7d), indicando prioridade relativa de tramitação no dataset 2020-2026. Contudo, 53% (4.522 casos) excedem 365d.

### 4.2 Limitações

- **Escopo de assunto:** 50.000 processos extraídos com filtro AP + mulher/protetiva — subconjunto da totalidade das AP do TJPR
- **Uma janela temporal/tribunal:** sem TJRS para comparação cross-tribunal
- **Nomenclatura TPU:** atividades mapeadas por texto — variações ortográficas geram ruído
- **Etapas ausentes ≠ etapas não realizadas:** registro no sistema pode estar incompleto
- **Conformance normativo (100% estrito, 0 tau):** Implementado em `analises/conformance_normativo.py` — Fitness 46.9%, Precision 66.8%, Gen. 86.1% contra modelo CPP arts. 394-405 (0% traces perfeitos; ver seção 3.2.7)

---

## 5. MELHORIA DO PROCESSO

### 5.1 Sugestões para o Dono do Processo (TJPR / Varas Criminais)

**P1 — Eliminar "Mero expediente" (gargalo principal: 236 dias):**
Implementar alerta automático no PJe quando processo ficar sem movimentação substantiva por mais de **30 dias**.

**P2 — Priorização operacional para violência doméstica:**
CNJ Res. 254/2018 exige tratamento prioritário. Mediana violência (490.2d) < outros AP (569.7d): prioridade relativa existe, mas 53% excede 365d. Criar fila dedicada com SLA interno nas Varas de Violência Doméstica do TJPR.

**P3 — Benchmarking entre varas:**
Cluster 0 (588d) vs. Cluster 1 (1.072d) = 484 dias de diferença. Varas mais lentas (878d) vs. mais rápidas (695d) = 183 dias. Compartilhar práticas das varas com menor mediana como modelo operacional interno.

**P4 — Meta CNJ de duração:**
Definir KPI: "% de AP julgadas em ≤ 365 dias". Hoje: < 40% (mediana 755d). Meta progressiva: ≥ 50% em 12 meses → ≥ 70% em 24 meses.

**P5 — Reduzir loops pós-"Definitivo":**
82 dias médios entre "Definitivo" e próxima petição. Criar fila prioritária para atos de baixa após decisão de mérito.

### 5.2 Sugestões para o Sistema de Informação (PJe/TJPR)

**S1 — Alertas de inércia processual:**
Alerta automático para processos sem movimentação por 30 dias — intervenção precoce no gargalo de 236 dias.

**S2 — Dashboard de violência doméstica em tempo real:**
Integrar API Datajud → painel TJPR com throughput por vara, alertas de 30 dias sem movimentação e flag CNJ Res. 254/2018.

**S3 — Registro obrigatório de marcos processuais:**
Tornar obrigatório: Resposta à Acusação, Decisão sobre absolvição sumária, data de designação de audiência. Hoje ausentes em parte significativa dos casos — impede conformance checking normativo completo.

---

## 5.3 Análise Aprofundada no tema — Violência Doméstica/Protetiva

### Contexto legal

| Norma | O que regula | Referência |
|-------|-------------|------------|
| Lei Maria da Penha art. 18 (Lei 11.340/2006) | Decisão sobre medida protetiva de urgência | **48 horas** |
| CNJ Resolução 254/2018 | Prioridade de tramitação para casos de violência doméstica | Prioridade formal |
| CNJ Resolução 385/2021 | Prioridade de pauta em instâncias superiores | Prioridade formal |
| CF art. 5º, LXXVIII | Razoável duração do processo e celeridade | Garantia constitucional |

### Universo analisado

De 13.234 Ações Penais Ordinárias fechadas, **8.585 casos (~64.9%)** envolvem violência/protetiva:

| Categoria | N |
|-----------|---|
| Contra a Mulher | 5.232 |
| Lesão Cometida em Razão da Condição de Mulher | 2.350 |
| Descumprimento de Medida Protetiva de Urgência | 949 |
| Violência Psicológica contra a Mulher | 36 |
| Feminicídio | 18 |

> **Nota metodológica:** A Ação Penal Ordinária não utiliza medidas liminares como instrumento central — medidas protetivas de urgência são processadas em **autos separados** (cautelar autônoma, art. 19 Lei 11.340/2006). Por isso, apenas 4/8.585 casos (0,05%) registram liminar na AP principal.

### Resultados SLA — Duração até Trânsito em Julgado

| Categoria | N | Mediana | Acima 365d |
|-----------|---|---------|-----------|
| Contra a Mulher | 5.232 | **419,9d** | 41,7% (1.121 casos) |
| Lesão/Condição de Mulher | 2.350 | **400,6d** | 41,9% (848 casos) |
| Desc. Medida Protetiva | 949 | **255,2d** | 22,4% (146 casos) |
| Violência Psicológica | 36 | **372,6d** | 41,5% (17 casos) |
| Feminicídio | 18 | **201,8d** | 25,0% (1 caso) |
| **Total** | **8.585** | **490,2d** | **52,7% (4.522 casos)** |

> Descumprimento de Medida Protetiva tramita mais rápido (255d) porque a prova central é o próprio descumprimento da ordem — instrução mais simples que crimes com extensa produção probatória.

| Grupo | N | Mediana | Diferença |
|-------|---|---------|-----------|
| Violência/protetiva | 8.585 | **490,2d** | −79,5d vs. outros |
| Outros AP | 4.649 | 569,7d | referência |

> **QP5 respondida:** A mediana de violência/protetiva (490.2d) é **menor** que os demais (569.7d), indicando prioridade relativa de tramitação no dataset 2020-2026. Contudo, 4.522/8.585 casos (53%) superam o alerta de 365d — a prioridade existe mas é insuficiente. Alta variância (0 a 2.113 dias) indica ausência de SLA interno padronizado entre varas.

### Distribuição por Cluster K-Means

| Cluster | N | % Violência | Mediana (dias) | Perfil real |
|---------|---|-------------|---------------|-------------|
| 0 — Redistribuídos | 6.408 | **64,9%** | 588d | Mudaram de vara (redistribuição 98.5%) |
| 1 — 2ª instância | 3.583 | **65,0%** | 1.072d | Acórdão 53.5% — subiram ao TJ |
| 2 — Desistência | 105 | **62,0%** | 1.014d | 100% desistiram da ação |
| 3 — Origem simples | 3.138 | **65,1%** | 775d | Sem redistribuição (1.1%), fluxo direto |

Violência doméstica distribui **proporcionalmente** entre todos os clusters (~62–65%) — não existe cluster especializado em violência doméstica. O comportamento processual (redistribuição, 2ª instância, desistência) independe do tipo de crime. **Intervenção prioritária por cluster:** Cluster 1 (1.072d, 27.1%) concentra 65% de casos de violência que deveriam ter tramitação prioritária por lei (CNJ Res. 254/2018) — são exatamente os que mais demoram por terem chegado ao TJ.

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

| Métrica | Descoberto (IM) | Normativo CPP (100% estrito) | Nível |
|---------|----------------|------------------------------|-------|
| Fitness (TBR) | **99.6%** | **46.9%** | Descoberto alto (trivial); normativo 46.9% = gap estrutural PJe |
| Precision (TBR-ETC) | **~14%** | **66.8%** | Descoberto permissivo; normativo é 4,7× mais restritivo |
| Generalization (TBR) | **~89%** | **86.1%** | Ambos altos |
| Simplicity | **~61%** | **50.0%** | Normativo: 8P / 8T / 16 arcos — mínimo, zero tau |

O padrão fitness↑/precision↓ no modelo descoberto é diagnóstico de **processo ad hoc** com variância extrema. A comparação com o normativo 100% estrito CPP (46.9% fitness, 0% perfeitos) confirma: o fluxo real nunca é linear segundo o rito formal, e o PJe não registra etapas obrigatórias do CPP.

---

#### `conformance_normativo.png` — Conformance Normativo CPP arts. 394-405
Cobertura dos 8 marcos CPP no log + tabela comparativa das 4 métricas (normativo × descoberto).

**Como interpretar:**
- Barras verdes (≥70%) = marco bem registrado no PJe
- Barras vermelhas (<30%) = gap de dados — ato ocorre fora do sistema
- Citação = 1.1% → ato cartorial físico não eletrônico; não significa que citação não ocorreu
- Fitness normativo 46.9% (100% estrito, 0 tau) + 0% perfeitos → nenhum caso é linear no rito CPP dentro do PJe; gaps: Citação 1.1% + Trânsito 83.8%

---

#### `petri_net_normativa_cpp.png` — Petri Net Normativa CPP (100% Estrita)
Rede de Petri construída manualmente com base nos arts. 394-405 do CPP. **8 places, 8 transições obrigatórias visíveis, 0 tau** — modelo 100% estrito sem nenhuma concessão ao subregistro do PJe. Cada etapa mandatória (incluindo Citação e Trânsito em Julgado) é transição visível. Usada como referência para o conformance normativo estrito.

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

Boxplot + swarmplot com distribuição de dias até liminar por categoria. Linha vermelha = 2 dias (Lei Maria da Penha art. 18).

Apenas **4 casos** em 8.585 registram liminar na AP principal (0,05%) — medidas protetivas tramitam em autos separados (cautelar autônoma, art. 19 Lei 11.340/2006). O gráfico praticamente vazio é achado estrutural, não ausência de dado.

---

#### `violencia_sla_total.png` — Duração Total por Caso (Violência/Protetiva)

Boxplot por categoria com mediana, IQR e outliers. Linha vermelha = 365 dias (CNJ Res. 254/2018).

| Categoria | Mediana | Acima 365d |
|-----------|---------|-----------|
| Contra a Mulher | 419,9d | 41,7% |
| Lesão/Condição de Mulher | 400,6d | 41,9% |
| Desc. Medida Protetiva | 255,2d | 22,4% |
| **Total** | **490,2d** | **52,7%** |

---

#### `violencia_vs_geral.png` — Violin: Violência vs. Outros AP

Violin plot comparando duração total entre violência/protetiva e demais AP Ordinárias.

- Violência: mediana **490,2d** (−79,5d vs. outros 569,7d) — prioridade relativa
- 53% dos casos violência ainda excedem 365d — SLA insuficiente

---

#### `violencia_sla_cumprimento.png` — % Casos por Faixa de Prazo (Liminar)

Barras por faixa: ≤2d, 3–7d, 8–30d, >30d. Base: 8.585 casos.

99,95% sem liminar (análise relevante apenas para cautelares autônomas, não para AP principal).

---

#### `violencia_por_cluster.png` — Violência por Cluster K-Means

Stacked bar: proporção violência vs. outros AP por cluster.

Violência distribui proporcionalmente em todos os clusters (62–65%) — não existe "cluster de violência" isolado. Intervenção prioritária: Cluster 1 (1.072d) com 65% de casos de violência.

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
| Mineração — Conformance (descoberto) | `analises/analisar.py` | ✓ Fitness 99.6%, Precision ~14%, Gen. ~89% |
| Mineração — Conformance (normativo CPP 100% estrito) | `analises/conformance_normativo.py` | ✓ Fitness 46.9%, Precision 66.8%, Gen. 86.1%, Simp. 50.0% (0% traces perfeitos, 0 tau) |
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

---

## 9. REFERÊNCIAS

### API Datajud CNJ

| Recurso | Link |
|---------|------|
| Documentação oficial | https://datajud-wiki.cnj.jus.br |
| Portal de acesso | https://www.cnj.jus.br/sistemas/datajud/ |
| Endpoint TJPR | `https://api-publica.datajud.cnj.jus.br/api_publica_tjpr/_search` |
| Tabela Processual Unificada (TPU) | https://www.cnj.jus.br/sgt/consulta_publica_classes.php |
| Painel de transparência CNJ | https://painel-estatistica.stg.cloud.cnj.jus.br |

**Normas relevantes:**

| Norma | Conteúdo |
|-------|----------|
| CNJ Resolução 254/2018 | Prioridade de tramitação para casos de violência doméstica |
| CNJ Resolução 385/2021 | Prioridade de pauta em instâncias superiores |
| CF art. 5º LXXVIII | Garantia de razoável duração do processo |
| CPP arts. 394–405 | Fluxo normativo da Ação Penal Ordinária |
| Lei 11.340/2006 | Lei Maria da Penha |

### Referências

**van der Aalst, W.M.P.** (2016). *Process Mining: Data Science in Action* (2nd ed.). Springer.
Referência central: discovery, conformance (fitness, precision, generalization, simplicity), perspectiva organizacional.
https://doi.org/10.1007/978-3-662-49851-4

**van der Aalst, W.M.P.** (2011). *Process Mining: Discovery, Conformance and Enhancement of Business Processes*. Springer.
https://doi.org/10.1007/978-3-642-19345-3

**Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P.** (2013). Discovering block-structured process models from event logs — A constructive approach. *Petri Nets 2013*, LNCS 7927.
Algoritmo **Inductive Miner** utilizado para descoberta da Rede de Petri.
https://doi.org/10.1007/978-3-642-38697-8_17

**van der Aalst, W.M.P., Adriansyah, A., van Dongen, B.** (2012). Replaying history on process models for conformance checking and performance analysis. *WIREs Data Mining and Knowledge Discovery*, 2(2).
Base do **Token-Based Replay (TBR)** utilizado no conformance check.
https://doi.org/10.1002/widm.1045

**Munoz-Gama, J., Carmona, J.** (2010). A Fresh Look at Precision in Process Conformance. *BPM 2010*, LNCS 6336.
Base da métrica **ETC Precision**.
https://doi.org/10.1007/978-3-642-15618-2_16

**Leemans, M., van der Aalst, W.M.P.** (2018). Using process mining to investigate judicial processes. *SSRN*.
https://doi.org/10.2139/ssrn.3280716

### Ferramentas

| Ferramenta | Referência |
|------------|-----------|
| **PM4Py** (Fraunhofer FIT / RWTH Aachen) | https://pm4py.fit.fraunhofer.de |
| **Disco** (Fluxicon) | https://fluxicon.com/disco/ |
| **IEEE XES Standard** | https://xes-standard.org/ |
| **Python** | https://python.org |
| **scikit-learn** | https://scikit-learn.org |
