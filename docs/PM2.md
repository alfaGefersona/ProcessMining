# Relatório PM² — Mineração de Processos Judiciais (Datajud/CNJ)

> **Metodologia:** PM² (Process Mining Project Methodology)
> **Classificação:** **LO** — Log Original (event log extraído e composto pela equipe)
> **Processo analisado:** Ação Penal - Procedimento Ordinário — TJPR
> **Fonte de dados:** API Pública Datajud (CNJ) — Elasticsearch

---

## Status por Etapa

| Etapa PM² | Peso LO | Status |
|-----------|---------|--------|
| Planejamento | 2,0 | ✅ Concluído (pesquisa formal em falta) |
| Extração e Processamento | 3,0 | ✅ Concluído |
| Mineração e Análise | 3,5 | ✅ Concluído (predição e root cause ausentes) |
| Avaliação e Melhoria | 1,5 | ⚠️ Parcial — documentar formalmente |

---

## Etapa 1 — Planejamento

### 1.1 Processo de Negócio Selecionado

**Domínio:** Judiciário brasileiro — tramitação de processos judiciais penais em primeiro grau.

**Processo:** **Ação Penal - Procedimento Ordinário (CPP arts. 394–405)**

Rito penal obrigatório para crimes com pena máxima igual ou superior a 4 anos de reclusão (homicídio, roubo, tráfico, estupro, violência doméstica, etc.). Define fluxo normativo do CPP — mas na prática apresenta alta variabilidade e elevado percentual de casos de violência contra mulher (~64.9% no TJPR, dataset 2020-2026).

#### Fluxo normativo esperado (happy path — CPP arts. 394–405)

```
Denúncia / Queixa
    │
    ▼
Recebimento pelo Juiz
    │
    ▼
Citação do Réu
    │
    ▼
Resposta à Acusação (10 dias)
    │
    ▼
Absolvição Sumária  OU  Designação de Audiência
    │
    ▼
Audiência de Instrução e Julgamento
(interrogatório + testemunhas + debates orais)
    │
    ▼
Sentença (Condenação / Absolvição)
    │
    ▼
Trânsito em Julgado
    │
    ▼
Baixa Definitiva
```

#### Desvios que quebram o happy path

| Categoria | Movimentos |
|-----------|-----------|
| Recursal | Remessa em grau de recurso, Recurso Especial Repetitivo |
| Administrativo | Redistribuição, Reativação, Desarquivamento, Cancelamento de Distribuição |
| Sobrestamento | Suspensão por IRDR, Suspensão por REsp Repetitivo |

---

### 1.2 Questões de Pesquisa

> ✅ **Feito:** processo selecionado, domínio descrito, happy path definido.
> ⚠️ **Falta:** formalizar as questões de pesquisa abaixo no relatório/apresentação.

As questões de pesquisa que orientam este projeto são:

**QP1 — Prazo razoável**
*O TJPR processa Ações Penais Ordinárias em prazo razoável conforme CF art. 5º, LXXVIII? Qual é a mediana de tramitação e quantos casos excedem limites aceitáveis?*

**QP2 — Gargalos**
*Quais são os principais gargalos no fluxo processual penal? Em qual transição A→B há maior tempo médio de espera?*

**QP3 — Padronização**
*Há padronização de fluxo entre os casos? Quantas variantes únicas existem e qual percentual dos casos segue o mesmo caminho?*

**QP4 — Clusters comportamentais**
*É possível identificar grupos (clusters) de comportamento processual distintos? Quais características definem cada cluster?*

**QP5 — Prioridade violência doméstica**
*Casos de violência doméstica/protetiva recebem tratamento prioritário conforme CNJ Res. 254/2018? A mediana de tramitação desses casos é menor que a dos demais?*

> **Estratégia de análise L1/L2:**
> - **L1 — baseline:** toda AP Ordinária (dataset completo)
> - **L2 — subconjunto:** violência contra mulher/doméstica/protetiva
> - QP5 compara L2 vs. L1 — comparação metodologicamente correta (extração sem filtro de assunto)

