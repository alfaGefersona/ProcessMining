"""
Process Mining — Extrator Datajud
Ponto de entrada do projeto.

Uso:
    python main.py

Saída:
    output/{TRIBUNAL}_{timestamp}.xes   — IEEE XES 1.0 (Disco / PM4Py)
    output/{TRIBUNAL}_{timestamp}.csv   — event log plano (Disco / PM4Py)
    output/{TRIBUNAL}_{timestamp}.html  — dashboard interativo (browser)
"""

import logging
import os
from datetime import datetime

from datajud.config import TRIBUNAIS, OUTPUT_DIR
from datajud.client import fetch_all_hits
from datajud.transform import hits_to_traces
from xes.writer import write_xes
from tabular.writer import write_csv
from dashboard.writer import write_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    resumo = []

    for alias, nome in TRIBUNAIS.items():
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join(OUTPUT_DIR, f"{nome}_{ts}")

        hits_gen   = fetch_all_hits(alias, nome)
        traces_gen = hits_to_traces(hits_gen, nome)
        traces     = list(traces_gen)   # coleta em memória para exportar múltiplos formatos

        # XES omitido: disco limitado — exportar_filtrado.py gera XES filtrado (menor)
        write_csv(traces, base + ".csv")
        write_html(traces, base + ".html", nome)
        n_t = len(traces)
        n_e = sum(len(t["events"]) for t in traces)

        resumo.append((nome, base, n_t, n_e))

    print("\n" + "=" * 60)
    print("RESUMO DA EXTRAÇÃO")
    print("=" * 60)
    for nome, base, n_t, n_e in resumo:
        print(f"  {nome}: {n_t} processos | {n_e} eventos")
        print(f"       → {base}.xes")
        print(f"       → {base}.csv")
        print(f"       → {base}.html")
    print("=" * 60)


if __name__ == "__main__":
    run()
