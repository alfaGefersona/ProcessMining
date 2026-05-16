"""
Relatório de Happy Path por tribunal.

Filtra processos que INICIARAM e ENCERRARAM dentro da janela temporal,
identifica os que seguiram o caminho feliz (CPC 2015) e exporta:

  output/{TRIBUNAL}_{slug}_{ts}_happy_path.csv          — 1 linha por processo
  output/{TRIBUNAL}_{slug}_{ts}_happy_path_transicoes.csv — 1 linha por transição A→B
  output/{TRIBUNAL}_{slug}_{ts}_happy_path.xes           — log XES (importar no Disco)

Uso:
    python analises/happy_path_report.py
    python analises/happy_path_report.py \\
        --classe "Procedimento Comum Cível" \\
        --data-inicio 2015-01-01 \\
        --data-fim 2020-12-31
    python analises/happy_path_report.py --tribunal TJRS
"""

import argparse
import glob
import os
import re
import sys
import warnings
from datetime import datetime, timezone

warnings.filterwarnings("ignore")

import pm4py
import pandas as pd

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "output")
TRIBUNAIS_PADRAO = ["TJPR"]

# ── Critérios de Happy Path — Ação Penal - Procedimento Ordinário (CPP arts. 394-405) ──────
# Nível 1 (IDEAL): Trânsito em julgado ou baixa + sem recurso + sem desvio admin
# Nível 2 (CONCLUÍDO): Qualquer atividade terminal AP + pode ter desvio admin, sem recurso
# Nível 3 (BAIXA): Somente Baixa Definitiva presente

TERMINAL_MERITO = {
    "Trânsito em julgado",
    "Baixa Definitiva",
    "Definitivo",
    "Procedência",
    "Improcedência",
    "Procedência em Parte",
    "Extinção",
}

DESVIO_RECURSIVO = {
    "Petição - Apelação",
    "Petição - Recurso em Sentido Estrito",
    "Petição - Agravo (inominado/ legal)",
    "Não Conhecimento de recurso",
    "Petição - Embargos de Declaração",
    "Petição - Recurso Ordinário",
    "Petição - Habeas Corpus",
}

DESVIO_ADMIN = {
    "Redistribuição - incompetência",
    "Redistribuição - prevenção",
    "Incompetência",
    "Declaração de competência em conflito",
    "Remessa - por declínio de competência entre instâncias do mesmo tribunal",
    "Desistência",
}


def fix_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c[5:] if c.startswith("case:case:") else c for c in df.columns]
    return df


def slug(texto: str) -> str:
    s = texto.replace(" ", "_")
    for src, dst in [
        ("ç","c"),("Ç","C"),("ã","a"),("Ã","A"),("â","a"),("Â","A"),
        ("á","a"),("Á","A"),("à","a"),("À","A"),("é","e"),("É","E"),
        ("ê","e"),("Ê","E"),("í","i"),("Í","I"),("ó","o"),("Ó","O"),
        ("ô","o"),("Ô","O"),("ú","u"),("Ú","U"),("õ","o"),("Õ","O"),
    ]:
        s = s.replace(src, dst)
    return re.sub(r"[^\w]", "_", s)[:40]


def nivel_happy_path(acts: set) -> int:
    """
    Retorna nível do happy path (0 = não happy):
      1 = Ideal: terminal mérito + sem recurso + sem desvio admin
      2 = Concluído: terminal mérito, pode ter desvio admin, sem recurso
      3 = Baixa: apenas Baixa Definitiva presente
      0 = Não happy (em andamento ou com recurso)
    """
    tem_terminal = bool(acts & TERMINAL_MERITO)
    tem_recurso  = bool(acts & DESVIO_RECURSIVO)
    tem_desvio   = bool(acts & DESVIO_ADMIN)
    tem_baixa    = "Baixa Definitiva" in acts

    if not tem_terminal:
        return 0
    if tem_recurso:
        return 0
    if not tem_desvio:
        return 1
    if tem_baixa:
        return 3
    return 2


# ── Carga ─────────────────────────────────────────────────────────────────────