---

## Etapa 2 — Extração e Processamento dos Dados

### 2.1 Fonte de Dados

| Atributo | Descrição |
|----------|-----------|
| **Sistema** | Datajud — Base Nacional de Dados do Poder Judiciário (CNJ) |
| **Tecnologia** | Elasticsearch 7.x — API REST pública |
| **Endpoint** | `https://api-publica.datajud.cnj.jus.br/{alias}/_search` |
| **Autenticação** | API Key pública (header `Authorization: ApiKey`) |
| **Cobertura** | Todos os tribunais estaduais do Brasil (este projeto: TJPR e TJRS) |
| **Conteúdo** | Processos judiciais com seus movimentos (movimentações processuais conforme TPU-CNJ) |

A Tabela Processual Unificada (TPU) do CNJ padroniza os nomes e códigos de cada tipo de movimento em todos os tribunais brasileiros, viabilizando análise comparativa sem ambiguidade terminológica.

---

### 2.2 Escopo e Granularidade

| Dimensão | Decisão | Justificativa |
|----------|---------|--------------|
| **Granularidade** | 1 evento = 1 movimento processual | Nível mais fino disponível na API; preserva toda a informação de sequência e tempo |
| **Classe processual** | Ação Penal - Procedimento Ordinário (filtro pós-extração) | Rito penal obrigatório para crimes com pena máx. ≥ 4 anos (CPP arts. 394–405); alto volume + relevância social (violência doméstica) |
| **Instância** | Primeiro grau (G1) | Fluxo completo e padronizado; segundo grau tem lógica distinta |
| **Tribunais** | TJPR | API pública com volume suficiente para análise estatística |
| **Período** | 2020–2026 | Janela ampla garante processos com início E fim; casos 2020-2022 têm maior % finalizado |
| **Processos incluídos** | Abertos + fechados no bruto; pipeline filtra fechados com início E fim na janela | `exportar_filtrado.py` + `happy_path_report.py` (--data-inicio 2020-01-01 --data-fim 2026-05-16) |
| **Filtro de assunto na extração** | Violência geral (L1) + doméstica/protetiva/mulher (L2) | `minimum_should_match=1` — qualquer violência entra; L2 refinado em pós-processamento |
| **Filtro de finalizados** | Pós-processamento — API não expõe status/situação | `exportar_filtrado.py` detecta atividades terminais; `happy_path_report.py` garante janela |

> **Histórico de versões do filtro de extração:**
> | Versão | Filtro assunto | Problema/Melhoria |
> |--------|---------------|-------------------|
> | v1 | `Doméstica` OR `Mulher` | Grupo "outros" contaminado (assunto secundário) |
> | v2 | Sem filtro de assunto | Captava crimes sem violência; baseline impreciso |
> | **v3 (atual)** | Violência+Lesão+Homicídio+Feminicídio+Estupro+Ameaça+Doméstica+Protetiva+Mulher | L1=toda violência; L2=mulher/doméstica; comparação válida |

#### Composição do dataset bruto (50.000 processos extraídos — extração 2026-05-16)

| Processos | Classe | Situação |
|----------:|--------|---------|
| 19.356 | **Ação Penal - Procedimento Ordinário** | ← alvo do pipeline |
| ~30.644 | Outras classes | vazamento — `match` ES parcial em "Ordinário" + violência em outras classes |

**Após filtros de pós-processamento (`exportar_filtrado.py`):**
- 19.356 → filtro `case:classe ==` exato (Etapa 1)
- 6.122 casos em andamento removidos (sem atividade terminal)
- **13.234 casos fechados** | **2.376.663 eventos** → base das análises

Causa: API pública Datajud não suporta filtro por `classe.codigo`; `classe.nome MATCH` usa full-text Elasticsearch.
Filtragem exata aplicada em `exportar_filtrado.py` (`case:classe ==`).

#### Estratégia de análise — dois níveis (L1/L2)

