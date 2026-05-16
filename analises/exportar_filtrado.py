"""
Filtra event log por classe processual e exporta XES + CSV para o Disco.

Apenas casos que possuem INÍCIO (qualquer evento) E FIM (atividade terminal de mérito)
são incluídos. Casos em andamento são excluídos completamente.

Uso:
    python analises/exportar_filtrado.py
    python analises/exportar_filtrado.py --classe "Execução Fiscal"
    python analises/exportar_filtrado.py --classe "Procedimento Comum Cível" --tribunal TJPR

Gera em output/:
    {TRIBUNAL}_{slug_classe}_{timestamp}.xes   — IEEE XES 1.0 (Disco / PM4Py)
    {TRIBUNAL}_{slug_classe}_{timestamp}.csv   — event log plano UTF-8 BOM (Disco / PM4Py)
"""

import argparse
import glob
import os
import re
import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

import pm4py
import pandas as pd

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "output")

TRIBUNAIS_PADRAO = ["TJPR", "TJRS"]

# Atividades que caracterizam o FIM de um processo.
# Casos que não possuem nenhuma dessas atividades são considerados "em andamento"
# e NÃO são incluídos no log exportado.
TERMINAL_MERITO = {
    "Baixa Definitiva",
    "Trânsito em julgado",
    "Definitivo",
    "Procedência",
    "Improcedência",
    "Procedência em Parte",
    "Extinção",
    "Extinção da execução ou do cumprimento da sentença",
    "Provimento",
    "Não-Provimento",
}


def fix_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c[5:] if c.startswith("case:case:") else c for c in df.columns]
    return df


def filtrar_top_variantes(df: pd.DataFrame, top_n: int) -> tuple:
    """
    Mantém apenas casos que seguem uma das top_n variantes mais frequentes.
    Retorna (df_filtrado, n_removidos, tabela_top_variantes).

    Uso: concentrar a análise no comportamento mainstream, descartando
    variantes raras que fragmentam o DFG e dificultam a interpretação.
    """
    df_sorted = df.sort_values(["case:concept:name", "time:timestamp"])
    variante_por_caso = (
        df_sorted.groupby("case:concept:name")["concept:name"]
        .apply(" → ".join)
    )

    contagem = variante_por_caso.value_counts()
    top_variantes = contagem.head(top_n)
    top_set = set(top_variantes.index)

    casos_top = set(variante_por_caso[variante_por_caso.isin(top_set)].index)
    n_total     = df["case:concept:name"].nunique()
    n_removidos = n_total - len(casos_top)

    df_top = df[df["case:concept:name"].isin(casos_top)].copy()

    tabela = pd.DataFrame({
        "rank":     range(1, len(top_variantes) + 1),
        "variante": top_variantes.index,
        "casos":    top_variantes.values,
        "pct":      (top_variantes.values / n_total * 100).round(1),
        "pct_acum": (top_variantes.cumsum().values / n_total * 100).round(1),
    })

    return df_top, n_removidos, tabela


def filtrar_casos_fechados(df: pd.DataFrame) -> tuple:
    """
    Remove casos sem nenhuma atividade terminal (em andamento).
    Opera puramente sobre DataFrame — independente de versão do PM4Py.
    Retorna (df_filtrado, n_removidos).
    """
    casos_com_fim = set(
        df[df["concept:name"].isin(TERMINAL_MERITO)]["case:concept:name"].unique()
    )
    n_total     = df["case:concept:name"].nunique()
    n_removidos = n_total - len(casos_com_fim)
    df_fechados = df[df["case:concept:name"].isin(casos_com_fim)].copy()
    return df_fechados, n_removidos


def slug(texto: str) -> str:
    """'Procedimento Comum Cível' → 'Procedimento_Comum_Civel'"""
    s = texto.replace(" ", "_")
    s = s.replace("ç", "c").replace("Ç", "C")
    s = s.replace("ã", "a").replace("Ã", "A").replace("â", "a").replace("Â", "A")
    s = s.replace("á", "a").replace("Á", "A").replace("à", "a").replace("À", "A")
    s = s.replace("é", "e").replace("É", "E").replace("ê", "e").replace("Ê", "E")
    s = s.replace("í", "i").replace("Í", "I")
    s = s.replace("ó", "o").replace("Ó", "O").replace("ô", "o").replace("Ô", "O")
    s = s.replace("ú", "u").replace("Ú", "U")
    s = s.replace("õ", "o").replace("Õ", "O").replace("ñ", "n")
    s = re.sub(r"[^\w]", "_", s)
    return s[:40]


