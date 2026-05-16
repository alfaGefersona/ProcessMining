#!/usr/bin/env python3
"""
Análise SLA — Ação Penal - Procedimento Ordinário: Violência contra a Mulher
e Medida Protetiva (TJPR, 2023–2026).

Metodologia PM² — Análise Especializada (Perspectiva Legal e Urgência)

Contexto legal:
  - Lei Maria da Penha (Lei 11.340/2006) art. 18: medida protetiva de urgência
    deve ser decidida em 48 horas pelo juiz de 1º grau após comunicação policial.
  - CNJ Resolução 254/2018: prioridade de tramitação para casos de violência
    doméstica em todos os graus de jurisdição.
  - CF art. 5º, LXXVIII: garantia de razoável duração do processo.

Filtro de assuntos (case:assunto_principal):
  - Contra a Mulher
  - Lesão Cometida em Razão da Condição de Mulher
  - Crime de Descumprimento de Medida Protetiva de Urgência
  - Violência Psicológica contra a Mulher
  - Doméstica (qualquer assunto contendo esse termo)

SLAs monitorados:
  - Ajuizamento → Liminar    (medida cautelar/protetiva — objetivo: ≤ 2 dias)
  - Ajuizamento → Trânsito   (encerramento total — alerta padrão: 365 dias)

Saídas:
  analises/imgs/violencia_sla_liminar.png       — tempo até liminar (box+swarm)
  analises/imgs/violencia_sla_total.png         — tempo total por categoria
  analises/imgs/violencia_vs_geral.png          — comparação violência vs. outros AP
  analises/imgs/violencia_por_cluster.png       — distribuição por cluster K-Means
  analises/imgs/violencia_sla_cumprimento.png   — % casos dentro do SLA por faixa
  output/violencia_sla_detalhado.csv            — 1 linha/caso: SLAs + alertas
  output/violencia_sla_resumo.txt               — resumo executivo

Uso:
    python analises/analise_violencia_mulher.py
    python analises/analise_violencia_mulher.py --sla-liminar 2 --sla-total 365
"""

import argparse
import glob
import os
import sys
import warnings

warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "output")
IMG_DIR = os.path.join(ROOT, "analises", "imgs")
os.makedirs(IMG_DIR, exist_ok=True)

# ==============================================================================
# CONSTANTES LEGAIS
# ==============================================================================

# Dias — referências legais
SLA_LIMINAR_URGENCIA_DIAS = 2      # 48h — Lei Maria da Penha art. 18
SLA_TOTAL_ALERTA_DIAS     = 365    # alerta de duração total — CNJ Res. 254/2018

ASSUNTOS_VIOLENCIA = {
    "Análogo à Lesão Corporal em Razão da Condição de Mulher",
    "Contra a Mulher",
    "Contra a mulher",
    "Crime de Descumprimento de Medida Protetiva  de Urgência",
    "Descumprimento de Medida Protetiva de Urgência",
    "Feminicídio",
    "Lesão Cometida em Razão da Condição de Mulher",
    "Violência Doméstica Contra a Mulher",
    "Violência Psicológica contra a Mulher",
}

# Atividades que marcam cada etapa de SLA
# ATIV_AJUIZAMENTO é fallback — AP Ordinária usa case:data_ajuizamento como fonte primária
ATIV_AJUIZAMENTO = {"Petição - Petição inicial", "Recebimento da Petição Inicial"}
ATIV_LIMINAR     = {"Liminar"}
ATIV_TRANSITO    = {"Trânsito em julgado"}

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def _find_latest_csv(pattern: str, excludes: list[str]) -> str | None:
    """Retorna o CSV mais recente que não contém nenhuma das strings em excludes."""
    candidates = sorted([
        f for f in glob.glob(pattern)
        if not any(x in os.path.basename(f) for x in excludes)
    ])
    return candidates[-1] if candidates else None


def load_event_log(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True)
    df["case_id"] = df["case:concept:name"].astype(str)
    return df


def load_features(features_path: str) -> pd.DataFrame:
    df = pd.read_csv(features_path)
    df["case_id"] = df["case_id"].astype(str)
    return df


def is_violencia(assunto: str) -> bool:
    if pd.isna(assunto):
        return False
    return assunto in ASSUNTOS_VIOLENCIA