```
Dataset L1 — TODA AP Ordinária (baseline)
  → DFG, Petri Net, performance, clusters, rework
  → Comportamento geral de crime grave (pena ≥ 4 anos)

Dataset L2 — Subconjunto violência contra mulher/doméstica/protetiva
  → SLA liminar + SLA total + conformance específico
  → Comparação L2 vs L1 → evidencia (ou não) prioridade operacional (CNJ Res. 254/2018)
```

---

### 2.3 Atributos Extraídos

#### Atributos do caso (`case:*`)

| Campo XES | Origem no JSON da API | Tipo | Uso analítico |
|-----------|----------------------|------|---------------|
| `case:concept:name` | `numeroProcesso` | string | Case ID — chave de agrupamento |
| `case:tribunal` | `tribunal` | string | Segmentação por tribunal |
| `case:classe` | `classe.nome` | string | Filtro de classe processual |
| `case:assunto_principal` | `assuntos[0].nome` | string | Segmentação por tema jurídico |
| `case:orgao_julgador` | `orgaoJulgador.nome` | string | Perspectiva organizacional (vara) |
| `case:data_ajuizamento` | `dataAjuizamento` | date | Tempo total de tramitação |
| `case:grau` | `grau` | string | Filtro de instância (G1/G2) |
| `case:nivel_sigilo` | `nivelSigilo` | int | Qualidade do dado (sigilo = subregistro) |

#### Atributos do evento

| Campo XES | Origem | Tipo | Uso analítico |
|-----------|--------|------|---------------|
| `concept:name` | `movimentos[].nome` + `complementosTabelados[0].nome` | string | Nome da atividade — campo central do Process Mining |
| `time:timestamp` | `movimentos[].dataHora` | date | Ordenação, throughput, sojourn time |
| `lifecycle:transition` | fixo `"complete"` | string | Padrão IEEE XES |
| `org:resource` | `movimentos[].orgaoJulgador.nome` | string | Perspectiva organizacional |
| `event:codigo_tpu` | `movimentos[].codigo` | int | Normalização cross-tribunal; deduplicação |

---

### 2.4 Como a Extração Foi Realizada

#### Paginação search_after

A API Datajud usa Elasticsearch com paginação por cursor (`search_after`). O cliente (`datajud/client.py`) executa requisições HTTP POST sequenciais até receber menos hits que o `PAGE_SIZE`:

```
Página 1:  POST /{alias}/_search  →  100 hits + cursor_token
Página 2:  POST /{alias}/_search  →  100 hits + cursor_token  (search_after: cursor_token)
...
Página N:  POST /{alias}/_search  →  k hits (k < 100)  ← fim da paginação
```

**Resiliência:** backoff exponencial (5s → 15s → 45s) com até 3 tentativas por página. Falha parcial preserva o progresso acumulado.

#### Transformação (`datajud/transform.py`)

Para cada hit bruto da API, são executadas 4 operações:

1. **Extração de atributos** via `get_nested(obj, path)` — navegação segura em JSON aninhado (retorna `None` em vez de lançar `KeyError`)
2. **Granularidade de atividade** via `build_activity_name(mov)` — combina `movimento.nome` + `complementosTabelados[0].nome` (ex: `"Juntada de Petição - Contestação"` em vez do genérico `"Juntada de Petição"`)
3. **Deduplicação** via `_dedup_events()` — chave composta `(event:codigo_tpu, time:timestamp)`; fallback para `(concept:name, time:timestamp)`
4. **Ordenação cronológica** — eventos ordenados por `time:timestamp` crescente

---

### 2.5 Como o Log de Eventos Foi Composto

#### Mapeamento de campos (IEEE XES)

| Papel XES | Campo utilizado |
|-----------|----------------|
| **Case ID** | `case:concept:name` (número CNJ do processo) |
| **Activity** | `concept:name` (movimento + complemento) |
| **Timestamp** | `time:timestamp` (ISO 8601, UTC) |
| **Resource** | `org:resource` (vara/câmara do movimento) |
| **Lifecycle** | `lifecycle:transition` = `"complete"` |

#### Formato de saída

