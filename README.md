# ProcessMining — PM² TJPR

Process Mining aplicado a **Ações Penais - Procedimento Ordinário** do TJPR.
Metodologia **PM²** (Process Mining Project Methodology) sobre dados públicos da API Datajud (CNJ Elasticsearch).

**Aluno:** Geferson Artuzo
**Período de análise:** 01/01/2020 → 13/05/2026

---

## Sobre o Relatório (`RELATORIO_PM2.md`)

O arquivo [`RELATORIO_PM2.md`](./RELATORIO_PM2.md) é o **documento central do projeto** — contém todo o conteúdo acadêmico estruturado em PM²:

| Seção | Conteúdo |
|-------|----------|
| **1. Planejamento** | Processo de negócio selecionado, justificativa, questões de pesquisa (QP1–QP5), fluxo normativo CPP arts. 394–405 |
| **2. Extração e Processamento** | Fonte de dados (API Datajud CNJ), escopo, pipeline de filtros, event log |
| **3. Análise** | Descoberta (DFG, Petri Net), variantes, performance, gargalos, rework, perspectiva organizacional, conformance, clusters |
| **4. Violência Doméstica** | SLA Lei Maria da Penha, CNJ Res. 254/2018, comparação com demais casos |
| **5. Conclusões** | Respostas às QP1–QP5, recomendações de intervenção |

**Para editar o relatório:** modifique `RELATORIO_PM2.md` e regenere o PDF:

```bash
python gerar_pdf.py
# Gera output/RELATORIO_PM2_AcaoPenal.pdf  (~6.4 MB, com imagens inline)
```

O `gerar_pdf.py` sintetiza o MD para PDF (remove seções de setup/configuração, injeta imagens nas seções correspondentes e redimensiona automaticamente imagens grandes).

---

## Processo de Negócio

**Ação Penal - Procedimento Ordinário** — rito penal obrigatório para crimes com pena máxima ≥ 4 anos (CPP art. 394, §1º, I). Crimes típicos: homicídio, feminicídio, roubo qualificado, tráfico, estupro, lesão corporal grave em violência doméstica.

**Fluxo normativo (CPP arts. 394–405):**

```
Denúncia → Recebimento → Citação → Resposta à Acusação
    → [Absolvição sumária] → Audiência de Instrução e Julgamento
    → Sentença → Trânsito em Julgado
```

**Por que AP Ordinária para PM²:**

| Critério | Valor |
|----------|-------|
| Fluxo normativo definido em lei | CPP arts. 394–405 |
| Volume de casos fechados | 13.234 |
| Relevância social | ~64,9% violência/protetiva |
| Hipótese testável | Prazo razoável (CF art. 5º LXXVIII)? |

---

## Questões de Pesquisa

| # | Questão |
|---|---------|
| QP1 | O TJPR processa AP Ordinárias em prazo razoável? (CF art. 5º LXXVIII) |
| QP2 | Quais gargalos contribuem mais para atraso no julgamento? |
| QP3 | O fluxo real apresenta padronização? Quantas variantes únicas? |
| QP4 | É possível identificar perfis comportamentais (clusters)? |
| QP5 | Casos de violência doméstica recebem prioridade? (CNJ Res. 254/2018) |

---

## Requisitos

```bash
brew install graphviz   # para DFG / Petri Net via pm4py

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Extração de dados

```bash
python main.py
# Gera output/TJPR_{timestamp}.csv e .html
```

Configurações em `datajud/config.py`: tribunais, filtro de datas, campos extras.

## Pipeline de análise

Roda todas as etapas em sequência sobre dados já extraídos:

```bash
source .venv/bin/activate
python run_pipeline.py
```

| # | Script | Saída |
|---|--------|-------|
| 1 | `exportar_filtrado.py` | XES + CSV filtrados por classe |
| 2 | `happy_path_report.py` | CSV + XES happy path + transições |
| 3 | `analisar.py` | PNGs análise PM4Py (discovery, performance, rework) |
| 4 | `agrupar.py` | CSV por cluster K-Means + top variantes |
| 5 | `analise_violencia_mulher.py` | SLA violência doméstica / CNJ Res. 254/2018 |

Parâmetros opcionais:

```bash
python run_pipeline.py --classe "Ação Penal - Procedimento Ordinário" \
                       --tribunal TJPR \
                       --data-inicio 2020-01-01 \
                       --data-fim 2026-05-16
```

## Relatório PDF

```bash
python gerar_pdf.py
# Gera output/RELATORIO_PM2_AcaoPenal.pdf
```

## Estrutura

```
RELATORIO_PM2.md    Relatório acadêmico completo (fonte da verdade)
gerar_pdf.py        Converte MD → PDF com imagens inline
run_pipeline.py     Executa todas as análises em sequência
main.py             Extração via API Datajud