def carregar(tribunal: str, classe: str) -> pd.DataFrame | None:
    # Prefere arquivo já filtrado pela classe (exclui outputs do próprio script)
    candidates = sorted([
        f for f in glob.glob(os.path.join(OUT_DIR, f"{tribunal}_{slug(classe)}_*.csv"))
        if "happy_path" not in os.path.basename(f)
        and "top" not in os.path.basename(f)
        and "cluster" not in os.path.basename(f)
        and "features" not in os.path.basename(f)
        and "sla" not in os.path.basename(f)
    ])
    if not candidates:
        # Fallback: XES completo do tribunal
        xes_candidates = sorted(glob.glob(os.path.join(OUT_DIR, f"{tribunal}_*.xes")))
        xes_candidates = [f for f in xes_candidates if "happy_path" not in f
                          and slug(classe) not in f]
        if not xes_candidates:
            print(f"  [ERRO] Nenhum dado para {tribunal}.")
            return None
        xes_path = xes_candidates[-1]
        print(f"  {tribunal}: carregando XES {os.path.basename(xes_path)} e filtrando classe...")
        log_raw = pm4py.read_xes(xes_path)
        df_raw  = fix_colunas(pm4py.convert_to_dataframe(log_raw))
        # Filtro por classe via DataFrame — independente de versão do PM4Py
        df = df_raw[df_raw["case:classe"] == classe].copy() if "case:classe" in df_raw.columns else df_raw
    else:
        csv_path = candidates[-1]
        print(f"  {tribunal}: lendo {os.path.basename(csv_path)}")
        df = pd.read_csv(csv_path, encoding="utf-8-sig")

    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True, errors="coerce")
    return df


# ── Filtro temporal ───────────────────────────────────────────────────────────

def filtrar_janela(df: pd.DataFrame, inicio: datetime, fim: datetime,
                   tribunal: str) -> pd.DataFrame:
    """
    Mantém apenas processos cujo PRIMEIRO evento >= inicio
    E ÚLTIMO evento <= fim.
    Assim garantimos processos que iniciaram E encerraram dentro da janela.
    """
    bounds = df.groupby("case:concept:name")["time:timestamp"].agg(["min", "max"])
    inicio_tz = pd.Timestamp(inicio).tz_localize("UTC") if inicio.tzinfo is None else pd.Timestamp(inicio)
    fim_tz    = pd.Timestamp(fim).tz_localize("UTC")    if fim.tzinfo is None    else pd.Timestamp(fim)

    dentro = bounds[(bounds["min"] >= inicio_tz) & (bounds["max"] <= fim_tz)].index
    df_filtrado = df[df["case:concept:name"].isin(dentro)].copy()

    n_total  = df["case:concept:name"].nunique()
    n_dentro = len(dentro)
    print(f"         Janela {inicio_tz.date()} → {fim_tz.date()}: "
          f"{n_dentro:,} / {n_total:,} processos ({n_dentro/n_total:.1%}) "
          f"iniciaram E encerraram dentro da janela")
    return df_filtrado


# ── Classificação e enriquecimento ───────────────────────────────────────────