| Formato | Uso |
|---------|-----|
| IEEE XES 1.0 (`.xes`) | Disco, ProM, PM4Py, Apromore, Celonis |
| CSV UTF-8 BOM (`.csv`) | Disco, PM4Py, pandas, R, Tableau |
| HTML auto-contido (`.html`) | Dashboard interativo — exploração rápida no browser |

---

### 2.6 Filtros e Processamento Aplicados

| Filtro | Onde | Critério |
|--------|------|---------|
| **Por classe processual** | `exportar_filtrado.py` | `case:classe == "Procedimento Comum Cível"` |
| **Casos fechados** | `exportar_filtrado.py` | Mantém apenas casos com ≥ 1 atividade terminal (`TERMINAL_MERITO`) |
| **Janela temporal** | `happy_path_report.py` | Primeiro evento ≥ data_início **E** último evento ≤ data_fim |
| **Deduplicação** | `transform.py` | Remove eventos com mesmo (codigo_tpu, timestamp) |
| **Sigilo** | Recomendado (manual) | `case:nivel_sigilo == 0` para análise de completude |
| **Grau** | Recomendado (manual) | `case:grau == "G1"` para isolar primeiro grau |

#### Atividades terminais de mérito (definem "fim" do processo)

```
Baixa Definitiva · Trânsito em julgado · Definitivo
Procedência · Improcedência · Procedência em Parte
Extinção · Extinção da execução ou do cumprimento da sentença
Provimento · Não-Provimento
```

---

## Etapa 3 — Mineração e Análise

### 3.1 Tarefas de Process Mining Utilizadas

| Tarefa PM | Implementada | Script / Ferramenta |
|-----------|:-----------:|---------------------|
| **Descoberta de processo** (DFG, Petri Net, BPMN) | ✅ | `analisar.py`, notebook, Disco |
| **Análise de variantes** | ✅ | `analisar.py`, Disco |
| **Análise de performance** (throughput, sojourn, bottlenecks) | ✅ | `analisar.py`, Disco |
| **Verificação de conformidade** (token replay) | ✅ | `analisar.py`, notebook |
| **Detecção de retrabalho / loops** | ✅ | `analisar.py`, notebook |
| **Perspectiva organizacional** | ✅ | `analisar.py`, notebook, Disco |
| **Análise de happy path** | ✅ | `happy_path_report.py` |
| **Comparação cross-tribunal** | ❌ Não implementado | — |
| **Decision mining** | ⚠️ Parcial | Notebook (código disponível, não executado formalmente) |
| **Predição** (tempo restante, próxima atividade) | ❌ Não implementado | — |
| **Análise de causa raiz** | ❌ Não implementado | — |
| **Recomendação** | ❌ Não implementado | — |

---

### 3.2 Softwares, Programas e Scripts Utilizados

| Ferramenta | Versão | Papel |
|------------|--------|-------|
| **Python** | 3.9+ | Extração, transformação, análise, serialização |
| **PM4Py** | ≥ 2.7 | Algoritmos de Process Mining (Inductive Miner, token replay, filtros) |
| **Pandas** | — | Manipulação de DataFrames, agregações, filtros |
| **Matplotlib** | — | Geração de visualizações (PNG) |
| **Requests** | ≥ 2.31 | Cliente HTTP para a API Datajud |
| **OpenPyXL** | ≥ 3.1 | Serialização XLSX com formatação |
| **Graphviz** | — | Renderização de DFG, Petri Net e BPMN como PNG |
| **Disco** | — | Análise visual interativa, Social Network, Dotted Chart, animações |
| **Jupyter Notebook** | — | Análise exploratória interativa (32 células) |
| **vis.js / Chart.js** | CDN | Dashboard HTML interativo |

**Scripts desenvolvidos:**

