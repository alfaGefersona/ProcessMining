"""
Agrupamento (Clustering) de casos processuais.

Executa dois tipos de agrupamento complementares:

  1. AGRUPAMENTO POR VARIANTE
     Agrupa casos por sequência exata de atividades (variante).
     Cada grupo = todos os processos que seguiram o mesmo caminho.
     Útil para: análise do happy path, comparação de caminhos alternativos.

  2. AGRUPAMENTO POR COMPORTAMENTO (K-Means)
     Agrupa casos por features extraídas: duração, n° de eventos,
     n° de atividades únicas, presença de marcos processuais.
     Usa K-Means (sklearn) com normalização Z-score.
     Útil para: identificar perfis de processo sem depender da sequência exata.

Saídas geradas em output/:
  {TRIBUNAL}_{slug}_{ts}_cluster_variante_{i}.xes/.csv   — um arquivo por variante (top N)
  {TRIBUNAL}_{slug}_{ts}_cluster_kmeans_{i}.xes/.csv     — um arquivo por cluster K-Means
  analises/imgs/{TRIBUNAL}_{slug}_clusters.png           — visualização dos clusters

Uso:
    python analises/agrupar.py
    python analises/agrupar.py --classe "Procedimento Comum Cível" --tribunal TJPR
    python analises/agrupar.py --k 4 --top-variantes 10
    python analises/agrupar.py --so-variantes    # pula K-Means
    python analises/agrupar.py --so-kmeans       # pula agrupamento por variante
"""

import argparse
import glob
import os
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pm4py

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "output")
IMG_DIR = os.path.join(ROOT, "analises", "imgs")
os.makedirs(IMG_DIR, exist_ok=True)

TRIBUNAIS_PADRAO = ["TJPR"]

# Marcos processuais para features booleanas — Ação Penal (CPP arts. 394-405)
MARCOS = {
    "tem_liminar":         lambda acts: any("Liminar" in a for a in acts),
    "tem_sentenca":        lambda acts: any("Procedência" in a or "Improcedência" in a
                                            or "Extinção" in a or "Sentença" in a for a in acts),
    "tem_acordao":         lambda acts: any("Acórdão" in a for a in acts),
    "tem_transito":        lambda acts: "Trânsito em julgado" in acts,
    "tem_recurso":         lambda acts: any("Recurso" in a or "Agravo" in a
                                            or "Embargos" in a or "Apelação" in a for a in acts),
    "tem_redistribuicao":  lambda acts: any("Redistribuição" in a for a in acts),
    "tem_audiencia":       lambda acts: any("Audiência" in a for a in acts),
    "tem_desistencia":     lambda acts: any("Desistência" in a for a in acts),
    "tem_incompetencia":   lambda acts: any("Incompetência" in a
                                            or "competência" in a.lower() for a in acts),
}

CLUSTER_COLORS = [
    "#4361ee", "#e63946", "#2a9d8f", "#f4a261",
    "#8338ec", "#06d6a0", "#fb8500", "#ef233c",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def fix_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c[5:] if c.startswith("case:case:") else c for c in df.columns]
    return df


def carregar(tribunal: str, classe: str) -> pd.DataFrame | None:
    """Carrega CSV filtrado por classe (prefere arquivo já filtrado, fallback XES)."""
    candidates = sorted([
        f for f in glob.glob(os.path.join(OUT_DIR, f"{tribunal}_{slug(classe)}_*.csv"))
        if "happy_path" not in f and "cluster" not in f and "top" not in f
        and "features" not in f and "kmeans" not in f and "sla" not in f
    ])
    if candidates:
        csv_path = candidates[-1]
        print(f"  {tribunal}: lendo {os.path.basename(csv_path)}")
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True, errors="coerce")
        return fix_colunas(df)

    # fallback: XES bruto
    xes_candidates = sorted([
        f for f in glob.glob(os.path.join(OUT_DIR, f"{tribunal}_*.xes"))
        if "happy_path" not in f and "cluster" not in f and slug(classe) not in f
    ])
    if not xes_candidates:
        print(f"  [ERRO] Nenhum dado para {tribunal}. Execute exportar_filtrado.py primeiro.")
        return None
    xes_path = xes_candidates[-1]
    print(f"  {tribunal}: carregando XES {os.path.basename(xes_path)}...")
    log = pm4py.read_xes(xes_path)
    log_f = pm4py.filter_trace_attribute_values(log, "case:classe", [classe], retain=True)
    df = fix_colunas(pm4py.convert_to_dataframe(log_f))
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True, errors="coerce")
    return df


