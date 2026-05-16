"""
Executa todas as análises de Process Mining e salva os resultados em analises/imgs/.
Não requer Jupyter — rode diretamente:

    python analises/analisar.py                                    # usa defaults Ação Penal
    python analises/analisar.py --classe "Ação Penal - Procedimento Ordinário"  # classe específica
    python analises/analisar.py --tribunal TJPR                    # tribunal específico
    python analises/analisar.py output/TJPR_*.xes                  # arquivo XES direto
"""

import argparse
import glob
import os
import sys
import warnings

warnings.filterwarnings("ignore")

import pm4py
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # sem janela gráfica — salva direto em arquivo
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"figure.dpi": 130, "figure.figsize": (13, 5)})

IMGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imgs")
os.makedirs(IMGS_DIR, exist_ok=True)

gerados: list[str] = []


# ── Utilitários ───────────────────────────────────────────────────────────────

def salvar(nome: str) -> str:
    path = os.path.join(IMGS_DIR, f"{nome}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    salvo → imgs/{nome}.png")
    gerados.append(path)
    return path


def fix_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    PM4Py prefixa atributos de trace com 'case:' ao converter para DataFrame.
    Como nossos atributos já têm 'case:' (ex: 'case:classe'), o resultado é
    'case:case:classe'. Este fix remove o prefixo duplicado.
    """
    df.columns = [c[5:] if c.startswith("case:case:") else c for c in df.columns]
    return df


def carregar(xes_path: str):
    print(f"\n[1/8] Carregando: {xes_path}")
    log = pm4py.read_xes(xes_path)
    df  = fix_colunas(pm4py.convert_to_dataframe(log))

    n_c = df["case:concept:name"].nunique()
    n_e = len(df)
    n_a = df["concept:name"].nunique()
    print(f"      Processos: {n_c:,} | Eventos: {n_e:,} | Atividades: {n_a:,}")
    return log, df


def filtrar_classe(log, df: pd.DataFrame, classe: str | None = None):
    if classe:
        disponiveis = df["case:classe"].value_counts()
        if classe not in disponiveis.index:
            print(f"      [AVISO] Classe '{classe}' não encontrada. Usando a mais frequente.")
            classe = disponiveis.index[0]
    else:
        classe = df["case:classe"].value_counts().index[0]
    print(f"\n      Classe selecionada: \"{classe}\"")
    log_c = pm4py.filter_trace_attribute_values(log, "case:classe", [classe], retain=True)
    df_c  = fix_colunas(pm4py.convert_to_dataframe(log_c))
    print(f"      Processos nessa classe: {df_c['case:concept:name'].nunique():,}")
    return log_c, df_c, classe


def filtrar_ano(log_or_df, df: pd.DataFrame, ano: int):
    """Filtra casos pelo ano de ajuizamento (case:data_ajuizamento começa com YYYY).
    Aceita EventLog ou DataFrame como primeiro argumento (PM4Py 2.7 retorna DataFrame
    em algumas funções de filtro)."""
    col = "case:data_ajuizamento"
    if col not in df.columns:
        print(f"      [AVISO] {col} não encontrado. Filtro de ano ignorado.")
        return log_or_df, df
    mask     = df[col].astype(str).str.startswith(str(ano))
    casos_no = set(df.loc[mask, "case:concept:name"].unique())
    if not casos_no:
        print(f"      [AVISO] Nenhum caso ajuizado em {ano}.")
        return log_or_df, df

    df_f = df[df["case:concept:name"].isin(casos_no)].copy()

    if isinstance(log_or_df, pd.DataFrame):
        log_f = log_or_df[log_or_df["case:concept:name"].isin(casos_no)].copy()
    else:
        from pm4py.objects.log.obj import EventLog
        log_f = EventLog()
        log_f.attributes = dict(log_or_df.attributes)
        for trace in log_or_df:
            if trace.attributes.get("concept:name") in casos_no:
                log_f.append(trace)

    n = df_f["case:concept:name"].nunique()
    print(f"      Filtro ano={ano}: {n:,} casos ajuizados")
    return log_f, df_f


# ── Análise 2: Descoberta ─────────────────────────────────────────────────────

def descoberta(log_c, top_class: str, dfg_min_pct: float = 2.0):
    """
    Descobre DFGs, Petri Net e gargalos.

    dfg_min_pct: mantém apenas arestas com frequência >= X% do arco mais frequente.
    Valor padrão 2% reduz DFGs de centenas de MB para <1 MB sem perder o fluxo principal.
    """
    print("\n[2/8] Descoberta de Processo...")

    # DFG frequência
    try:
        dfg, sa, ea = pm4py.discover_dfg(log_c)
        dfg_vis = dfg
        sa_vis, ea_vis = sa, ea
        if dfg and dfg_min_pct > 0:
            max_freq  = max(dfg.values())
            threshold = max_freq * dfg_min_pct / 100
            filtered  = {k: v for k, v in dfg.items() if v >= threshold}
            if filtered:
                n_rem   = len(dfg) - len(filtered)
                dfg_vis = filtered
                # Filtrar sa/ea para remover nós sem arestas no grafo filtrado
                nodes   = {a for a, _ in dfg_vis} | {b for _, b in dfg_vis}
                sa_vis  = {k: v for k, v in sa.items() if k in nodes}
                ea_vis  = {k: v for k, v in ea.items() if k in nodes}
                if n_rem:
                    print(f"      DFG freq: {len(dfg)} arcos → {len(dfg_vis)} "
                          f"(removidos {n_rem} arcos < {dfg_min_pct}% do máximo={max_freq})")
            else:
                print(f"      [AVISO] Threshold {dfg_min_pct}% removeu todos os arcos — usando DFG completo.")
        pm4py.save_vis_dfg(dfg_vis, sa_vis, ea_vis, os.path.join(IMGS_DIR, "dfg_frequencia.png"))
        print("    salvo → imgs/dfg_frequencia.png")
        gerados.append(os.path.join(IMGS_DIR, "dfg_frequencia.png"))
    except Exception as e:
        print(f"    DFG indisponível (instale graphviz: brew install graphviz): {e}")

    # DFG performance — filtra pelas mesmas arestas do DFG de frequência
    try:
        # PM4Py 2.7+ requer case:concept:name como dtype string.
        # Após filtros (filtrar_ano, filtrar_classe), o dtype pode ser int64 se
        # os IDs foram lidos como numéricos. Cast preventivo.
        log_perf = log_c
        if isinstance(log_c, pd.DataFrame) and "case:concept:name" in log_c.columns:
            if log_c["case:concept:name"].dtype != object and str(log_c["case:concept:name"].dtype) != "string":
                log_perf = log_c.copy()
                log_perf["case:concept:name"] = log_perf["case:concept:name"].astype(str)
        dfg_p, sa_p, ea_p = pm4py.discover_performance_dfg(log_perf)
        dfg_p_vis = dfg_p
        if dfg_p and dfg_min_pct > 0 and dfg_vis:
            allowed    = set(dfg_vis.keys())
            filtered_p = {k: v for k, v in dfg_p.items() if k in allowed}
            if filtered_p:
                dfg_p_vis = filtered_p
                # Filtrar sa_p/ea_p pelos nós presentes no grafo filtrado.
                # Sem isso, save_vis_performance_dfg lança KeyError para
                # atividades removidas pelo threshold (ex: 'Desmembramento de Feitos').
                nodes_p = {a for a, _ in dfg_p_vis} | {b for _, b in dfg_p_vis}
                sa_p    = {k: v for k, v in sa_p.items() if k in nodes_p}
                ea_p    = {k: v for k, v in ea_p.items() if k in nodes_p}
        pm4py.save_vis_performance_dfg(dfg_p_vis, sa_p, ea_p,
                                       os.path.join(IMGS_DIR, "dfg_performance.png"))
        print("    salvo → imgs/dfg_performance.png")
        gerados.append(os.path.join(IMGS_DIR, "dfg_performance.png"))

        # Top 10 transições mais lentas (texto, não precisa graphviz)
        lento = sorted([(k, v["mean"] / 86400) for k, v in dfg_p.items()],
                       key=lambda x: -x[1])[:10]
        print("    Top 10 gargalos (transições mais lentas):")
        for (a, b), d in lento:
            print(f"      {d:6.1f}d  {a[:30]} → {b[:30]}")
    except Exception as e:
        print(f"    DFG performance indisponível: {e}")

    # Petri Net — Inductive Miner (log completo, noise=0.2)
    net = im = fm = None
    try:
        net, im, fm = pm4py.discover_petri_net_inductive(log_c, noise_threshold=0.2)
        pm4py.save_vis_petri_net(net, im, fm, os.path.join(IMGS_DIR, "petri_net.png"))
        print("    salvo → imgs/petri_net.png")
        gerados.append(os.path.join(IMGS_DIR, "petri_net.png"))
    except Exception as e:
        print(f"    Petri Net indisponível: {e}")

    # Petri Net — Cluster dominante (maior cluster K-Means por tamanho de arquivo, noise=0.4)
    # Detecta dinamicamente o cluster com mais casos (não hardcoded como cluster 3)
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        all_cluster_files = glob.glob(
            os.path.join(root, "output", "*_cluster_kmeans_[0-9]*.xes")
        )
        if all_cluster_files:
            # Proxy: maior arquivo XES = mais casos (mesma estrutura de evento)
            dominant_xes = max(all_cluster_files, key=os.path.getsize)
            cluster_id   = os.path.basename(dominant_xes).split("kmeans_")[1].split(".")[0]
            print(f"    Petri Net cluster dominante (id={cluster_id}): {os.path.basename(dominant_xes)}")
            log_kd = pm4py.read_xes(dominant_xes)
            n_kd   = len(log_kd)
            print(f"      {n_kd:,} casos no cluster dominante")
            net_kd, im_kd, fm_kd = pm4py.discover_petri_net_inductive(
                log_kd, noise_threshold=0.4
            )
            pm4py.save_vis_petri_net(
                net_kd, im_kd, fm_kd,
                os.path.join(IMGS_DIR, f"petri_net_cluster_dominante.png")
            )
            print(f"    salvo → imgs/petri_net_cluster_dominante.png")
            gerados.append(os.path.join(IMGS_DIR, "petri_net_cluster_dominante.png"))
        else:
            print("    Petri Net cluster dominante: nenhum *_cluster_kmeans_*.xes em output/")
    except Exception as e:
        print(f"    Petri Net cluster dominante indisponível: {e}")

    return net, im, fm


# ── Análise 2b: Top-K Variantes (cluster dominante) ──────────────────────────

def descoberta_top_variantes(top_k: int = 10, noise_threshold: float = 0.3):
    """
    Filtra cluster dominante às top_k variantes mais frequentes antes de minerar.
    Reduz drasticamente heterogeneidade → menos τ-transitions no modelo final.
    top_k: número de variantes a manter (padrão 10).
    noise_threshold: threshold do Inductive Miner após filtro (padrão 0.3).
    """
    print(f"\n[2c] Top-{top_k} variantes do cluster dominante (noise={noise_threshold})...")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    all_cluster_files = glob.glob(
        os.path.join(root, "output", "*_cluster_kmeans_[0-9]*.xes")
    )
    if not all_cluster_files:
        print("    Nenhum *_cluster_kmeans_*.xes em output/ — rode agrupar.py antes.")
        return

    cluster_xes = max(all_cluster_files, key=os.path.getsize)
    print(f"    Cluster XES: {os.path.basename(cluster_xes)}")
    log_k3 = pm4py.read_xes(cluster_xes)

    try:
        log_filtered = pm4py.filter_variants_top_k(log_k3, top_k)
        n_casos = len(log_filtered)
        print(f"    Casos após filtro top-{top_k}: {n_casos:,}")

        net, im, fm = pm4py.discover_petri_net_inductive(
            log_filtered, noise_threshold=noise_threshold
        )
        hidden = sum(1 for t in net.transitions if t.label is None)
        print(f"    Places: {len(net.places)} | Transitions: {len(net.transitions)} | Silent: {hidden}")

        nome = f"petri_net_cluster3_top{top_k}v"
        out = os.path.join(IMGS_DIR, f"{nome}.png")
        pm4py.save_vis_petri_net(net, im, fm, out)
        print(f"    salvo → imgs/{nome}.png")
        gerados.append(out)
    except Exception as e:
        print(f"    Top-variantes indisponível: {e}")


# ── Análise 3: Variantes ──────────────────────────────────────────────────────

def variantes(df_c: pd.DataFrame, top_class: str):
    print("\n[3/8] Variantes...")

    df_v     = df_c.sort_values(["case:concept:name", "time:timestamp"])
    variants = df_v.groupby("case:concept:name")["concept:name"].apply(" → ".join)
    counts   = variants.value_counts()
    total    = len(variants)
    cumul    = (counts.cumsum() / total * 100).values

    top_n = min(30, len(counts))
    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()
    ax1.bar(range(top_n), counts.values[:top_n], color="#4361ee", alpha=0.85)
    ax2.plot(range(top_n), cumul[:top_n], color="#e63946", lw=2, marker="o", ms=4)
    ax2.axhline(80, color="gray", ls="--", lw=1, alpha=0.6)
    ax2.text(top_n * 0.98, 82, "80%", ha="right", color="gray", fontsize=9)
    ax1.set_xlabel("Variante (rank)")
    ax1.set_ylabel("Processos", color="#4361ee")
    ax2.set_ylabel("% Acumulado", color="#e63946")
    ax2.set_ylim(0, 105)
    ax1.set_title(f"Pareto de Variantes — {top_class}\nTop {top_n} de {len(counts):,} variantes")
    salvar("variantes_pareto")

    n_80 = int((cumul < 80).sum()) + 1
    print(f"      Total de variantes: {len(counts):,}")
    print(f"      {n_80} variante(s) cobrem 80% dos processos")


# ── Análise 4: Temporal ───────────────────────────────────────────────────────

def temporal(df_c: pd.DataFrame, top_class: str):
    print("\n[4/8] Performance Temporal...")

    df_s   = df_c.sort_values(["case:concept:name", "time:timestamp"])
    bounds = df_s.groupby("case:concept:name")["time:timestamp"].agg(["min", "max"])
    bounds["dur"] = (bounds["max"] - bounds["min"]).dt.total_seconds() / 86400
    dur    = bounds["dur"].dropna()

    s = dur.describe(percentiles=[.5, .75, .9, .95])
    print(f"      Média: {s['mean']:.0f}d | Mediana: {s['50%']:.0f}d | "
          f"P90: {s['90%']:.0f}d | P95: {s['95%']:.0f}d | Máx: {s['max']:.0f}d")

    # Histograma throughput
    cap = dur.quantile(0.95)
    fig, ax = plt.subplots(figsize=(10, 4))
    dur.clip(upper=cap).hist(bins=40, ax=ax, color="#4361ee", edgecolor="white", lw=0.4)
    ax.axvline(s["mean"], color="red",    ls="--", lw=1.5, label=f'Média: {s["mean"]:.0f}d')
    ax.axvline(s["50%"],  color="orange", ls="--", lw=1.5, label=f'Mediana: {s["50%"]:.0f}d')
    ax.set_title("Tempo de Ciclo (truncado no P95)")
    ax.set_xlabel("Dias"); ax.set_ylabel("Processos"); ax.legend()
    salvar("throughput_time")

    # Sojourn time
    df_s = df_c.sort_values(["case:concept:name", "time:timestamp"]).copy()
    df_s["next_ts"] = df_s.groupby("case:concept:name")["time:timestamp"].shift(-1)
    df_s["wait_d"]  = (df_s["next_ts"] - df_s["time:timestamp"]).dt.total_seconds() / 86400

    sojourn = (
        df_s.dropna(subset=["wait_d"])
        .groupby("concept:name")["wait_d"]
        .agg(media="mean", mediana="median")
        .sort_values("media", ascending=False)
        .head(15)
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    y = range(len(sojourn))
    lbls = [a[:45] + "…" if len(a) > 45 else a for a in sojourn.index]
    ax.barh(y, sojourn["media"],   color="#4361ee", alpha=0.9,  label="Média")
    ax.barh(y, sojourn["mediana"], color="#f59e0b", alpha=0.75, label="Mediana")
    ax.set_yticks(y); ax.set_yticklabels(lbls, fontsize=9)
    ax.set_xlabel("Dias"); ax.set_title("Sojourn Time — Top 15 atividades mais lentas")
    ax.legend()
    salvar("sojourn_time")

    # Gargalos (A→B mais lentos)
    df_s["next_act"] = df_s.groupby("case:concept:name")["concept:name"].shift(-1)
    btk = (
        df_s.dropna(subset=["next_act", "wait_d"])
        .groupby(["concept:name", "next_act"])["wait_d"]
        .agg(media="mean", mediana="median")
        .reset_index()
        .sort_values("media", ascending=False)
        .head(10)
        .assign(label=lambda x: x["concept:name"].str[:28] + "  →  " + x["next_act"].str[:28])
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    y = range(len(btk))
    ax.barh(y, btk["media"],   color="#e63946", alpha=0.9,  label="Média")
    ax.barh(y, btk["mediana"], color="#f59e0b", alpha=0.75, label="Mediana")
    ax.set_yticks(y); ax.set_yticklabels(btk["label"], fontsize=9)
    ax.set_xlabel("Dias"); ax.set_title("Top 10 Gargalos — transições mais lentas")
    ax.legend()
    salvar("bottlenecks")

    return bounds


# ── Análise 5: Rework ─────────────────────────────────────────────────────────

def rework(df_c: pd.DataFrame):
    print("\n[5/8] Rework...")

    rw = (
        df_c.groupby(["case:concept:name", "concept:name"])
        .size().reset_index(name="n")
    )
    rw       = rw[rw["n"] > 1]
    affected = rw["case:concept:name"].nunique()
    total    = df_c["case:concept:name"].nunique()
    print(f"      Processos com rework: {affected:,} ({affected / total:.1%})")

    top_rw = (
        rw.groupby("concept:name")
        .agg(total_rep=("n", "sum"), casos=("case:concept:name", "nunique"))
        .sort_values("total_rep", ascending=False)
        .head(15)
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    lbls = [a[:45] + "…" if len(a) > 45 else a for a in top_rw.index]
    ax.barh(lbls, top_rw["total_rep"], color="#e63946")
    ax.set_xlabel("Total de repetições")
    ax.set_title("Top Atividades com Rework (repetições dentro do mesmo processo)")
    salvar("rework")


# ── Análise 6: Organizacional ─────────────────────────────────────────────────

def organizacional(df_c: pd.DataFrame, bounds: pd.DataFrame):
    print("\n[6/8] Perspectiva Organizacional...")

    if "org:resource" not in df_c.columns:
        print("      org:resource não encontrado.")
        return

    vol = df_c["org:resource"].value_counts().head(20)

    vara_princ = (
        df_c.groupby("case:concept:name")["org:resource"]
        .agg(lambda x: x.value_counts().index[0])
        .rename("vara")
    )
    perf = (
        bounds[["dur"]].join(vara_princ)
        .groupby("vara")["dur"]
        .agg(mediana="median", n="count")
        .query("n >= 5")
        .sort_values("mediana", ascending=False)
        .head(20)
    )

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    lbls_v = [str(v)[:45] + "…" if len(str(v)) > 45 else str(v) for v in vol.index]
    axes[0].barh(lbls_v, vol.values, color="#4361ee")
    axes[0].set_xlabel("N° de eventos")
    axes[0].set_title("Volume de Eventos por Vara (Top 20)")
    axes[0].tick_params(axis="y", labelsize=8)

    lbls_p = [str(v)[:45] + "…" if len(str(v)) > 45 else str(v) for v in perf.index]
    axes[1].barh(lbls_p, perf["mediana"], color="#f59e0b")
    axes[1].set_xlabel("Duração mediana (dias)")
    axes[1].set_title("Duração Mediana por Vara\n(≥ 5 processos, top 20 mais lentas)")
    axes[1].tick_params(axis="y", labelsize=8)

    plt.tight_layout()
    salvar("organizacional")

    print(f"      Varas com ≥5 processos: {len(perf):,}")
    if len(perf) >= 2:
        print(f"      Menor duração mediana: {perf['mediana'].min():.0f}d "
              f"| Maior: {perf['mediana'].max():.0f}d")


# ── Análise 7: Conformance ────────────────────────────────────────────────────

def conformance(log_c, net, im, fm):
    print("\n[7/8] Conformance (token replay)...")

    if net is None:
        print("      Pulado — Petri Net não disponível (graphviz necessário).")
        return

    # Amostragem: token replay é O(n × comprimento × tamanho_rede) — limitar a 500 traces
    MAX_CONF = 500
    from pm4py.objects.log.obj import EventLog
    if isinstance(log_c, pd.DataFrame):
        casos = log_c["case:concept:name"].unique()
        if len(casos) > MAX_CONF:
            import random; random.seed(42)
            casos_sample = set(random.sample(list(casos), MAX_CONF))
            log_conf = log_c[log_c["case:concept:name"].isin(casos_sample)].copy()
            print(f"      Amostra: {MAX_CONF}/{len(casos)} casos para token replay")
        else:
            log_conf = log_c
    else:
        if len(log_c) > MAX_CONF:
            import random; random.seed(42)
            idx = random.sample(range(len(log_c)), MAX_CONF)
            log_conf = EventLog([log_c[i] for i in idx])
            log_conf.attributes = dict(log_c.attributes)
            print(f"      Amostra: {MAX_CONF}/{len(log_c)} casos para token replay")
        else:
            log_conf = log_c

    fitness = pm4py.fitness_token_based_replay(log_conf, net, im, fm)
    print(f"      Fitness médio:    {fitness['average_trace_fitness']:.2%}")
    print(f"      Traces conformes: {fitness['percentage_of_fitting_traces']:.2%}")

    diags    = pm4py.conformance_diagnostics_token_based_replay(log_conf, net, im, fm)
    fit_vals = [d["trace_fitness"] for d in diags]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(fit_vals, bins=20, color="#4361ee", edgecolor="white", lw=0.4)
    ax.axvline(0.8, color="red", ls="--", lw=1.5, label="Limite 0.8")
    ax.set_xlabel("Fitness"); ax.set_ylabel("Processos")
    ax.set_title("Distribuição de Fitness — Token Replay"); ax.legend()
    salvar("conformance_fitness")

    baixo = sum(1 for v in fit_vals if v < 0.8)
    print(f"      Processos com fitness < 0.8: {baixo:,} ({baixo / len(fit_vals):.1%})")


# ── Análise 8: Comparação tribunais ──────────────────────────────────────────

def comparacao(xes_dir: str):
    print("\n[8/8] Comparação entre Tribunais...")

    files: dict[str, str] = {}
    for f in sorted(glob.glob(os.path.join(xes_dir, "*.xes"))):
        tribunal = os.path.basename(f).split("_")[0]
        files[tribunal] = f

    if len(files) < 2:
        print("      Apenas 1 tribunal disponível — comparação ignorada.")
        return

    rows = []
    for tribunal, path in files.items():
        df_t = fix_colunas(pm4py.convert_to_dataframe(pm4py.read_xes(path)))
        b    = (df_t.sort_values("time:timestamp")
                    .groupby("case:concept:name")["time:timestamp"]
                    .agg(["min", "max"]))
        dur  = (b["max"] - b["min"]).dt.total_seconds() / 86400
        vct  = (df_t.sort_values("time:timestamp")
                    .groupby("case:concept:name")["concept:name"]
                    .apply(tuple).value_counts())
        n    = df_t["case:concept:name"].nunique()
        rows.append({
            "Tribunal":        tribunal,
            "Processos":       n,
            "Atividades":      df_t["concept:name"].nunique(),
            "Variantes":       len(vct),
            "Evt/Processo":    round(len(df_t) / n, 1),
            "Mediana (dias)":  round(dur.median(), 1),
            "P90 (dias)":      round(dur.quantile(0.9), 1),
        })

    comp = pd.DataFrame(rows).set_index("Tribunal")
    print(comp.to_string())

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, col, color in zip(axes,
                               ["Mediana (dias)", "Evt/Processo", "Variantes"],
                               ["#4361ee", "#2dc653", "#f59e0b"]):
        comp[col].plot(kind="bar", ax=ax, color=color, edgecolor="white")
        ax.set_title(col); ax.set_xlabel(""); ax.tick_params(axis="x", rotation=0)
    plt.suptitle("Comparação entre Tribunais", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    salvar("comparacao_tribunais")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import re as _re

    def _slug(texto: str) -> str:
        s = texto.replace(" ", "_")
        for src, dst in [
            ("ç","c"),("ã","a"),("â","a"),("á","a"),("à","a"),("é","e"),
            ("ê","e"),("í","i"),("ó","o"),("ô","o"),("ú","u"),("õ","o"),
        ]:
            s = s.replace(src, dst).replace(src.upper(), dst.upper())
        return _re.sub(r"[^\w]", "_", s)[:40]

    parser = argparse.ArgumentParser(
        description="Análises PM4Py do event log Datajud. Salva PNGs em analises/imgs/."
    )
    parser.add_argument(
        "xes", nargs="?",
        help="Arquivo .xes (opcional — detecta automaticamente se omitido)"
    )
    parser.add_argument(
        "--classe", default="Ação Penal - Procedimento Ordinário",
        help="Classe processual a analisar (default: Ação Penal - Procedimento Ordinário)"
    )
    parser.add_argument(
        "--tribunal", default="TJPR",
        help="Tribunal (default: TJPR)"
    )
    parser.add_argument(
        "--ano", type=int, default=None, metavar="YYYY",
        help="Filtrar DFG/Petri Net por ano de ajuizamento (ex: 2025). "
             "Reduz tamanho do grafo para logs com muitos casos. "
             "Demais análises (throughput, rework, org) usam todos os casos."
    )
    parser.add_argument(
        "--dfg-min-pct", type=float, default=2.0, metavar="PCT",
        help="Manter apenas arestas do DFG com freq >= PCT%% do arco mais frequente "
             "(default: 2.0). Aumentar reduz o grafo; 0 = sem filtro."
    )
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "output")

    # Detecta XES: prefere arquivo filtrado pela classe, fallback para XES bruto
    if args.xes:
        xes_path = args.xes
    else:
        slug_classe = _slug(args.classe)
        # 1. XES filtrado por classe (gerado por exportar_filtrado.py), excluindo top10v e happy_path
        filtered = sorted([
            f for f in glob.glob(os.path.join(out_dir, f"{args.tribunal}_{slug_classe}_*.xes"))
            if "top10v" not in f and "happy_path" not in f and "cluster" not in f
        ])
        if filtered:
            xes_path = filtered[-1]
        else:
            # 2. XES bruto (todo tribunal)
            bruto = sorted([
                f for f in glob.glob(os.path.join(out_dir, f"{args.tribunal}_[0-9]*.xes"))
            ])
            if not bruto:
                print("Nenhum arquivo .xes encontrado em output/. Execute main.py primeiro.")
                sys.exit(1)
            xes_path = bruto[-1]

    xes_dir = os.path.dirname(os.path.abspath(xes_path))

    # Pipeline de análises
    log, df           = carregar(xes_path)
    log_c, df_c, cls  = filtrar_classe(log, df, args.classe)

    # Filtro de ano para DFG/Petri Net (opcional)
    log_dfg, df_dfg = log_c, df_c
    if args.ano:
        log_dfg, df_dfg = filtrar_ano(log_c, df_c, args.ano)
        print(f"      [Discovery usa {df_dfg['case:concept:name'].nunique():,} casos de {args.ano}]")
        print(f"      [Demais análises usam todos {df_c['case:concept:name'].nunique():,} casos]")

    net, im, fm       = descoberta(log_dfg, cls, dfg_min_pct=args.dfg_min_pct)
    descoberta_top_variantes(top_k=20, noise_threshold=0.3)
    variantes(df_c, cls)
    bounds            = temporal(df_c, cls)
    rework(df_c)
    organizacional(df_c, bounds)
    # Conformance usa o mesmo subconjunto que gerou a Petri Net (log_dfg).
    # Se ano não foi filtrado, log_dfg == log_c (sem diferença).
    # Usar log_c (dataset completo) contra Petri Net de subset produziria
    # fitness artificialmente alto/baixo por mismatch de populações.
    conformance(log_dfg, net, im, fm)
    comparacao(xes_dir)

    # Resumo final
    print(f"\n{'='*55}")
    print(f"  {len(gerados)} arquivo(s) gerado(s) em:")
    print(f"  {IMGS_DIR}")
    print("=" * 55)
    for p in sorted(gerados):
        print(f"  {os.path.basename(p)}")
    print("=" * 55)

    # Abre a pasta (macOS)
    os.system(f'open "{IMGS_DIR}"')


if __name__ == "__main__":
    main()