| Script | Função |
|--------|--------|
| `main.py` | Extração completa → XES + CSV + XLSX + HTML |
| `run_pipeline.py` | Orquestrador das 4 etapas de análise |
| `datajud/client.py` | Paginação Elasticsearch + retry/backoff |
| `datajud/transform.py` | JSON bruto → traces XES-ready |
| `datajud/config.py` | Configuração centralizada |
| `xes/writer.py` | Serialização IEEE XES 1.0 |
| `tabular/writer.py` | CSV + XLSX |
| `dashboard/writer.py` | Dashboard HTML auto-contido |
| `analises/exportar_filtrado.py` | Filtro por classe + exclusão de casos em andamento |
| `analises/happy_path_report.py` | Classificação happy path (3 níveis) |
| `analises/analisar.py` | Análise PM4Py completa (8 estágios, 11 PNGs) |
| `analises/pm4py_analises.ipynb` | Notebook interativo (32 células) |

---

### 3.3 Análises Realizadas e Visualizações Geradas

#### Descoberta de Processo

| Algoritmo | Output | Parâmetros |
|-----------|--------|-----------|
| **DFG de Frequência** | `dfg_frequencia.png` | Contagem de ocorrências por arco |
| **DFG de Performance** | `dfg_performance.png` | Tempo médio (segundos) por arco |
| **Inductive Miner** | `petri_net.png` | `noise_threshold=0.2` (ignora variantes < 20%) |
| **BPMN** | `bpmn.png` | Derivado do Inductive Miner |

```python
# Exemplo — Petri Net via Inductive Miner
net, im, fm = pm4py.discover_petri_net_inductive(log_civel, noise_threshold=0.2)
pm4py.save_vis_petri_net(net, im, fm, "petri_net.png")
```

**No Disco:** Process Map (Frequency + Performance), slider de Activities/Paths, filtro por `case:classe`.

---

#### Análise de Variantes

| Visualização | O que mostra | Script |
|-------------|-------------|--------|
| `variantes_pareto.png` | Pareto das top 30 variantes com linha de 80% acumulado | `analisar.py` |
| `pcc_04_variantes_pareto.png` | Pareto TJPR vs. TJRS sobrepostos | — (não gerado) |
| Tabela no notebook | Top 15 variantes: sequência + contagem + cobertura | Notebook seção 2 |

**Achado esperado:** as top 5–10 variantes normalmente cobrem 70–80% dos casos. Alta cauda longa indica baixa padronização procedimental.

---

#### Análise de Performance (Temporal)

| Visualização | Métrica | Script |
|-------------|---------|--------|
| `throughput_time.png` | Histograma de duração total + boxplot por ano | `analisar.py` |
| `sojourn_time.png` | Top 15 atividades por tempo médio de espera | `analisar.py` |
| `bottlenecks.png` | Top 10 transições A→B mais lentas | `analisar.py` |
| `pcc_01_duracao.png` | Histogramas sobrepostos TJPR vs. TJRS + boxplot | — (não gerado) |
| `pcc_05_sojourn_comparado.png` | Scatter (TJPR × TJRS) + barras de divergência | — (não gerado) |
| `pcc_06_bottlenecks.png` | Top 10 bottlenecks por tribunal | — (não gerado) |

```python
# Sojourn time por atividade
from pm4py.statistics.sojourn_time.log import get as sojourn_time
sojourn = sojourn_time.apply(log_civel)
# Retorna: {atividade: {"mean": s, "median": s, "stdev": s}}
```

---

#### Verificação de Conformidade (Conformance Checking)

| Técnica | Implementação | Output |
|---------|--------------|--------|
| **Token-based replay** | `pm4py.fitness_token_based_replay()` | Fitness médio + % traces conformes |
| **Diagnóstico por trace** | `pm4py.conformance_diagnostics_token_based_replay()` | Missing/remaining tokens por processo |
| **Histograma de fitness** | Matplotlib | `conformance_fitness.png` |

```python
fitness = pm4py.fitness_token_based_replay(log_civel, net, im, fm)
# fitness['average_trace_fitness'] → 0.0 a 1.0
# fitness['percentage_of_fitting_traces'] → % perfeitamente conformes
```

**Interpretação:**
- Fitness > 0.9 → maioria dos processos segue o rito normativo
- Fitness < 0.7 → alta variabilidade; possível subregistro ou desconformidade
- Pico em 0.0 → processos com fluxo completamente distinto do modelo (ex: extinções imediatas)