# ── Extração de features por caso ─────────────────────────────────────────────

def extrair_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói DataFrame com 1 linha por caso e as seguintes features:
      - duracao_dias        : tempo do 1º ao último evento
      - n_eventos           : total de eventos no caso
      - n_atividades_unicas : atividades distintas no caso
      - variante            : sequência completa de atividades (string)
      - n_passos            : número de passos na variante
      - tem_*               : flags booleanas de marcos processuais
    """
    df = df.sort_values(["case:concept:name", "time:timestamp"])

    bounds = df.groupby("case:concept:name")["time:timestamp"].agg(
        data_inicio="min", data_fim="max"
    )
    bounds["duracao_dias"] = (
        (bounds["data_fim"] - bounds["data_inicio"]).dt.total_seconds() / 86400
    ).round(1)

    n_ev = df.groupby("case:concept:name")["concept:name"].agg(
        n_eventos="count",
        n_atividades_unicas="nunique",
    )

    variante = (
        df.groupby("case:concept:name")["concept:name"]
        .apply(" → ".join)
        .rename("variante")
    )

    feats = bounds[["duracao_dias"]].join(n_ev).join(variante)
    feats["n_passos"] = feats["variante"].apply(lambda v: len(v.split(" → ")))

    # Flags de marcos processuais
    acts_por_caso = df.groupby("case:concept:name")["concept:name"].apply(set)
    for col, fn in MARCOS.items():
        feats[col] = acts_por_caso.apply(fn).astype(int)

    # Metadados extras (primeiro valor por caso)
    meta_cols = [c for c in df.columns if c.startswith("case:") and c != "case:concept:name"]
    meta = df.groupby("case:concept:name")[meta_cols].first()

    feats = feats.join(meta)
    return feats.reset_index().rename(columns={"case:concept:name": "case_id"})


# ── Agrupamento 1 — Por Variante ──────────────────────────────────────────────

def agrupar_por_variante(df: pd.DataFrame, feats: pd.DataFrame,
                          top_n: int, tribunal: str, slug_classe: str,
                          ts: str) -> pd.DataFrame:
    """
    Agrupa casos pelas top_n variantes mais frequentes.
    Exporta um XES + CSV por variante.
    Retorna DataFrame resumo dos grupos.
    """
    print(f"\n  [Agrupamento por Variante — top {top_n}]")

    contagem = feats["variante"].value_counts()
    total    = len(feats)
    top_vars = contagem.head(top_n)

    resumo_linhas = []
    for rank, (variante, n_casos) in enumerate(top_vars.items(), start=1):
        casos = feats[feats["variante"] == variante]["case_id"].tolist()
        passos = variante.split(" → ")
        cobertura = n_casos / total * 100

        dur = feats[feats["variante"] == variante]["duracao_dias"]

        print(f"    Variante {rank:2d}: {n_casos:4d} casos ({cobertura:.1f}%)  "
              f"{len(passos)} passos  "
              f"mediana {dur.median():.0f}d")
        print(f"             {' → '.join(passos[:6])}{'…' if len(passos) > 6 else ''}")

        # Exportar XES + CSV para esta variante
        df_grupo = df[df["case:concept:name"].isin(casos)].copy()
        base = f"{tribunal}_{slug_classe}_{ts}_cluster_variante_{rank:02d}"

        df_grupo.to_csv(os.path.join(OUT_DIR, base + ".csv"),
                        index=False, encoding="utf-8-sig")

        try:
            log_grupo = pm4py.filter_log(
                lambda trace, c=set(casos): trace.attributes.get("concept:name", "") in c,
                pm4py.convert_to_event_log(df_grupo),
            )
            pm4py.write_xes(log_grupo, os.path.join(OUT_DIR, base + ".xes"))
        except Exception as e:
            print(f"      [AVISO] XES não gerado para variante {rank}: {e}")

        resumo_linhas.append({
            "tipo":         "variante",
            "grupo":        f"Variante {rank:02d}",
            "n_casos":      n_casos,
            "pct_total":    round(cobertura, 1),
            "duracao_mediana_dias": round(dur.median(), 1),
            "duracao_media_dias":   round(dur.mean(), 1),
            "n_passos":     len(passos),
            "variante_preview": " → ".join(passos[:6]) + ("…" if len(passos) > 6 else ""),
        })

    # Casos fora das top variantes = "Outros"
    outros = feats[~feats["variante"].isin(top_vars.index)]
    if len(outros):
        resumo_linhas.append({
            "tipo":         "variante",
            "grupo":        "Outros",
            "n_casos":      len(outros),
            "pct_total":    round(len(outros) / total * 100, 1),
            "duracao_mediana_dias": round(outros["duracao_dias"].median(), 1),
            "duracao_media_dias":   round(outros["duracao_dias"].mean(), 1),
            "n_passos":     None,
            "variante_preview": f"{contagem.iloc[top_n:].shape[0]} variantes raras",
        })

    return pd.DataFrame(resumo_linhas)


# ── Agrupamento 2 — K-Means ────────────────────────────────────────────────────

def agrupar_kmeans(df: pd.DataFrame, feats: pd.DataFrame,
                   k: int, tribunal: str, slug_classe: str, ts: str) -> pd.DataFrame:
    """
    K-Means clustering nas features numéricas + flags booleanas.
    Exporta um XES + CSV por cluster.
    Retorna DataFrame resumo com perfil de cada cluster.
    """
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import KMeans
    except ImportError:
        print("  [AVISO] scikit-learn não instalado. Pulando K-Means.")
        print("          Instale: pip install scikit-learn")
        return pd.DataFrame()

    print(f"\n  [K-Means — k={k}]")

    feature_cols = (
        ["duracao_dias", "n_eventos", "n_atividades_unicas", "n_passos"]
        + list(MARCOS.keys())
    )
    X = feats[feature_cols].fillna(0).values

    scaler  = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    feats = feats.copy()
    feats["cluster_kmeans"] = km.fit_predict(X_scaled)

    # Inércia como indicador de qualidade
    print(f"    Inércia (menor = clusters mais coesos): {km.inertia_:.0f}")

    resumo_linhas = []
    for cluster_id in sorted(feats["cluster_kmeans"].unique()):
        grupo = feats[feats["cluster_kmeans"] == cluster_id]
        casos = grupo["case_id"].tolist()
        n     = len(grupo)
        pct   = n / len(feats) * 100

        dur   = grupo["duracao_dias"]
        n_ev  = grupo["n_eventos"]

        # Perfil do cluster: flags de marcos com % de presença
        flags = {col: round(grupo[col].mean() * 100, 0) for col in MARCOS.keys()}
        flag_str = "  ".join(
            f"{col.replace('tem_', '')}:{int(v)}%"
            for col, v in sorted(flags.items(), key=lambda x: -x[1])
            if v >= 30  # mostrar apenas marcos com ≥ 30% de presença
        )

        print(f"    Cluster {cluster_id}: {n:4d} casos ({pct:.1f}%)  "
              f"mediana {dur.median():.0f}d  eventos/caso {n_ev.median():.1f}")
        print(f"             Marcos: {flag_str or '—'}")

        # Variante dominante deste cluster
        top_var = grupo["variante"].value_counts().index[0]
        top_var_steps = top_var.split(" → ")
        print(f"             Variante dominante: "
              f"{' → '.join(top_var_steps[:5])}{'…' if len(top_var_steps) > 5 else ''}")

        # Exportar XES + CSV
        df_grupo = df[df["case:concept:name"].isin(casos)].copy()
        df_grupo["case:concept:name"] = df_grupo["case:concept:name"].astype(str)
        base = f"{tribunal}_{slug_classe}_{ts}_cluster_kmeans_{cluster_id}"
        df_grupo.to_csv(os.path.join(OUT_DIR, base + ".csv"),
                        index=False, encoding="utf-8-sig")
        try:
            pm4py.write_xes(df_grupo, os.path.join(OUT_DIR, base + ".xes"),
                            case_id_key="case:concept:name")
        except Exception as e:
            print(f"      [AVISO] XES não gerado para cluster {cluster_id}: {e}")

        resumo_linhas.append({
            "tipo":                 "kmeans",
            "grupo":                f"Cluster {cluster_id}",
            "n_casos":              n,
            "pct_total":            round(pct, 1),
            "duracao_mediana_dias": round(dur.median(), 1),
            "duracao_media_dias":   round(dur.mean(), 1),
            "eventos_mediana":      round(n_ev.median(), 1),
            "variante_dominante":   " → ".join(top_var_steps[:5]) + ("…" if len(top_var_steps) > 5 else ""),
            **{f"pct_{col}": int(v) for col, v in flags.items()},
        })

    feats.to_csv(
        os.path.join(OUT_DIR, f"{tribunal}_{slug_classe}_{ts}_features_kmeans.csv"),
        index=False, encoding="utf-8-sig",
    )

    return pd.DataFrame(resumo_linhas), feats


# ── Visualização ──────────────────────────────────────────────────────────────

def visualizar(feats_kmeans: pd.DataFrame, resumo_var: pd.DataFrame,
               resumo_km: pd.DataFrame, k: int,
               tribunal: str, slug_classe: str) -> None:
    """
    Gera 4 subplots:
      1. Scatter duracao × n_eventos (colorido por cluster K-Means)
      2. Tamanho dos clusters K-Means (barras)
      3. Duração mediana por cluster K-Means (barras)
      4. Cobertura das top variantes (barras horizontais empilhadas)
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f"Agrupamento de Casos — {tribunal} · {slug_classe.replace('_', ' ')}",
                 fontsize=14, fontweight="bold")

    # ── 1. Scatter K-Means ────────────────────────────────────────────────────
    ax = axes[0, 0]
    if "cluster_kmeans" in feats_kmeans.columns:
        for cid in sorted(feats_kmeans["cluster_kmeans"].unique()):
            sub = feats_kmeans[feats_kmeans["cluster_kmeans"] == cid]
            # Remove outliers extremos para melhor visualização (P95)
            p95_dur = feats_kmeans["duracao_dias"].quantile(0.95)
            p95_ev  = feats_kmeans["n_eventos"].quantile(0.95)
            sub_plot = sub[(sub["duracao_dias"] <= p95_dur) & (sub["n_eventos"] <= p95_ev)]
            color = CLUSTER_COLORS[cid % len(CLUSTER_COLORS)]
            ax.scatter(sub_plot["duracao_dias"], sub_plot["n_eventos"],
                       color=color, alpha=0.5, s=18, label=f"Cluster {cid} (n={len(sub):,})")
        ax.set_xlabel("Duração (dias)")
        ax.set_ylabel("Nº de eventos")
        ax.set_title("Clusters K-Means — Duração × Eventos (P95 cap)")
        ax.legend(fontsize=8)
    else:
        ax.text(0.5, 0.5, "K-Means não executado", ha="center", va="center",
                transform=ax.transAxes)
    ax.grid(alpha=0.3)

    # ── 2. Tamanho dos clusters K-Means ───────────────────────────────────────
    ax = axes[0, 1]
    if not resumo_km.empty:
        grupos = resumo_km["grupo"].tolist()
        sizes  = resumo_km["n_casos"].tolist()
        colors = [CLUSTER_COLORS[i % len(CLUSTER_COLORS)] for i in range(len(grupos))]
        bars = ax.bar(grupos, sizes, color=colors)
        for bar, size in zip(bars, sizes):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{size:,}", ha="center", va="bottom", fontsize=9)
        ax.set_ylabel("Casos")
        ax.set_title("Tamanho dos Clusters K-Means")
    else:
        ax.text(0.5, 0.5, "K-Means não executado", ha="center", va="center",
                transform=ax.transAxes)
    ax.grid(axis="y", alpha=0.3)

    # ── 3. Duração mediana por cluster ────────────────────────────────────────
    ax = axes[1, 0]
    if not resumo_km.empty:
        grupos = resumo_km["grupo"].tolist()
        durs   = resumo_km["duracao_mediana_dias"].tolist()
        colors = [CLUSTER_COLORS[i % len(CLUSTER_COLORS)] for i in range(len(grupos))]
        bars = ax.bar(grupos, durs, color=colors)
        for bar, d in zip(bars, durs):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{d:.0f}d", ha="center", va="bottom", fontsize=9)
        ax.set_ylabel("Dias (mediana)")
        ax.set_title("Duração Mediana por Cluster K-Means")
    else:
        ax.text(0.5, 0.5, "K-Means não executado", ha="center", va="center",
                transform=ax.transAxes)
    ax.grid(axis="y", alpha=0.3)

    # ── 4. Cobertura das top variantes ────────────────────────────────────────
    ax = axes[1, 1]
    if not resumo_var.empty:
        nomes = resumo_var["grupo"].tolist()
        pcts  = resumo_var["pct_total"].tolist()
        colors_var = [CLUSTER_COLORS[i % len(CLUSTER_COLORS)] for i in range(len(nomes))]
        # Horizontal stacked bar (uma única barra 100%)
        left = 0
        for nome, pct, color in zip(nomes, pcts, colors_var):
            ax.barh(0, pct, left=left, color=color, edgecolor="white", linewidth=0.5,
                    label=f"{nome} ({pct:.1f}%)")
            if pct >= 3:
                ax.text(left + pct / 2, 0, f"{pct:.0f}%",
                        ha="center", va="center", fontsize=8, color="white", fontweight="bold")
            left += pct
        ax.set_xlim(0, 100)
        ax.set_xlabel("Cobertura (%)")
        ax.set_yticks([])
        ax.set_title("Cobertura das Top Variantes")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15),
                  ncol=2, fontsize=7)
    else:
        ax.text(0.5, 0.5, "Sem dados de variantes", ha="center", va="center",
                transform=ax.transAxes)

    plt.tight_layout()
    out_path = os.path.join(IMG_DIR, f"{tribunal}_{slug_classe}_clusters.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  → {out_path}")




# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agrupamento de casos processuais (variante + K-Means)."
    )
    parser.add_argument("--classe",       default="Ação Penal - Procedimento Ordinário")
    parser.add_argument("--tribunal",     default=None)
    parser.add_argument("--k",            type=int, default=4,
                        help="Número de clusters K-Means (default: 4)")
    parser.add_argument("--top-variantes", type=int, default=10,
                        help="Top N variantes para agrupamento por variante (default: 10)")
    parser.add_argument("--so-variantes", action="store_true",
                        help="Executar apenas agrupamento por variante (pular K-Means)")
    parser.add_argument("--so-kmeans",    action="store_true",
                        help="Executar apenas K-Means (pular agrupamento por variante)")
    args = parser.parse_args()

    tribunais   = [args.tribunal] if args.tribunal else TRIBUNAIS_PADRAO
    slug_classe = slug(args.classe)
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"  Agrupamento de Casos")
    print(f"  Classe:    {args.classe}")
    print(f"  Tribunais: {', '.join(tribunais)}")
    print(f"  K-Means k: {args.k}")
    print(f"  Top vars:  {args.top_variantes}")
    print(f"{'='*60}")

    for tribunal in tribunais:
        print(f"\n[{tribunal}]")

        df = carregar(tribunal, args.classe)
        if df is None:
            continue

        n_casos = df["case:concept:name"].nunique()
        print(f"  {n_casos:,} casos carregados")

        if n_casos < 10:
            print(f"  [AVISO] Poucos casos para agrupamento significativo.")
            continue

        # Extrair features
        feats = extrair_features(df)

        resumo_var = pd.DataFrame()
        resumo_km  = pd.DataFrame()
        feats_km   = feats.copy()

        # ── Agrupamento por variante
        if not args.so_kmeans:
            top_n_efetivo = min(args.top_variantes, feats["variante"].nunique())
            resumo_var = agrupar_por_variante(
                df, feats, top_n_efetivo, tribunal, slug_classe, ts
            )

        # ── K-Means
        if not args.so_variantes:
            k_efetivo = min(args.k, n_casos // 3)  # mínimo 3 casos por cluster
            result = agrupar_kmeans(df, feats, k_efetivo, tribunal, slug_classe, ts)
            if isinstance(result, tuple):
                resumo_km, feats_km = result

        # Visualização
        visualizar(feats_km, resumo_var, resumo_km, args.k, tribunal, slug_classe)

    print(f"\n{'='*60}")
    print(f"  Outputs em: output/  e  analises/imgs/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
