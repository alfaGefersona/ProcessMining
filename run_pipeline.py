"""
Pipeline PM² — Ação Penal - Procedimento Ordinário (TJPR, 2020-2026).

Uso:
    python run_pipeline.py
    python run_pipeline.py --classe "Ação Penal - Procedimento Ordinário"
    python run_pipeline.py --data-inicio 2020-01-01 --data-fim 2026-05-16
    python run_pipeline.py --tribunal TJPR

Etapas executadas:
  1. exportar_filtrado.py        — filtra XES/CSV por classe (casos fechados) + top variantes
  2. happy_path_report.py        — happy path com janela temporal (exporta .xes/.csv)
  3. analisar.py                 — análise PM4Py completa (DFG, Petri Net, performance, rework)
  4. agrupar.py                  — agrupamento por variante + K-Means (XES/CSV por cluster)
  5. analise_violencia_mulher.py — SLA violência doméstica/protetiva (Lei Maria da Penha + CNJ 385/2021)
"""

import argparse
import shutil
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def check_graphviz() -> None:
    """Avisa se Graphviz não está instalado — DFG/Petri Net/BPMN precisam dele."""
    if shutil.which("dot") is None:
        print("=" * 60)
        print("  AVISO: Graphviz não encontrado no PATH.")
        print("  Gráficos de DFG, Petri Net e BPMN serão pulados.")
        print("  Para instalar: brew install graphviz")
        print("=" * 60)


def run(label: str, cmd: list[str]) -> bool:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"\n[ERRO] Etapa falhou (código {result.returncode}). Continuando...")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo de análises de process mining."
    )
    parser.add_argument(
        "--classe", default="Ação Penal - Procedimento Ordinário",
        help="Classe processual (default: Ação Penal - Procedimento Ordinário)"
    )
    parser.add_argument(
        "--data-inicio", default="2020-01-01",
        help="Início da janela temporal — 1º evento >= esta data (default: 2020-01-01)"
    )
    parser.add_argument(
        "--data-fim", default="2026-05-16",
        help="Fim da janela temporal — último evento <= esta data (default: 2026-05-16)"
    )
    parser.add_argument(
        "--tribunal", default=None,
        help="Restringir a um tribunal (default: todos)"
    )
    parser.add_argument(
        "--top-variantes", type=int, default=10, metavar="N",
        help="Exportar log extra com top N caminhos mais frequentes (default: 10)"
    )
    parser.add_argument(
        "--k", type=int, default=4,
        help="Número de clusters K-Means para agrupar.py (default: 4)"
    )
    parser.add_argument(
        "--ano-dfg", type=int, default=None, metavar="YYYY",
        help="Filtrar DFG/Petri Net por ano de ajuizamento (ex: 2025). "
             "Reduz tamanho dos grafos para logs grandes. (default: sem filtro)"
    )
    parser.add_argument(
        "--dfg-min-pct", type=float, default=2.0, metavar="PCT",
        help="Arcos DFG com freq >= PCT%% do máximo (default: 2.0)"
    )
    args = parser.parse_args()

    py = sys.executable
    tribunal_args = ["--tribunal", args.tribunal] if args.tribunal else []

    etapas = [
        (
            "Etapa 1/5 — Exportar log filtrado (casos fechados) + top variantes",
            [py, "analises/exportar_filtrado.py",
             "--classe", args.classe,
             "--top-variantes", str(args.top_variantes),
             *tribunal_args],
        ),
        (
            "Etapa 2/5 — Relatório de happy path com janela temporal",
            [py, "analises/happy_path_report.py",
             "--classe",      args.classe,
             "--data-inicio", args.data_inicio,
             "--data-fim",    args.data_fim,
             *tribunal_args],
        ),
        (
            "Etapa 3/5 — Análise PM4Py completa (PNGs em analises/imgs/)",
            [py, "analises/analisar.py",
             "--classe", args.classe,
             "--dfg-min-pct", str(args.dfg_min_pct),
             *(["--ano", str(args.ano_dfg)] if args.ano_dfg else []),
             *tribunal_args],
        ),
        (
            "Etapa 4/5 — Agrupamento por variante + K-Means",
            [py, "analises/agrupar.py",
             "--classe", args.classe,
             "--k", str(args.k),
             "--top-variantes", str(args.top_variantes),
             *tribunal_args],
        ),
        (
            "Etapa 5/5 — SLA Violência Doméstica/Protetiva (Lei Maria da Penha + CNJ Res. 254/2018)",
            [py, "analises/analise_violencia_mulher.py",
             "--sla-liminar", "2",
             "--sla-total",   "365"],
        ),
    ]

    check_graphviz()

    print(f"\n{'#'*60}")
    print(f"  PIPELINE PM² — {args.classe}")
    print(f"  Janela (início E fim dentro de): {args.data_inicio} → {args.data_fim}")
    if args.tribunal:
        print(f"  Tribunal: {args.tribunal}")
    print(f"{'#'*60}")

    resultados = []
    for label, cmd in etapas:
        ok = run(label, cmd)
        resultados.append((label, ok))

    print(f"\n{'#'*60}")
    print("  RESUMO")
    print(f"{'#'*60}")
    for label, ok in resultados:
        status = "✓" if ok else "✗ FALHOU"
        print(f"  {status}  {label.split('—')[1].strip()}")

    print(f"\n  Outputs em:")
    print(f"    output/          → CSV, XES filtrados, happy path, clusters, SLA violência")
    print(f"    analises/imgs/   → PNGs PM4Py, clusters e SLA violência")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