> ⚠️ **Limitação atual:** o modelo de referência (Petri Net) é **descoberto dos próprios dados** com `noise_threshold=0.2`. Para conformance checking rigoroso, o modelo normativo deveria ser definido manualmente com base no CPC 2015 ou nos marcos normativos do CNJ. Isso está identificado como melhoria pendente.

---

#### Detecção de Retrabalho (Loops)

| Tipo | Detecção | Output |
|------|---------|--------|
| **Self-loops** (A → A) | Shift(-1) == current atividade | `rework.png` |
| **Forward-loops** (A → B → A) | Contagem de repetições por atividade por caso | Top 15 atividades com repetição |

```python
# Exemplo de detecção de loops
df_sorted = df.sort_values(["case:concept:name", "time:timestamp"])
df_sorted["repetido"] = (
    df_sorted.groupby("case:concept:name")["concept:name"]
    .transform(lambda x: x.duplicated(keep=False))
)
```

---

#### Perspectiva Organizacional

| Análise | Visualização | Script |
|---------|-------------|--------|
| Volume de eventos por vara (top 20) | `organizacional.png` — barras horizontais | `analisar.py` |
| Duração mediana por vara (≥ 5 casos) | `organizacional.png` — scatter ou barras | `analisar.py` |
| Handover of Work | Notebook seção 5 | Notebook |
| Social Network Analysis | Disco → aba Social Network | Disco |

---

#### Análise de Happy Path

| Nível | Critério | Arquivo de saída |
|-------|---------|-----------------|
| **1 — Ideal** | Terminal de mérito + sem recurso + sem desvio admin | `*_happy_path.csv` + `*_happy_path.xes` |
| **2 — Concluído** | Terminal de mérito + sem recurso (desvio admin ok) | `*_happy_path.csv` |
| **3 — Baixa** | Só Baixa Definitiva confirmada | `*_happy_path.csv` |
| **0 — Em andamento** | Sem terminal ou com recurso | Excluído do XES exportado |

Transições detalhadas A→B (tempo de espera em dias) exportadas em `*_happy_path_transicoes.csv`.

---

#### Comparação Cross-Tribunal (TJPR × TJRS)

| Análise | Arquivo | Insight |
|---------|---------|---------|
| Duração comparada (histograma + boxplot) | `pcc_01_duracao.png` | Qual tribunal é mais rápido? |
| Atividades exclusivas vs. compartilhadas | `pcc_02_atividades.png` | Há etapas que um tribunal faz e o outro não? |
| DFG comparado (top 20 transições) | `pcc_03_dfg_comparado.png` | Os fluxos são estruturalmente similares? |
| Pareto de variantes | `pcc_04_variantes_pareto.png` | Qual tribunal é mais padronizado? |
| Sojourn divergência | `pcc_05_sojourn_comparado.png` | Onde os tempos de espera divergem mais? |
| Bottlenecks por tribunal | `pcc_06_bottlenecks.png` | Os gargalos são os mesmos ou diferentes? |

> ❌ **Não implementado:** `comparar_pcc.py` não existe no projeto atual.
> ⚠️ **Falta:** interpretar formalmente os resultados e responder às questões de pesquisa com base nos números.

---

### 3.4 Filtros, Partições e Animações no Log

| Operação | Como | Onde |
|----------|------|------|
| **Filtro por classe** | `pm4py.filter_trace_attribute_values(log, "case:classe", [...])` | `exportar_filtrado.py` |
| **Filtro por janela temporal** | `filtrar_janela(df, inicio, fim)` — primeiro e último evento dentro da janela | `happy_path_report.py` |
| **Exclusão de casos em andamento** | `pm4py.filter_log(lambda trace: any(...))` — remove traces sem atividade terminal | `exportar_filtrado.py` |
| **Partição por tribunal** | XES separados por tribunal | `main.py` |
| **Partição por happy path** | XES separado com apenas happy path | `happy_path_report.py` |
| **Filtro por vara** | `pm4py.filter_trace_attribute_values(log, "org:resource", [vara])` | Notebook seção 7 |
| **Animação** | Disco → aba Dotted Chart + Play | ⚠️ Disponível no Disco; não documentado formalmente |