def exportar(tribunal: str, classe: str, ts: str, top_n: int = 0) -> None:
    # Prefere CSV bruto (main.py pode omitir XES quando disco limitado)
    csv_candidates = sorted([
        f for f in glob.glob(os.path.join(OUT_DIR, f"{tribunal}_[0-9]*.csv"))
        if "happy_path" not in os.path.basename(f)
        and slug(classe) not in os.path.basename(f)
        and "cluster" not in os.path.basename(f)
        and "features" not in os.path.basename(f)
        and "top10v" not in os.path.basename(f)
    ])
    xes_candidates = sorted([
        f for f in glob.glob(os.path.join(OUT_DIR, f"{tribunal}_[0-9]*.xes"))
        if "happy_path" not in os.path.basename(f)
        and slug(classe) not in os.path.basename(f)
    ])

    if not csv_candidates and not xes_candidates:
        print(f"  [ERRO] Nenhum arquivo bruto para {tribunal}. Execute main.py primeiro.")
        return

    if csv_candidates:
        src = csv_candidates[-1]
        print(f"\n  {tribunal}: lendo {os.path.basename(src)}")
        df_full = pd.read_csv(src, encoding="utf-8-sig", low_memory=False)
        df_full = fix_colunas(df_full)
        if "time:timestamp" in df_full.columns:
            df_full["time:timestamp"] = pd.to_datetime(df_full["time:timestamp"], utc=True, errors="coerce")
    else:
        src = xes_candidates[-1]
        print(f"\n  {tribunal}: lendo {os.path.basename(src)}")
        log_raw = pm4py.read_xes(src)
        df_full = fix_colunas(pm4py.convert_to_dataframe(log_raw))

    if "case:classe" not in df_full.columns or classe not in df_full["case:classe"].values:
        print(f"  [ERRO] Classe '{classe}' não encontrada em {tribunal}.")
        available = sorted(df_full.get("case:classe", pd.Series()).dropna().unique())
        print(f"         Disponíveis: {available[:10]}")
        return

    # ── Filtro por classe (DataFrame) ─────────────────────────────────────────
    df_f = df_full[df_full["case:classe"] == classe].copy()
    n_classe = df_f["case:concept:name"].nunique()
    print(f"         {n_classe:,} processos na classe '{classe}'")

    # ── Manter apenas casos com INÍCIO e FIM (atividade terminal) ─────────────
    df_f, n_removidos = filtrar_casos_fechados(df_f)
    n = df_f["case:concept:name"].nunique()
    e = len(df_f)
    print(f"         {n_removidos:,} casos em andamento removidos")
    print(f"         {n:,} processos fechados | {e:,} eventos exportados")

    # ── Filtro de top variantes (opcional) ────────────────────────────────────
    if top_n > 0:
        df_top, n_var_rem, tabela_top = filtrar_top_variantes(df_f, top_n)
        cobertura = tabela_top["pct_acum"].iloc[-1] if len(tabela_top) else 0.0
        print(f"         Top {top_n} variantes: {df_top['case:concept:name'].nunique():,} casos "
              f"({cobertura:.1f}% cobertura) | {n_var_rem:,} casos em variantes raras removidos")
        print(f"         {'Rank':>4}  {'Casos':>6}  {'%':>5}  {'Acum%':>6}  Variante")
        for _, row in tabela_top.iterrows():
            steps = row["variante"].split(" → ")
            preview = " → ".join(steps[:5]) + ("…" if len(steps) > 5 else "")
            print(f"         {int(row['rank']):>4}  {int(row['casos']):>6}  "
                  f"{row['pct']:>4.1f}%  {row['pct_acum']:>5.1f}%  {preview}")

        base_top = f"{tribunal}_{slug(classe)}_top{top_n}v_{ts}"
        df_top["case:concept:name"] = df_top["case:concept:name"].astype(str)
        pm4py.write_xes(df_top, os.path.join(OUT_DIR, base_top + ".xes"),
                        case_id_key="case:concept:name")
        df_top.to_csv(os.path.join(OUT_DIR, base_top + ".csv"),
                      index=False, encoding="utf-8-sig")
        print(f"         → {base_top}.xes / .csv  (top {top_n} variantes)")

    base  = f"{tribunal}_{slug(classe)}_{ts}"
    xes_out  = os.path.join(OUT_DIR, base + ".xes")
    csv_out  = os.path.join(OUT_DIR, base + ".csv")

    # ── XES (DataFrame → XES via PM4Py) ─────────────────────────────────────
    df_f["case:concept:name"] = df_f["case:concept:name"].astype(str)
    pm4py.write_xes(df_f, xes_out, case_id_key="case:concept:name")
    print(f"         → {os.path.basename(xes_out)}")

    # ── CSV (UTF-8 BOM — compatível com Excel e Disco) ───────────────────────
    df_f.to_csv(csv_out, index=False, encoding="utf-8-sig")
    print(f"         → {os.path.basename(csv_out)}")


def main():
    parser = argparse.ArgumentParser(
        description="Exporta event log filtrado por classe processual."
    )
    parser.add_argument(
        "--classe", default="Procedimento Comum Cível",
        help="Classe processual (default: Procedimento Comum Cível)"
    )
    parser.add_argument(
        "--tribunal", default=None,
        help="Tribunal específico (default: todos)"
    )
    parser.add_argument(
        "--top-variantes", type=int, default=0, metavar="N",
        help="Exportar log extra com apenas os N caminhos mais frequentes (0 = desativado)"
    )
    args = parser.parse_args()

    tribunais = [args.tribunal] if args.tribunal else TRIBUNAIS_PADRAO
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"  Classe:    {args.classe}")
    print(f"  Tribunais: {', '.join(tribunais)}")
    if args.top_variantes:
        print(f"  Top variantes: {args.top_variantes}")
    print(f"  Destino:   output/")
    print(f"{'='*60}")

    for t in tribunais:
        exportar(t, args.classe, ts, top_n=args.top_variantes)

    print(f"\n{'='*60}")
    print("  Concluído.")
    print("  File → Import Event Log → selecione os arquivos gerados")
    print("=" * 60)

    os.system(f'open "{OUT_DIR}"')


if __name__ == "__main__":
    main()
