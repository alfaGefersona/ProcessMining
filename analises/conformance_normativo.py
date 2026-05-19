"""
Conformance Checking — Modelo Normativo CPP arts. 394–405

Complementa o conformance contra o modelo DESCOBERTO (analisar.py).
Este script:
  1. Mapeia atividades concretas do log a 8 marcos normativos CPP
  2. Projeta o log em variantes abstratas (somente marcos CPP)
  3. Constrói Petri Net normativa manualmente
  4. Calcula as 4 métricas de van der Aalst (2016) contra o modelo normativo
  5. Gera figura com cobertura dos marcos + tabela comparativa

Uso:
    python analises/conformance_normativo.py
    python analises/conformance_normativo.py --classe "Ação Penal - Procedimento Ordinário"
    python analises/conformance_normativo.py --tribunal TJPR --sample 1000
"""

import argparse
import glob
import os
import random
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "output")
IMG_DIR = os.path.join(ROOT, "analises", "imgs")
os.makedirs(IMG_DIR, exist_ok=True)


# ── Mapeamento de marcos CPP ───────────────────────────────────────────────────
# Cada entrada: rótulo abstrato → função que testa substring da atividade concreta.
# Os rótulos abstratos são os labels das transições na Petri Net normativa.
#
# Nomes reais no log TJPR/Datajud (TPU CNJ):
#   - Início:        "Denúncia" (ato do MP) ou "Distribuição - competência exclusiva"
#   - Recebimento:   "Recebimento" (exato)
#   - Citação:       NÃO registrada como evento PJe na maioria dos casos TJPR
#                    (0% cobertura — ato cartorial fora do sistema)
#   - Resposta:      "Petição - Resposta À acusação" (À maiúsculo no TPU)
#   - AIJ:           "de Instrução e Julgamento - designada/realizada/Juiz(a)"
#                    (prefixo "Audiência " ausente no TPU TJPR — truncado)
#   - Sentença:      "Procedência", "Improcedência", "Procedência em Parte"
#   - Trânsito:      "Trânsito em julgado" (exato, minúsculas)

CPP_MARCOS = {
    "Distribuição / Petição": lambda a: (
        "Distribuição" in a
        or "Petição inicial" in a
        or a.strip() == "Denúncia"
    ),
    "Recebimento": lambda a: a.strip() == "Recebimento",
    "Citação": lambda a: (
        "citado" in a.lower()          # "Réu revel citado por edital"
        or "Citação" in a              # caso apareça em outro formato
    ),
    "Resposta à Acusação": lambda a: (
        "Resposta" in a and "acusa" in a.lower()
    ),
    "Absolvição Sumária": lambda a: (
        "Absolvição" in a and "umária" in a
    ),
    "Audiência de Instrução": lambda a: (
        "Instrução e Julgamento" in a   # "de Instrução e Julgamento - realizada" etc.
        or ("Instrução" in a and "designada" in a)
    ),
    "Sentença": lambda a: any(k in a for k in [
        "Procedência",      # "Procedência", "Procedência em Parte"
        "Improcedência",    # "Improcedência", "improcedência" (minúscula no TPU)
        "improcedência",
    ]) and "Decisão" not in a and "Reforma" not in a,
    "Trânsito em Julgado": lambda a: a.strip() == "Trânsito em julgado",
}

# Ordem normativa CPP — usada para verificar sequência nos traces
ORDEM_NORMATIVA = [
    "Distribuição / Petição",
    "Recebimento",
    "Citação",
    "Resposta à Acusação",
    "Absolvição Sumária",
    "Audiência de Instrução",
    "Sentença",
    "Trânsito em Julgado",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def slug(texto: str) -> str:
    import re
    s = texto.replace(" ", "_")
    for src, dst in [
        ("ç","c"),("ã","a"),("â","a"),("á","a"),("à","a"),("é","e"),
        ("ê","e"),("í","i"),("ó","o"),("ô","o"),("ú","u"),("õ","o"),
    ]:
        s = s.replace(src, dst).replace(src.upper(), dst.upper())
    return re.sub(r"[^\w]", "_", s)[:40]


def fix_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c[5:] if c.startswith("case:case:") else c for c in df.columns]
    return df