datajud/            API client, config, transform
xes/                Serializador IEEE XES
tabular/            Serializador CSV (event log plano)
dashboard/          Dashboard HTML (vis.js + Chart.js)
analises/           Scripts de análise PM4Py + notebook Jupyter
  imgs/             Imagens geradas (gitignored)
output/             Dados extraídos e relatórios (gitignored)
```

## API Datajud CNJ

| Atributo | Valor |
|----------|-------|
| **Base URL** | `https://api-publica.datajud.cnj.jus.br` |
| **Endpoint TJPR** | `/api_publica_tjpr/_search` |
| **Motor** | Elasticsearch — paginação `search_after` |
| **Autenticação** | API Key pública CNJ (inclusa em `datajud/config.py`) |
| **Acesso** | Público e gratuito |
| **Página máxima** | 10.000 documentos por request (usado: 100) |

**Links oficiais:**

- Documentação Datajud: https://datajud-wiki.cnj.jus.br
- Portal de acesso: https://www.cnj.jus.br/sistemas/datajud/
- Painel de transparência CNJ: https://painel-estatistica.stg.cloud.cnj.jus.br
- Tabela Processual Unificada (TPU — códigos de movimentos): https://www.cnj.jus.br/sgt/consulta_publica_classes.php

**Normas e resoluções relevantes:**

| Norma | Conteúdo |
|-------|----------|
| CNJ Resolução 254/2018 | Prioridade de tramitação para casos de violência doméstica |
| CNJ Resolução 385/2021 | Prioridade de pauta em instâncias superiores |
| CF art. 5º LXXVIII | Garantia de razoável duração do processo |
| CPP arts. 394–405 | Fluxo normativo da Ação Penal Ordinária |
| Lei 11.340/2006 | Lei Maria da Penha |

---

## Referências Acadêmicas

### Process Mining — Fundamentos

- **van der Aalst, W.M.P.** (2016). *Process Mining: Data Science in Action* (2nd ed.). Springer.
  Referência central: algoritmos de discovery, conformance (fitness, precision, generalization, simplicity) e perspectiva organizacional.
  https://doi.org/10.1007/978-3-662-49851-4

- **van der Aalst, W.M.P.** (2011). *Process Mining: Discovery, Conformance and Enhancement of Business Processes*. Springer.
  https://doi.org/10.1007/978-3-642-19345-3

- **Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P.** (2013). Discovering block-structured process models from event logs — A constructive approach. *Petri Nets 2013*, LNCS 7927.
  Algoritmo **Inductive Miner** utilizado para descoberta da Rede de Petri.
  https://doi.org/10.1007/978-3-642-38697-8_17

- **van der Aalst, W.M.P., Adriansyah, A., van Dongen, B.** (2012). Replaying history on process models for conformance checking and performance analysis. *WIREs Data Mining and Knowledge Discovery*, 2(2), 182–192.
  Base do **Token-Based Replay (TBR)** utilizado no conformance check.
  https://doi.org/10.1002/widm.1045

- **Munoz-Gama, J., Carmona, J.** (2010). A Fresh Look at Precision in Process Conformance. *BPM 2010*, LNCS 6336.
  Base da métrica **ETC Precision** utilizada na avaliação do modelo.
  https://doi.org/10.1007/978-3-642-15618-2_16

### Ferramentas

- **PM4Py** — Python library for Process Mining (Fraunhofer FIT / RWTH Aachen):
  https://pm4py.fit.fraunhofer.de
  Documentação: https://processintelligence.solutions/static/api/2.7.11/index.html

- **Disco** — Process Mining tool (Fluxicon):
  https://fluxicon.com/disco/

- **IEEE XES Standard** (eXtensible Event Stream):
  https://xes-standard.org/

### Process Mining em Justiça / Setor Público

- **Leemans, M., van der Aalst, W.M.P.** (2018). Using process mining to investigate judicial processes. *SSRN*.
  https://doi.org/10.2139/ssrn.3280716

- **Teinemaa, I., Dumas, M., Rosa, M.L., Maggi, F.M.** (2019). Outcome-oriented predictive process monitoring. *ACM TKDD*, 13(2).
  https://doi.org/10.1145/3301300

---

## Principais achados — TJPR 2020–2026

| Métrica | Valor |
|---------|-------|
| Processos analisados | 13.234 fechados |
| Throughput mediano | 755 dias |
| Gargalo principal | Mero expediente → Recebimento: **236 dias** médios |
| Rework | 100% dos casos (pelo menos 1 retorno) |
| Variantes únicas | 13.234 (cada processo = caminho único) |
| Fitness (TBR) | 96,49% |
| Casos violência doméstica | ~64,9% do dataset |
| Mediana trânsito violência | 391 dias (> outros: 366 dias) |