def categoria(assunto: str) -> str:
    if pd.isna(assunto) or assunto not in ASSUNTOS_VIOLENCIA:
        return "Outros"
    if "Protetiva" in assunto or "Descumprimento" in assunto:
        return "Desc. Medida Protetiva"
    if assunto == "Feminicídio":
        return "Feminicídio"
    if "Lesão" in assunto or "Análogo" in assunto:
        return "Lesão/Condição de Mulher"
    if "Psicológica" in assunto:
        return "Violência Psicológica"
    if "Contra a Mulher" in assunto or "Contra a mulher" in assunto \
            or "Doméstica" in assunto:
        return "Contra a Mulher"
    return "Outros"


def first_ts(group: pd.DataFrame, atividades: set) -> pd.Timestamp | None:
    mask = group["concept:name"].isin(atividades)
    rows = group.loc[mask, "time:timestamp"]
    return rows.min() if not rows.empty else None


def _ts_ajuizamento(grp: pd.DataFrame) -> "pd.Timestamp | None":
    """
    Retorna timestamp do ajuizamento, priorizando:
    1. case:data_ajuizamento (atributo do caso — fonte mais confiável para AP Ordinária
       onde a peça inicial é Denúncia/Queixa, não "Petição inicial" civil)
    2. Primeira ocorrência de ATIV_AJUIZAMENTO (fallback)
    3. Primeiro evento do caso (fallback final)
    """
    col = "case:data_ajuizamento"
    if col in grp.columns:
        raw = grp[col].iloc[0]
        if pd.notna(raw):
            try:
                ts = pd.to_datetime(str(raw), utc=True, errors="coerce")
                if pd.notna(ts):
                    return ts
            except Exception:
                pass
    # Fallback 1: atividade de ajuizamento
    ts_act = first_ts(grp, ATIV_AJUIZAMENTO)
    if ts_act is not None:
        return ts_act
    # Fallback 2: primeiro evento do caso
    return grp["time:timestamp"].min()


def compute_slas(df_log: pd.DataFrame) -> pd.DataFrame:
    """Para cada case_id calcula os timestamps das etapas e os SLAs em dias."""
    records = []
    for case_id, grp in df_log.groupby("case_id"):
        grp = grp.sort_values("time:timestamp")
        assunto = grp["case:assunto_principal"].iloc[0]
        orgao   = grp["case:orgao_julgador"].iloc[0]

        ts_ajuiz = _ts_ajuizamento(grp)
        ts_lim   = first_ts(grp, ATIV_LIMINAR)
        ts_tran  = first_ts(grp, ATIV_TRANSITO)

        sla_liminar = (
            (ts_lim - ts_ajuiz).total_seconds() / 86400
            if ts_lim is not None and ts_ajuiz is not None else None
        )
        sla_total = (
            (ts_tran - ts_ajuiz).total_seconds() / 86400
            if ts_tran is not None and ts_ajuiz is not None else None
        )

        records.append({
            "case_id":          case_id,
            "assunto":          assunto,
            "categoria":        categoria(assunto),
            "violencia":        is_violencia(str(assunto)),
            "orgao":            orgao,
            "ts_ajuizamento":   ts_ajuiz,
            "ts_liminar":       ts_lim,
            "ts_transito":      ts_tran,
            "sla_liminar_dias": sla_liminar,
            "sla_total_dias":   sla_total,
            "tem_liminar":      ts_lim is not None,
            "alerta_liminar":   (sla_liminar is not None and sla_liminar > SLA_LIMINAR_URGENCIA_DIAS),
        })

    return pd.DataFrame(records)


# ==============================================================================
# VISUALIZAÇÕES
# ==============================================================================

COLORS = {
    "violencia": "#d62728",
    "outros":    "#1f77b4",
    "ok":        "#2ca02c",
    "alerta":    "#ff7f0e",
    "critico":   "#d62728",
}


