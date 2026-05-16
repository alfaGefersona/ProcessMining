# ProcessMining — PM² TJPR

Process Mining aplicado a **Ações Penais - Procedimento Ordinário** do TJPR.
Dados extraídos da API pública Datajud (CNJ Elasticsearch).

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

O relatório sintetiza os achados com imagens inline. Fonte: `RELATORIO_PM2.md`.

## Estrutura

```
datajud/        API Datajud — client, config, transform
xes/            Serializador IEEE XES
tabular/        Serializador CSV (event log plano)
dashboard/      Dashboard HTML auto-contido (vis.js + Chart.js)
analises/       Scripts de análise PM4Py + notebook Jupyter
  imgs/         Imagens geradas (gitignored)
output/         Dados extraídos e relatórios (gitignored)
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
| Casos violência doméstica | 83,2% do dataset |
| Mediana trânsito violência | 391 dias (> outros: 366 dias) |

## Questões de pesquisa

1. O TJPR processa Ações Penais em prazo razoável? (CF art. 5º LXXVIII)
2. Quais os principais gargalos do fluxo processual penal?
3. Há padronização de fluxo entre os casos?
4. É possível identificar clusters de comportamento processual?
5. Casos de violência doméstica recebem prioridade? (CNJ Res. 254/2018)