def carregar(tribunal: str, classe: str) -> pd.DataFrame | None:
    candidates = sorted([
        f for f in glob.glob(os.path.join(OUT_DIR, f"{tribunal}_{slug(classe)}_*.csv"))
        if "happy_path" not in f and "cluster" not in f and "top" not in f
        and "features" not in f and "kmeans" not in f and "sla" not in f
    ])
    if not candidates:
        print(f"  [ERRO] Nenhum CSV encontrado. Execute exportar_filtrado.py primeiro.")
        return None
    path = candidates[-1]
    print(f"  Carregando: {os.path.basename(path)}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True, errors="coerce")
    return fix_colunas(df)


# ── Projeção do log ────────────────────────────────────────────────────────────

def mapear_marco(activity: str) -> str | None:
    """Retorna o rótulo do marco CPP ou None se não mapear."""
    for marco, fn in CPP_MARCOS.items():
        if fn(activity):
            return marco
    return None


def projetar_log(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Projeta o log concreto em variantes abstratas CPP:
      - Mantém apenas eventos que mapeiam a um marco CPP
      - Substitui concept:name pelo rótulo abstrato
      - Remove duplicatas consecutivas do mesmo marco no mesmo caso
    Retorna (df_projetado, dict_cobertura).
    """
    df = df.sort_values(["case:concept:name", "time:timestamp"])
    df = df.copy()
    df["marco_cpp"] = df["concept:name"].apply(mapear_marco)

    total_cases = df["case:concept:name"].nunique()
    cobertura = {}
    for marco in CPP_MARCOS:
        n = df[df["marco_cpp"] == marco]["case:concept:name"].nunique()
        cobertura[marco] = {"n": n, "pct": n / total_cases * 100}

    df_proj = df.dropna(subset=["marco_cpp"]).copy()
    df_proj["concept:name"] = df_proj["marco_cpp"]

    # Remove consecutivos iguais (dedup por caso)
    df_proj["_prev"] = df_proj.groupby("case:concept:name")["concept:name"].shift(1)
    df_proj = df_proj[df_proj["concept:name"] != df_proj["_prev"]].copy()
    df_proj = df_proj.drop(columns=["marco_cpp", "_prev"])

    casos_proj = df_proj["case:concept:name"].nunique()
    print(f"  Casos com ≥1 marco CPP: {casos_proj:,} / {total_cases:,} "
          f"({casos_proj / total_cases:.1%})")
    return df_proj, cobertura


# ── Modelo normativo CPP (Petri Net manual) ────────────────────────────────────

def construir_petri_net_normativa():
    """
    Constrói a Petri Net ESTRITAMENTE normativa CPP arts. 394–405 (1º grau).

    Princípio: modelar APENAS o que a lei prescreve, sem NENHUMA concessão ao
    subregistro do PJe. Cada etapa é uma transição visível; a ausência dela
    no TBR produz token faltando → fitness baixo → achado real.

    Etapas OBRIGATÓRIAS (sem tau — zero exceções):
      Distribuição / Petição     art. 41 / 394
      Recebimento                art. 395-396
      Citação                    art. 396  ← obrigatória; ausência = desvio
      Resposta à Acusação        art. 396-A ← obrigatória; ausência = desvio
      Sentença                   art. 403  ← obrigatória
      Trânsito em Julgado        art. 502 CPC supletivo ← obrigatório; todo
                                  processo penal deve atingir res judicata

    Escolha NORMATIVA legítima (XOR sem tau — lei dá alternativas ao juiz):
      Absolvição Sumária (art. 397)
        OU Audiência de Instrução e Julgamento (art. 400)

    ZERO tau:
      Tau para Trânsito seria concessão à janela de observação (dado),
      não ao direito. O CPP não prevê processo sem Trânsito — todo processo
      penal DEVE atingir res judicata. Ausência no log = gap de dados = achado.

    Consequência esperada: fitness < 50%, pois:
      - Citação = 1.1% (gap crítico — mandado físico fora do PJe)
      - Trânsito = 83.8% (16.2% sem encerramento formal registrado)
    Ambos os gaps SÃO o achado — o PJe não registra etapas obrigatórias do CPP.
    """
    from pm4py.objects.petri_net.obj import PetriNet, Marking
    from pm4py.objects.petri_net.utils import petri_utils as utils

    net = PetriNet("CPP_Estrito_394_405")

    def place(name):
        p = PetriNet.Place(name)
        net.places.add(p)
        return p

    def trans(name, label=None):
        t = PetriNet.Transition(name, label)
        net.transitions.add(t)
        return t

    def arc(src, dst):
        utils.add_arc_from_to(src, dst, net)

    # Lugares
    p_start   = place("start")
    p1        = place("after_dist")
    p2        = place("after_recv")
    p3        = place("after_citacao")     # após Citação (obrigatória)
    p4        = place("after_resposta")    # após Resposta (obrigatória)
    p_instr_j = place("after_instrucao")  # join XOR Absolvição/AIJ
    p5        = place("after_sent")
    p_end     = place("end")

    # Transições TODAS OBRIGATÓRIAS (sem tau)
    t_dist  = trans("t_dist",  "Distribuição / Petição")   # art. 394
    t_recv  = trans("t_recv",  "Recebimento")               # art. 395-396
    t_cit   = trans("t_cit",   "Citação")                  # art. 396 — OBRIGATÓRIO
    t_resp  = trans("t_resp",  "Resposta à Acusação")       # art. 396-A — OBRIGATÓRIO
    t_absol = trans("t_absol", "Absolvição Sumária")        # art. 397 — XOR normativo
    t_aij   = trans("t_aij",   "Audiência de Instrução")   # art. 400 — XOR normativo
    t_sent  = trans("t_sent",  "Sentença")                  # art. 403 — OBRIGATÓRIO
    t_trans = trans("t_trans", "Trânsito em Julgado")       # art. 502 CPC supletivo — OBRIGATÓRIO

    # ── Sequência obrigatória linear ──────────────────────────────────────────
    arc(p_start, t_dist);  arc(t_dist, p1)
    arc(p1,      t_recv);  arc(t_recv, p2)
    arc(p2,      t_cit);   arc(t_cit,  p3)   # CPP art. 396 — sem alternativa
    arc(p3,      t_resp);  arc(t_resp, p4)   # CPP art. 396-A — sem alternativa

    # ── XOR normativo (art. 397): Absolvição Sumária OU AIJ ──────────────────
    # Ambas as saídas são PRESCRITAS pela lei — não é tau, é escolha do juiz.
    arc(p4, t_absol); arc(t_absol, p_instr_j)
    arc(p4, t_aij);   arc(t_aij,   p_instr_j)

    # ── Sentença (obrigatória após instrução) ─────────────────────────────────
    arc(p_instr_j, t_sent); arc(t_sent, p5)

    # ── Trânsito em Julgado (OBRIGATÓRIO — sem tau) ───────────────────────────
    # CPP não prevê processo sem res judicata. Ausência no log = gap de dados.
    arc(p5, t_trans); arc(t_trans, p_end)

    im = Marking(); im[p_start] = 1
    fm = Marking(); fm[p_end]   = 1

    n_vis = sum(1 for t in net.transitions if t.label is not None)
    n_sil = sum(1 for t in net.transitions if t.label is None)
    print(f"  Petri Net ESTRITA CPP (ZERO tau): {len(net.places)} places | "
          f"{n_vis} trans. obrigatórias | {n_sil} tau")
    print(f"  Sequência: Dist → Recebimento → Citação → Resposta"
          f" → [AbsolvSumária|AIJ] → Sentença → Trânsito")

    return net, im, fm


# ── Cálculo das 4 métricas ─────────────────────────────────────────────────────

def calcular_metricas(df_proj: pd.DataFrame, net, im, fm,
                      sample_size: int = 500, seed: int = 42) -> dict:
    """Calcula as 4 métricas de conformance de van der Aalst (2016)."""
    import pm4py
    from pm4py.objects.log.obj import EventLog

    # Converter para EventLog
    df_proj = df_proj.copy()
    df_proj["case:concept:name"] = df_proj["case:concept:name"].astype(str)

    casos = df_proj["case:concept:name"].unique()
    total = len(casos)

    if total == 0:
        print("  [ERRO] Nenhum caso na projeção — nenhuma métrica calculada.")
        return {}

    log_obj = pm4py.convert_to_event_log(df_proj)

    if total > sample_size:
        random.seed(seed)
        idx = random.sample(range(len(log_obj)), sample_size)
        log_sample = EventLog([log_obj[i] for i in idx])
        print(f"  Amostra: {sample_size}/{total} casos")
    else:
        log_sample = log_obj
        print(f"  Casos na projeção: {total}")

    metrics = {}
    fmt = lambda v: f"{v:.2%}" if v == v else "N/D"

    # 1. Fitness (TBR)
    try:
        fit = pm4py.fitness_token_based_replay(log_sample, net, im, fm)
        metrics["fitness"]  = fit.get("average_trace_fitness", float("nan"))
        metrics["pct_fit"]  = fit.get("percentage_of_fitting_traces", float("nan"))
        print(f"  Fitness (TBR):       {fmt(metrics['fitness'])}")
        print(f"  Traces conformes:    {fmt(metrics['pct_fit'])}")
    except Exception as e:
        print(f"  Fitness falhou: {e}")
        metrics["fitness"] = float("nan")

    # 2. Precision (TBR / ETC)
    try:
        prec = pm4py.precision_token_based_replay(log_sample, net, im, fm)
        metrics["precision"] = prec
        print(f"  Precision (TBR-ETC): {fmt(prec)}")
    except Exception as e:
        print(f"  Precision (TBR) falhou: {e}")
        try:
            prec = pm4py.precision_alignments(log_sample, net, im, fm)
            metrics["precision"] = prec
            print(f"  Precision (Align):   {fmt(prec)}")
        except Exception as e2:
            print(f"  Precision (Align) falhou: {e2}")
            metrics["precision"] = float("nan")

    # 3. Generalization (TBR)
    try:
        gen = pm4py.generalization_tbr(log_sample, net, im, fm)
        metrics["generalization"] = gen
        print(f"  Generalization:      {fmt(gen)}")
    except Exception as e:
        print(f"  Generalization falhou: {e}")
        metrics["generalization"] = float("nan")

    # 4. Simplicity (Arc Degree) — manual se pm4py não tiver o método
    try:
        simp = pm4py.simplicity_arc_degree(net)
        metrics["simplicity"] = simp
        print(f"  Simplicity:          {fmt(simp)}")
    except AttributeError:
        # Cálculo manual: inverso da densidade de arcos
        # simplicity = (|P| + |T|) / (|P| + |T| + |arcos|)
        n_p = len(net.places)
        n_t = len(net.transitions)
        n_a = len(net.arcs)
        simp = (n_p + n_t) / (n_p + n_t + n_a) if (n_p + n_t + n_a) > 0 else 1.0
        metrics["simplicity"] = simp
        print(f"  Simplicity (manual): {fmt(simp)}  ({n_p}P / {n_t}T / {n_a} arcos)")
    except Exception as e:
        print(f"  Simplicity falhou: {e}")
        metrics["simplicity"] = float("nan")

    return metrics


# ── Figura ─────────────────────────────────────────────────────────────────────

def gerar_figura(cobertura: dict, metricas_norm: dict,
                 metricas_desc: dict | None = None) -> str:
    """Gera PNG com cobertura dos marcos CPP + tabela de métricas comparativa."""

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(
        "Conformance Checking — Modelo Normativo CPP arts. 394–405\n"
        "TJPR · Ação Penal - Procedimento Ordinário",
        fontsize=13, fontweight="bold"
    )

    # Subplot 1: Cobertura dos marcos CPP (barra horizontal)
    ax1 = fig.add_subplot(2, 1, 1)
    marcos = list(cobertura.keys())
    pcts   = [cobertura[m]["pct"] for m in marcos]
    colors = [
        "#e63946" if p < 30 else
        "#f4a261" if p < 70 else
        "#2a9d8f"
        for p in pcts
    ]
    bars = ax1.barh(range(len(marcos)), pcts, color=colors)
    ax1.set_yticks(range(len(marcos)))
    ax1.set_yticklabels(marcos, fontsize=10)
    ax1.set_xlabel("% dos casos com o marco CPP registrado no PJe")
    ax1.set_title("Cobertura dos Marcos CPP arts. 394–405 no Log TJPR",
                  fontsize=11, fontweight="bold")
    ax1.set_xlim(0, 112)
    ax1.axvline(100, color="gray", ls="--", lw=1, alpha=0.4)

    for bar, pct, m in zip(bars, pcts, marcos):
        n = cobertura[m]["n"]
        ax1.text(min(pct + 1.5, 108), bar.get_y() + bar.get_height() / 2,
                 f"{pct:.1f}%  (n={n:,})", va="center", fontsize=9)

    ax1.grid(axis="x", alpha=0.3)
    ax1.legend(handles=[
        Patch(color="#2a9d8f", label="≥70% — marco bem registrado"),
        Patch(color="#f4a261", label="30–70% — registro parcial"),
        Patch(color="#e63946", label="<30% — subregistrado no PJe"),
    ], loc="lower right", fontsize=8)

    # Subplot 2a: Tabela de métricas comparativa
    ax2 = fig.add_subplot(2, 2, 3)
    ax2.axis("off")

    nan = float("nan")
    fmt = lambda v: f"{v:.1%}" if v == v else "N/D"

    rows_data = [
        ["Fitness (TBR)",        fmt(metricas_norm.get("fitness", nan)),
                                 fmt(metricas_desc.get("fitness", nan)) if metricas_desc else "—"],
        ["Precision (ETC-TBR)",  fmt(metricas_norm.get("precision", nan)),
                                 fmt(metricas_desc.get("precision", nan)) if metricas_desc else "—"],
        ["Generalization (TBR)", fmt(metricas_norm.get("generalization", nan)),
                                 fmt(metricas_desc.get("generalization", nan)) if metricas_desc else "—"],
        ["Simplicity (Arc Deg)", fmt(metricas_norm.get("simplicity", nan)),
                                 fmt(metricas_desc.get("simplicity", nan)) if metricas_desc else "—"],
    ]

    tbl = ax2.table(
        cellText=rows_data,
        colLabels=["Métrica", "Normativo CPP", "Descoberto (IM)"],
        loc="center", cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 2.2)
    ax2.set_title("Métricas van der Aalst (2016)\nNormativo × Descoberto",
                  fontsize=11, fontweight="bold", pad=20)

    # Subplot 2b: Interpretação
    ax3 = fig.add_subplot(2, 2, 4)
    ax3.axis("off")

    fit_n = metricas_norm.get("fitness", nan)
    interp = (
        "INTERPRETAÇÃO\n\n"
        f"Fitness normativo {fmt(fit_n)} = % de traces\n"
        f"que se encaixam no rito CPP arts. 394-405.\n\n"
        "Fitness normativo < descoberto → casos\n"
        "percorrem caminhos não previstos no CPP\n"
        "(atividades cartoriais, redistributivas).\n\n"
        "Precision normativa alta → modelo CPP\n"
        "é restritivo: aceita apenas sequências\n"
        "próximas ao rito formal.\n\n"
        "Marcos com cobertura <30% = etapas\n"
        "não registradas no PJe (gap de dados).\n"
        "Citação e Resposta à Acusação ausentes\n"
        "não significa que não ocorreram."
    )
    ax3.text(0.05, 0.95, interp, va="top", ha="left", fontsize=9,
             transform=ax3.transAxes,
             bbox=dict(boxstyle="round", facecolor="#fffbe6", alpha=0.9))
    ax3.set_title("Guia de Interpretação", fontsize=11, fontweight="bold")

    plt.tight_layout()
    out = os.path.join(IMG_DIR, "conformance_normativo.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  → salvo: {out}")
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Conformance Checking — Modelo Normativo CPP arts. 394-405."
    )
    parser.add_argument("--classe",   default="Ação Penal - Procedimento Ordinário")
    parser.add_argument("--tribunal", default="TJPR")
    parser.add_argument("--sample",   type=int, default=500,
                        help="Tamanho da amostra para TBR (default: 500)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Conformance — Modelo Normativo CPP arts. 394–405")
    print(f"  Tribunal: {args.tribunal}  |  Classe: {args.classe}")
    print(f"{'='*60}")

    df = carregar(args.tribunal, args.classe)
    if df is None:
        return

    total = df["case:concept:name"].nunique()
    print(f"  {total:,} casos carregados, {len(df):,} eventos")

    # Cobertura dos marcos CPP
    print(f"\n[1/3] Cobertura dos marcos CPP no log...")
    df_proj, cobertura = projetar_log(df)
    for marco, info in cobertura.items():
        print(f"  {marco:<35} {info['n']:5d} casos ({info['pct']:5.1f}%)")

    # Construir Petri Net normativa
    print(f"\n[2/3] Construindo Petri Net normativa CPP...")
    net, im, fm = construir_petri_net_normativa()

    # Calcular métricas
    print(f"\n[3/3] Calculando métricas (4 de van der Aalst 2016)...")
    metricas_norm = calcular_metricas(df_proj, net, im, fm,
                                      sample_size=args.sample)

    # Gerar figura (sem métricas descoberto — script standalone)
    gerar_figura(cobertura, metricas_norm, metricas_desc=None)

    # Salvar Petri Net normativa como PNG
    try:
        import pm4py
        out_pn = os.path.join(IMG_DIR, "petri_net_normativa_cpp.png")
        pm4py.save_vis_petri_net(net, im, fm, out_pn)
        print(f"  → salvo: petri_net_normativa_cpp.png")
    except Exception as e:
        print(f"  Petri Net PNG indisponível: {e}")

    # Resumo final
    fmt = lambda v: f"{v:.2%}" if v == v else "N/D"
    nan = float("nan")
    print(f"\n{'='*60}")
    print(f"  RESUMO — Modelo Normativo CPP arts. 394-405")
    print(f"{'='*60}")
    print(f"  Fitness (TBR):       {fmt(metricas_norm.get('fitness', nan))}")
    print(f"  Precision (ETC-TBR): {fmt(metricas_norm.get('precision', nan))}")
    print(f"  Generalization:      {fmt(metricas_norm.get('generalization', nan))}")
    print(f"  Simplicity:          {fmt(metricas_norm.get('simplicity', nan))}")
    print(f"\n  Cobertura dos marcos:")
    for marco, info in cobertura.items():
        barra = "█" * int(info["pct"] / 5) + "░" * (20 - int(info["pct"] / 5))
        print(f"  {barra} {marco:<35} {info['pct']:5.1f}%")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
