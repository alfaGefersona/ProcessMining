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