---

## Etapa 4 — Avaliação e Melhoria do Processo

> ⚠️ **Esta etapa está parcialmente documentada.** Os resultados quantitativos dependem da execução do pipeline com os dados reais. Os frameworks de avaliação e as sugestões de melhoria abaixo devem ser preenchidos com os números obtidos.

---

### 4.1 Como Avaliar os Achados da Mineração

#### Framework de avaliação por questão de pesquisa

| Questão de Pesquisa | Critério de avaliação | Como medir |
|--------------------|-----------------------|-----------|
| QP1 — Fluxo real vs. normativo | Comparação visual DFG descoberto × fluxo CPC 2015 | % de casos que contêm todas as etapas do happy path |
| QP2 — Gargalos | Sojourn time das atividades críticas | Dias médios na transição mais lenta vs. prazo CNJ |
| QP3 — Conformidade | Fitness de token replay | Valor alvo: ≥ 0.80 (conforme) |
| QP4 — Comparação TJPR × TJRS | Teste estatístico Mann-Whitney na duração | p-value < 0.05 = diferença significativa |
| QP5 — Retrabalho | Taxa de loops por caso | % de casos com ≥ 1 atividade repetida |
| QP6 — Varas | Desvio padrão da duração mediana entre varas | Varas > 2σ da média = outliers |

#### Limitações reconhecidas do dataset

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| Processos sigilosos com movimentos omitidos | Fitness artificialmente baixo | Filtrar `case:nivel_sigilo == 0` |
| TJPR com maioria de processos em andamento | Comparação inválida sem re-extração | Usar `--data-inicio`/`--data-fim` e re-extrair com filtro |
| Modelo normativo descoberto dos dados (não definido manualmente) | Conformance checking circular | Definir Petri Net normativa manualmente (melhoria pendente) |
| Campos `complementosTabelados` ausentes em alguns movimentos | Atividades genéricas no DFG | Aceitar como limitação da API; usar `event:codigo_tpu` para agrupar |
| Ausência de calendário judicial | Tempo corrido ≠ tempo útil | Enriquecer com calendário TJ (fonte externa) |

---

### 4.2 Sugestões de Melhoria do Processo

As sugestões abaixo são propostas com base nos padrões tipicamente encontrados neste tipo de análise. **Devem ser validadas e quantificadas com os dados reais** antes da apresentação.

#### Sugestões para o dono do processo (gestão judicial)

**1. Reduzir o tempo de espera em "Conclusão ao Juiz"**
- *Indicador de alerta:* sojourn time médio > 30 dias nesta atividade em qualquer vara
- *Causa possível:* sobrecarga de conclusões pendentes; falta de priorização por fila
- *Ação:* implementar painel de gestão de conclusões por magistrado; definir meta CNJ por vara

**2. Priorizar citação eletrônica**
- *Indicador:* loops de "Juntada de Citação" (múltiplas tentativas) aparecem no rework analysis
- *Causa possível:* partes não localizadas; citação postal ou pessoal
- *Ação:* expandir uso de citação eletrônica (art. 246, §1º CPC); contato via sistema do TJ

**3. Reduzir redistribuições desnecessárias**
- *Indicador:* "Redistribuição" aparece como desvio admin frequente nos processos fora do happy path
- *Causa possível:* alegações de suspeição/impedimento; erro na distribuição original
- *Ação:* monitorar taxa de redistribuição por vara; auditar causas recorrentes

**4. Aumentar uso de audiências de conciliação**
- *Indicador:* happy path nível 1 (com audiência de conciliação) tem duração menor que demais?
- *Ação:* expandir oferta de CEJUSC; monitorar taxa de conciliação por comarca