def plot_sla_liminar(df_viol: pd.DataFrame, sla_ref: float, out: str) -> None:
    """Boxplot + jitter: dias até liminar, violência/protetiva, por categoria."""
    df = df_viol[df_viol["tem_liminar"] & df_viol["sla_liminar_dias"].notna()].copy()
    if df.empty:
        return

    cats = df["categoria"].value_counts().index.tolist()
    fig, ax = plt.subplots(figsize=(10, 5))

    data_by_cat = [df.loc[df["categoria"] == c, "sla_liminar_dias"].values for c in cats]
    bp = ax.boxplot(data_by_cat, patch_artist=True, widths=0.5,
                    medianprops=dict(color="black", linewidth=2))
    for patch in bp["boxes"]:
        patch.set_facecolor("#f4a0a0")

    for i, (cat, vals) in enumerate(zip(cats, data_by_cat)):
        jitter = np.random.uniform(-0.15, 0.15, size=len(vals))
        ax.scatter(np.full(len(vals), i + 1) + jitter, vals,
                   alpha=0.7, s=40, color=COLORS["critico"], zorder=5)

    ax.axhline(sla_ref, color=COLORS["alerta"], linewidth=1.5, linestyle="--",
               label=f"Referência urgência: {sla_ref} dias")
    ax.set_xticks(range(1, len(cats) + 1))
    ax.set_xticklabels(cats, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("Dias até Liminar")
    ax.set_title("SLA: Ajuizamento → Liminar — Casos de Violência/Protetiva (TJPR 2023–2026)", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_sla_total(df_viol: pd.DataFrame, out: str, sla_alerta: float = 365.0) -> None:
    """
    Boxplot por categoria: distribuição de duração total — violência/protetiva.

    Substituiu o gráfico de 1 barra/caso (ilegível com 8.585 casos → 13 MB).
    Boxplot mostra mediana, IQR e outliers por categoria — legível em qualquer volume.
    """
    df = df_viol[df_viol["sla_total_dias"].notna()].copy()
    if df.empty:
        return

    palette = {
        "Desc. Medida Protetiva":    "#d62728",
        "Lesão/Condição de Mulher":  "#ff7f0e",
        "Contra a Mulher":           "#9467bd",
        "Violência Psicológica":     "#8c564b",
        "Feminicídio":               "#e377c2",
    }

    # Ordenar categorias por mediana descendente
    cats = (
        df.groupby("categoria")["sla_total_dias"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    data_by_cat = [df.loc[df["categoria"] == c, "sla_total_dias"].values for c in cats]

    # Rótulos com n e % acima do alerta
    labels_ext = []
    for c, vals in zip(cats, data_by_cat):
        n        = len(vals)
        pct_acim = (vals > sla_alerta).mean() * 100
        med      = np.median(vals)
        labels_ext.append(f"{c}\nn={n:,}  med={med:.0f}d\n{pct_acim:.0f}% >{sla_alerta:.0f}d")

    fig, ax = plt.subplots(figsize=(13, 6))
    bp = ax.boxplot(
        data_by_cat,
        patch_artist=True,
        widths=0.55,
        showfliers=True,
        flierprops=dict(marker=".", markersize=3, alpha=0.4),
        medianprops=dict(color="black", linewidth=2),
    )
    for patch, cat in zip(bp["boxes"], cats):
        patch.set_facecolor(palette.get(cat, "#aec7e8"))
        patch.set_alpha(0.7)

    ax.axhline(sla_alerta, color="red", linewidth=1.5, linestyle="--",
               label=f"{sla_alerta:.0f} dias (CNJ Res. 254/2018)")
    ax.set_xticks(range(1, len(cats) + 1))
    ax.set_xticklabels(labels_ext, fontsize=8.5)
    ax.set_ylabel("Dias (ajuizamento → trânsito)")
    ax.set_title(
        "Duração Total por Categoria — Violência/Protetiva (TJPR 2023–2026)\n"
        "Boxplot: mediana, IQR, outliers",
        fontsize=11,
    )
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_vs_geral(df_sla: pd.DataFrame, out: str) -> None:
    """Violin: SLA total — violência vs. outros AP."""
    df = df_sla[df_sla["sla_total_dias"].notna()].copy()
    if df.empty:
        return

    grupos = ["Violência/Protetiva", "Outros AP"]
    data   = [
        df.loc[df["violencia"],  "sla_total_dias"].values,
        df.loc[~df["violencia"], "sla_total_dias"].values,
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    parts = ax.violinplot(data, positions=[1, 2], showmedians=True, showextrema=True)
    for i, (pc, cor) in enumerate(zip(parts["bodies"], [COLORS["critico"], COLORS["outros"]])):
        pc.set_facecolor(cor)
        pc.set_alpha(0.6)

    ax.set_xticks([1, 2])
    ax.set_xticklabels(grupos, fontsize=11)
    ax.set_ylabel("Dias (ajuizamento → trânsito)")
    ax.set_title("Duração Total: Violência/Protetiva vs. Outros AP (TJPR)", fontsize=11)

    for i, (pos, vals) in enumerate(zip([1, 2], data)):
        if len(vals) == 0:
            continue
        med = np.median(vals)
        ax.text(pos + 0.15, med, f"med={med:.0f}d", fontsize=9, va="center",
                color=COLORS["critico"] if i == 0 else COLORS["outros"])

    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_por_cluster(df_sla: pd.DataFrame, df_feat: pd.DataFrame, out: str) -> None:
    """Stacked bar: proporção violência por cluster K-Means."""
    merged = df_sla.merge(
        df_feat[["case_id", "cluster_kmeans"]], on="case_id", how="left"
    )
    merged = merged[merged["cluster_kmeans"].notna()]

    # Labels dinâmicos baseados nos dados reais
    cluster_info = merged.groupby("cluster_kmeans")["case_id"].count()
    cluster_labels = {
        int(cid): f"Cluster {int(cid)}\n({n} casos)"
        for cid, n in cluster_info.items()
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    clusters = sorted(merged["cluster_kmeans"].unique())
    xs = range(len(clusters))

    for j, cl in enumerate(clusters):
        sub = merged[merged["cluster_kmeans"] == cl]
        n_total  = len(sub)
        n_viol   = sub["violencia"].sum()
        n_outros = n_total - n_viol
        ax.bar(j, n_viol,   color=COLORS["critico"], label="Violência/Protetiva" if j == 0 else "")
        ax.bar(j, n_outros, bottom=n_viol, color=COLORS["outros"], label="Outros AP" if j == 0 else "")
        ax.text(j, n_total + 0.3, f"{n_viol}/{n_total}", ha="center", fontsize=9)

    ax.set_xticks(list(xs))
    ax.set_xticklabels([cluster_labels.get(int(c), f"C{c}") for c in clusters],
                       fontsize=8.5)
    ax.set_ylabel("Nº de casos")
    ax.set_title("Distribuição por Cluster K-Means — Violência/Protetiva vs. Outros AP", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_cumprimento_sla(df_viol: pd.DataFrame, sla_ref: float, out: str) -> None:
    """Barras: % casos por faixa de prazo de liminar — violência/protetiva."""
    df = df_viol[df_viol["tem_liminar"] & df_viol["sla_liminar_dias"].notna()].copy()
    if df.empty:
        return

    faixas = [
        ("≤ 2 dias\n(urgência)", 0, 2,  COLORS["ok"]),
        ("3–7 dias", 2, 7,              COLORS["alerta"]),
        ("8–30 dias", 7, 30,            "#ff7f0e"),
        ("> 30 dias", 30, float("inf"), COLORS["critico"]),
    ]

    counts = []
    labels = []
    colors = []
    for label, lo, hi, cor in faixas:
        n = ((df["sla_liminar_dias"] > lo) & (df["sla_liminar_dias"] <= hi)).sum()
        counts.append(n)
        labels.append(label)
        colors.append(cor)

    total = sum(counts)
    pcts  = [c / total * 100 if total else 0 for c in counts]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(labels, pcts, color=colors, edgecolor="white", linewidth=0.7)
    for bar, n, pct in zip(bars, counts, pcts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{n} casos\n({pct:.0f}%)", ha="center", fontsize=9)
    ax.set_ylabel("% de casos com liminar")
    ax.set_ylim(0, max(pcts) * 1.3 if pcts else 10)
    ax.set_title(f"Prazo Ajuizamento → Liminar — Violência/Protetiva (n={total} com liminar)", fontsize=11)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


# ==============================================================================
# RELATÓRIO TEXTO
# ==============================================================================

def gerar_resumo(df_sla: pd.DataFrame, df_viol: pd.DataFrame, sla_liminar: float,
                 sla_total: float, out_path: str) -> None:
    v  = df_viol
    g  = df_sla[~df_sla["violencia"]]

    v_lim_med = v["sla_liminar_dias"].median()
    v_lim_max = v["sla_liminar_dias"].max()
    v_tot_med = v["sla_total_dias"].median()
    v_tot_max = v["sla_total_dias"].max()
    g_tot_med = g["sla_total_dias"].median()

    n_lim_ok    = (v["sla_liminar_dias"] <= sla_liminar).sum() if v["sla_liminar_dias"].notna().any() else 0
    n_lim_total = v["tem_liminar"].sum()

    alertas = v[v["alerta_total"]]

    lines = [
        "=" * 65,
        "  ANÁLISE SLA — AÇÃO PENAL — VIOLÊNCIA/PROTETIVA (TJPR 2023–2026)",
        f"  Lei Maria da Penha art. 18 | CNJ Res. 254/2018 | CF art. 5º LXXVIII",
        "=" * 65,
        f"  Total AP no dataset               : {len(df_sla)}",
        f"  Casos violência/protetiva         : {len(v)} ({len(v)/len(df_sla)*100:.1f}%)",
        f"    Desc. Medida Protetiva          : {(v['categoria']=='Desc. Medida Protetiva').sum()}",
        f"    Lesão/Condição de Mulher        : {(v['categoria']=='Lesão/Condição de Mulher').sum()}",
        f"    Contra a Mulher                 : {(v['categoria']=='Contra a Mulher').sum()}",
        f"    Violência Psicológica           : {(v['categoria']=='Violência Psicológica').sum()}",
        f"    Feminicídio                     : {(v['categoria']=='Feminicídio').sum()}",
        "",
        "  SLA: AJUIZAMENTO → LIMINAR",
        f"    Referência legal (urgência)     : ≤ {sla_liminar} dias",
        f"    Casos com liminar concedida     : {n_lim_total}/{len(v)} ({n_lim_total/len(v)*100:.0f}%)",
        (f"    Dentro da referência            : {n_lim_ok}/{n_lim_total} "
         f"({n_lim_ok/n_lim_total*100:.0f}% dos que têm liminar)") if n_lim_total else "    N/A",
        f"    Mediana dias até liminar        : {v_lim_med:.1f} dias" if not pd.isna(v_lim_med) else "    N/A",
        f"    Máximo dias até liminar         : {v_lim_max:.1f} dias" if not pd.isna(v_lim_max) else "    N/A",
        "",
        "  SLA: AJUIZAMENTO → TRÂNSITO EM JULGADO",
        f"    Alerta (>) definido em          : {sla_total} dias",
        f"    Mediana violência/protetiva     : {v_tot_med:.1f} dias" if not pd.isna(v_tot_med) else "    N/A",
        f"    Mediana outros AP               : {g_tot_med:.1f} dias" if not pd.isna(g_tot_med) else "    N/A",
        f"    Máximo violência/protetiva      : {v_tot_max:.1f} dias" if not pd.isna(v_tot_max) else "    N/A",
        f"    Casos acima do alerta           : {len(alertas)}/{len(v)} ({len(alertas)/len(v)*100:.0f}%)",
        "",
        f"  CASOS CRÍTICOS (duração total > {sla_total:.0f} dias):",
    ]

    if alertas.empty:
        lines.append("    Nenhum caso acima do limiar.")
    else:
        for _, row in alertas.sort_values("sla_total_dias", ascending=False).head(10).iterrows():
            lines.append(
                f"    {str(row['case_id'])[-10:]}  {row['categoria']:<28} "
                f"total={row['sla_total_dias']:.0f}d  "
                f"{'LIMINAR' if row['tem_liminar'] else 'sem liminar'}"
            )

    lines += [
        "",
        "  INTERPRETAÇÃO PM²:",
        "  • Mediana violência/protetiva > outros AP: ausência de prioridade operacional.",
        "  • CNJ Res. 254/2018 exige prioridade de tramitação — não implementada uniformemente.",
        "  • Alta variância indica ausência de SLA interno padronizado nas varas.",
        "  • Sugestão: criar flag automático no PJe para assuntos de violência/protetiva",
        "    com meta de 365 dias (CNJ Res. 254/2018).",
        "=" * 65,
        "",
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))


# ==============================================================================
# MAIN
# ==============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Análise SLA — Ação Penal Violência/Protetiva TJPR"
    )
    parser.add_argument("--sla-liminar", type=float, default=SLA_LIMINAR_URGENCIA_DIAS,
                        help=f"Referência urgência para liminar em dias (padrão: {SLA_LIMINAR_URGENCIA_DIAS})")
    parser.add_argument("--sla-total", type=float, default=SLA_TOTAL_ALERTA_DIAS,
                        help=f"Alerta para duração total em dias (padrão: {SLA_TOTAL_ALERTA_DIAS})")
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Localizar arquivos
    # ------------------------------------------------------------------
    EXCLUDE = ["features", "transicoes", "variante", "kmeans", "cluster",
               "resumo", "conformance", "relatorio", "sla", "happy"]

    raw_csv = _find_latest_csv(
        os.path.join(OUT_DIR, "TJPR_Acao_Penal___Procedimento_Ordinario_2*.csv"), EXCLUDE
    )
    if not raw_csv:
        sys.exit("[ERRO] Nenhum event log CSV de Ação Penal encontrado em output/. "
                 "Rode run_pipeline.py primeiro.")

    feat_csv = _find_latest_csv(
        os.path.join(OUT_DIR, "TJPR_Acao_Penal___Procedimento_Ordinario_*features_kmeans.csv"), []
    )

    print(f"[INFO] Event log  : {os.path.basename(raw_csv)}")
    print(f"[INFO] Features   : {os.path.basename(feat_csv) if feat_csv else 'não encontrado (cluster plot será omitido)'}")

    # ------------------------------------------------------------------
    # 2. Carregar e computar SLAs
    # ------------------------------------------------------------------
    df_log  = load_event_log(raw_csv)
    df_sla  = compute_slas(df_log)

    # Aplicar alerta_total com threshold configurável via --sla-total
    df_sla["alerta_total"] = df_sla["sla_total_dias"].gt(args.sla_total)

    df_feat = load_features(feat_csv) if feat_csv else None

    df_viol = df_sla[df_sla["violencia"]].copy()
    print(f"[INFO] Casos violência/protetiva : {len(df_viol)} / {len(df_sla)}")

    if df_viol.empty:
        sys.exit("[AVISO] Nenhum caso de violência/protetiva encontrado no dataset.")

    # ------------------------------------------------------------------
    # 3. Gerar visualizações
    # ------------------------------------------------------------------
    print("[INFO] Gerando visualizações...")

    plot_sla_liminar(
        df_viol, args.sla_liminar,
        os.path.join(IMG_DIR, "violencia_sla_liminar.png")
    )
    plot_sla_total(
        df_viol,
        os.path.join(IMG_DIR, "violencia_sla_total.png")
    )
    plot_vs_geral(
        df_sla,
        os.path.join(IMG_DIR, "violencia_vs_geral.png")
    )
    plot_cumprimento_sla(
        df_viol, args.sla_liminar,
        os.path.join(IMG_DIR, "violencia_sla_cumprimento.png")
    )
    if df_feat is not None:
        plot_por_cluster(
            df_sla, df_feat,
            os.path.join(IMG_DIR, "violencia_por_cluster.png")
        )

    # ------------------------------------------------------------------
    # 4. Exportar CSV detalhado
    # ------------------------------------------------------------------
    out_csv = os.path.join(OUT_DIR, "violencia_sla_detalhado.csv")
    df_viol_export = df_viol[[
        "case_id", "assunto", "categoria", "orgao",
        "ts_ajuizamento", "ts_liminar", "ts_transito",
        "sla_liminar_dias", "sla_total_dias",
        "tem_liminar", "alerta_liminar", "alerta_total",
    ]].sort_values("sla_total_dias", ascending=False)
    df_viol_export.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[INFO] CSV exportado: {out_csv}")

    # ------------------------------------------------------------------
    # 5. Resumo textual
    # ------------------------------------------------------------------
    out_txt = os.path.join(OUT_DIR, "violencia_sla_resumo.txt")
    gerar_resumo(df_sla, df_viol, args.sla_liminar, args.sla_total, out_txt)
    print(f"[INFO] Resumo exportado: {out_txt}")
    print("[INFO] Análise concluída.")


if __name__ == "__main__":
    main()
