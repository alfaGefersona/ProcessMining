"""
Camada de geração tabular: serializa traces em CSV.

Formato: event log plano (uma linha por evento), compatível com PM4Py e Disco.
  - Cada linha representa um evento.
  - Atributos do trace (processo) são repetidos em colunas "case:*" para cada evento.
  - O atributo "concept:name" do trace vira a coluna "case:concept:name" (case ID padrão PM4Py).
"""

import csv
import logging
import os

log = logging.getLogger(__name__)

# Colunas obrigatórias — sempre nas primeiras posições
_CASE_FIRST  = ["case:concept:name"]
_EVENT_FIRST = ["concept:name", "time:timestamp", "lifecycle:transition", "org:resource"]


def _traces_to_rows(traces: list[dict]) -> tuple[list[str], list[dict]]:
    """
    Converte lista de traces em (headers, rows) para serialização tabular.

    Regras de nomeação de colunas:
      - Trace "concept:name"  → coluna "case:concept:name"
      - Trace "case:*"        → coluna "case:*"  (mantém prefixo)
      - Event attrs           → coluna com chave original
    """
    from xes.writer import format_date

    case_extra_cols  = []   # colunas de trace além de case:concept:name (descobertas em ordem)
    event_extra_cols = []   # colunas de evento além dos 4 obrigatórios
    seen_case_cols   = set(_CASE_FIRST)
    seen_event_cols  = set(_EVENT_FIRST)

    rows = []

    for trace in traces:
        # Mapeia atributos do trace → dict de colunas "case:*"
        case_row: dict = {}
        for k, (val, xes_type) in trace["attrs"].items():
            col = "case:concept:name" if k == "concept:name" else k
            case_row[col] = format_date(val) if xes_type == "date" else val
            if col not in seen_case_cols:
                seen_case_cols.add(col)
                case_extra_cols.append(col)

        # Uma linha por evento
        for evt in trace["events"]:
            row = dict(case_row)
            for k, (val, xes_type) in evt.items():
                row[k] = format_date(val) if xes_type == "date" else val
                if k not in seen_event_cols:
                    seen_event_cols.add(k)
                    event_extra_cols.append(k)
            rows.append(row)

    headers = _CASE_FIRST + case_extra_cols + _EVENT_FIRST + event_extra_cols
    return headers, rows


def write_csv(traces: list[dict], output_path: str) -> tuple[int, int]:
    """
    Escreve o event log em formato CSV (UTF-8 com BOM para compatibilidade com Excel).

    Args:
        traces:      lista de dicts {'attrs': ..., 'events': [...]}
        output_path: caminho completo do arquivo de saída

    Returns:
        (n_traces, n_events)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    headers, rows = _traces_to_rows(traces)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    n_traces = len(traces)
    n_events = len(rows)
    log.info(f"CSV salvo: {output_path}  ({n_traces} traces | {n_events} eventos)")
    return n_traces, n_events