def classificar_processos(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna DataFrame com 1 linha por processo, incluindo nível happy path."""
    df_s = df.sort_values(["case:concept:name", "time:timestamp"])

    # Metadados do processo (primeiro evento = valores canônicos)
    meta_cols = [c for c in df.columns
                 if c.startswith("case:") and c != "case:concept:name"]
    meta = (df_s.groupby("case:concept:name")[meta_cols]
            .first()
            .reset_index())

    # Timestamps e duração
    bounds = (df_s.groupby("case:concept:name")["time:timestamp"]
              .agg(data_inicio="min", data_fim="max")
              .reset_index())
    bounds["duracao_dias"] = (
        (bounds["data_fim"] - bounds["data_inicio"]).dt.total_seconds() / 86400
    ).round(1)

    # Variante (sequência de atividades)
    variante = (df_s.groupby("case:concept:name")["concept:name"]
                .apply(" → ".join)
                .reset_index()
                .rename(columns={"concept:name": "variante"}))

    # N° de atividades únicas e total de eventos
    n_eventos = (df.groupby("case:concept:name")
                 .agg(n_eventos=("concept:name", "count"),
                      n_atividades_unicas=("concept:name", "nunique"))
                 .reset_index())

    # Nível happy path
    por_caso = df.groupby("case:concept:name")["concept:name"].apply(set)
    nivel_df = por_caso.apply(nivel_happy_path).reset_index()
    nivel_df.columns = ["case:concept:name", "nivel_happy_path"]

    nivel_labels = {0: "em_andamento_ou_recurso", 1: "ideal", 2: "concluido", 3: "baixa_definitiva"}
    nivel_df["happy_path_label"] = nivel_df["nivel_happy_path"].map(nivel_labels)

    # Merge tudo
    result = (meta
              .merge(bounds,    on="case:concept:name")
              .merge(variante,  on="case:concept:name")
              .merge(n_eventos, on="case:concept:name")
              .merge(nivel_df,  on="case:concept:name"))

    result = result.rename(columns={"case:concept:name": "case_id"})
    return result


# ── Transições detalhadas ─────────────────────────────────────────────────────

def calcular_transicoes(df: pd.DataFrame, casos_hp: list) -> pd.DataFrame:
    """
    Para processos do happy path, calcula cada transição A → B com:
    - atividade de origem e destino
    - timestamps
    - tempo entre elas (dias)
    - caso e tribunal
    """
    df_hp = df[df["case:concept:name"].isin(casos_hp)].copy()
    df_hp = df_hp.sort_values(["case:concept:name", "time:timestamp"])

    df_hp["atividade_proxima"] = df_hp.groupby("case:concept:name")["concept:name"].shift(-1)
    df_hp["ts_proxima"]        = df_hp.groupby("case:concept:name")["time:timestamp"].shift(-1)
    df_hp["dias_ate_proxima"]  = (
        (df_hp["ts_proxima"] - df_hp["time:timestamp"]).dt.total_seconds() / 86400
    ).round(2)

    transicoes = df_hp.dropna(subset=["atividade_proxima"]).copy()
    transicoes = transicoes[[
        "case:concept:name",
        "concept:name",
        "time:timestamp",
        "atividade_proxima",
        "ts_proxima",
        "dias_ate_proxima",
        "org:resource",
    ]].rename(columns={
        "case:concept:name": "case_id",
        "concept:name":       "atividade_origem",
        "time:timestamp":     "ts_origem",
        "org:resource":       "recurso",
    })

    return transicoes.reset_index(drop=True)


# ── Exportação ────────────────────────────────────────────────────────────────

def exportar_xes_happy_path(df: pd.DataFrame, casos_hp: list,
                             output_path: str) -> None:
    """Exporta XES apenas com processos do happy path."""
    df_hp = df[df["case:concept:name"].isin(casos_hp)].copy()
    df_hp["time:timestamp"] = pd.to_datetime(df_hp["time:timestamp"], utc=True)
    df_hp["case:concept:name"] = df_hp["case:concept:name"].astype(str)

    # pm4py.write_xes aceita DataFrame com case_id_key
    pm4py.write_xes(df_hp, output_path, case_id_key="case:concept:name")
    print(f"         → {os.path.basename(output_path)}")




# ── Resumo ────────────────────────────────────────────────────────────────────

def imprimir_resumo(df_proc: pd.DataFrame, tribunal: str) -> None:
    total = len(df_proc)
    por_nivel = df_proc["nivel_happy_path"].value_counts().sort_index()

    print(f"\n  {'─'*52}")
    print(f"  {tribunal} — resumo (processos na janela temporal)")
    print(f"  {'─'*52}")
    print(f"  Total processos na janela:  {total:,}")
    for nivel, n in por_nivel.items():
        label = {0:"em andamento/recurso", 1:"Happy Path IDEAL",
                 2:"Concluído (c/ desvio admin)", 3:"Baixa Definitiva"}.get(nivel, "?")
        pct = n / total * 100 if total else 0
        print(f"  Nível {nivel} — {label:<30} {n:5,}  ({pct:.1f}%)")

    hp = df_proc[df_proc["nivel_happy_path"] >= 1]
    if len(hp) > 0:
        dur = hp["duracao_dias"]
        print(f"\n  Duração (happy path nível ≥ 1):")
        print(f"    Mediana: {dur.median():.0f}d  |  Média: {dur.mean():.0f}d  "
              f"|  P90: {dur.quantile(0.9):.0f}d")

        # Top 5 variantes do happy path ideal
        ideal = df_proc[df_proc["nivel_happy_path"] == 1]
        if len(ideal) > 0:
            top_v = ideal["variante"].value_counts().head(5)
            print(f"\n  Top 5 variantes — Happy Path Ideal ({len(ideal)} casos):")
            for i, (v, n) in enumerate(top_v.items(), 1):
                acts = v.split(" → ")
                pct  = n / len(ideal) * 100
                print(f"    {i}. {n:3d} casos ({pct:.1f}%)  {len(acts)} atividades")
                print(f"       {' → '.join(acts[:6])}{'…' if len(acts)>6 else ''}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Relatório de happy path por tribunal."
    )
    parser.add_argument("--classe",       default="Ação Penal - Procedimento Ordinário")
    parser.add_argument("--data-inicio",  default="2023-01-01",
                        help="Data de início da janela (YYYY-MM-DD)")
    parser.add_argument("--data-fim",     default="2026-05-12",
                        help="Data de fim da janela (YYYY-MM-DD)")
    parser.add_argument("--tribunal",     default=None,
                        help="Tribunal específico (default: todos)")
    args = parser.parse_args()

    tribunais   = [args.tribunal] if args.tribunal else TRIBUNAIS_PADRAO
    classe      = args.classe
    slug_classe = slug(classe)
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")

    inicio = datetime.strptime(args.data_inicio, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    fim    = datetime.strptime(args.data_fim,    "%Y-%m-%d").replace(tzinfo=timezone.utc)

    print(f"\n{'='*60}")
    print(f"  Happy Path Report")
    print(f"  Classe:  {classe}")
    print(f"  Janela:  {args.data_inicio}  →  {args.data_fim}")
    print(f"{'='*60}")

    for tribunal in tribunais:
        print(f"\n[{tribunal}]")

        df = carregar(tribunal, classe)
        if df is None:
            continue

        df_janela = filtrar_janela(df, inicio, fim, tribunal)

        if df_janela.empty:
            print(f"  Nenhum processo na janela temporal. "
                  f"Verifique se há dados disponíveis ou ajuste as datas.")
            print(f"  → Consulte datajud/config.py para re-extração com filtro de data.")
            continue

        # Classifica todos os processos da janela
        df_proc = classificar_processos(df_janela)
        casos_hp = df_proc[df_proc["nivel_happy_path"] >= 1]["case_id"].tolist()

        imprimir_resumo(df_proc, tribunal)

        base = f"{tribunal}_{slug_classe}_{ts}_happy_path"

        # CSV — todos os processos da janela (com nível happy path)
        csv_all = os.path.join(OUT_DIR, base + ".csv")
        df_proc.to_csv(csv_all, index=False, encoding="utf-8-sig")
        print(f"\n         → {os.path.basename(csv_all)}  ({len(df_proc):,} processos)")

        if casos_hp:
            # CSV transições — apenas happy path
            df_trans = calcular_transicoes(df_janela, casos_hp)
            csv_trans = os.path.join(OUT_DIR, base + "_transicoes.csv")
            df_trans.to_csv(csv_trans, index=False, encoding="utf-8-sig")
            print(f"         → {os.path.basename(csv_trans)}  ({len(df_trans):,} transições)")

            # XES — apenas happy path (para Disco)
            xes_hp = os.path.join(OUT_DIR, base + ".xes")
            exportar_xes_happy_path(df_janela, casos_hp, xes_hp)
        else:
            print(f"\n  Nenhum processo happy path encontrado na janela.")
            print(f"  → TJPR provavelmente requer re-extração com processos fechados.")
            print(f"  → Veja instrução em datajud/config.py.")

    print(f"\n{'='*60}")
    print(f"  Arquivos gerados em: output/")
    print(f"{'='*60}")
    os.system(f'open "{OUT_DIR}"')


if __name__ == "__main__":
    main()