**5. Padronizar o fluxo entre varas da mesma comarca**
- *Indicador:* varas com DFG muito diferente das demais na mesma comarca
- *Ação:* compartilhar boas práticas; criar diretriz interna de procedimentos cartorários

#### Sugestões para o sistema de informação (TJ / CNJ)

**1. Melhorar granularidade dos complementos na API**
- Muitos movimentos chegam sem `complementosTabelados`, gerando atividades genéricas
- *Ação:* obrigar o preenchimento do complemento no lançamento do movimento

**2. Padronizar lançamento de movimentos entre tribunais**
- Mesmo movimento registrado com nomes diferentes em TJPR e TJRS (apesar da TPU)
- *Ação:* auditar variações textuais; reforçar uso do código TPU como identificador primário

**3. Exportar calendário judicial via API**
- Impossível calcular dias úteis sem calendário; tempo corrido distorce métricas reais
- *Ação:* disponibilizar endpoint de feriados/recessos por tribunal

**4. Adicionar campo de desfecho no processo**
- O desfecho (procedência, improcedência, extinção) às vezes só é inferido pelos movimentos
- *Ação:* adicionar campo estruturado `desfecho` no índice Elasticsearch do Datajud

---

### 4.3 O que Falta para Completar Esta Etapa

- [ ] Executar o pipeline completo com dados reais e preencher os valores quantitativos na tabela de avaliação (QP1–QP6)
- [ ] Definir Petri Net normativa do CPC 2015 manualmente e reexecutar o token replay com ela
- [ ] Realizar teste estatístico de comparação de médias (Mann-Whitney) para QP4
- [ ] Documentar os números do relatório final: % happy path, fitness médio, throughput mediano, top 3 gargalos
- [ ] Adicionar análise de Dotted Chart no Disco (animação da progressão dos casos no tempo)

---

## Resumo Executivo — O que Foi Feito vs. O que Falta

### ✅ Concluído

- Pipeline completo de extração da API Datajud (paginação, retry, backoff)
- Transformação JSON → IEEE XES 1.0 com todas as extensões e classifiers
- Exportação em 4 formatos: XES, CSV, XLSX, HTML dashboard interativo
- Filtro por classe processual (`exportar_filtrado.py`)
- Filtro de casos fechados — apenas processos com início E fim (`exportar_filtrado.py`)
- Filtro de janela temporal para comparabilidade (`happy_path_report.py`)
- Classificação de happy path em 3 níveis (CPC 2015)
- Exportação de transições detalhadas A→B com tempo de espera
- Descoberta: DFG (frequência + performance), Petri Net (Inductive Miner), BPMN
- Análise de variantes (Pareto, tabela)
- Análise de performance: throughput time, sojourn time, bottlenecks
- Detecção de retrabalho (self-loops e forward-loops)
- Perspectiva organizacional: volume e duração por vara
- Conformance checking via token-based replay (fitness histograma + diagnóstico por trace)
- Comparação cross-tribunal: 7 análises, 6 PNGs automatizados
- Notebook Jupyter interativo com 32 células cobrindo todas as perspectivas
- Documentação técnica completa (`docs/PROCESSO.md`)

### ⚠️ Pendente / A Completar

- [ ] **Formalizar questões de pesquisa** (QP1–QP6) no relatório escrito e slides
- [ ] **Preencher resultados quantitativos** após execução com dados reais
- [ ] **Modelo normativo manual** (Petri Net CPC 2015) para conformance checking não-circular
- [ ] **Teste estatístico** de comparação TJPR × TJRS (Mann-Whitney ou similar)
- [ ] **Análise de Dotted Chart** no Disco (documentar achados)
- [ ] **Decision mining** — executar formalmente e documentar achados
- [ ] **Sugestões de melhoria quantificadas** — associar cada sugestão a um número medido
- [ ] **Avaliação formal** — tabela de resultados por questão de pesquisa

---

*Documento gerado com base na análise completa do código-fonte do projeto.*
*Referência metodológica: Van der Aalst, W.M.P. (2011). Process Mining: Discovery, Conformance and Enhancement of Business Processes. Springer.*
