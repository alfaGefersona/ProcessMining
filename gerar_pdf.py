#!/usr/bin/env python3
"""
Gera PDF do Relatório PM² — Ação Penal - Procedimento Ordinário (TJPR).

Converte RELATORIO_PM2.md → HTML → PDF (WeasyPrint).
Imagens injetadas inline próximas às seções relevantes.

Uso:
    python gerar_pdf.py
    python gerar_pdf.py --output output/RELATORIO_PM2.pdf
"""

import argparse
import base64
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

try:
    import markdown
    from weasyprint import HTML, CSS
except ImportError:
    sys.exit("[ERRO] Instale dependências: pip install weasyprint markdown")

try:
    from PIL import Image as _PILImage
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

# ==============================================================================
# CSS — Estilo profissional para PDF
# ==============================================================================
CSS_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap');

@page {
    size: A4;
    margin: 2cm 2.2cm 2.5cm 2.2cm;
    @top-right {
        content: "PM² · Ação Penal · TJPR";
        font-size: 8pt;
        color: #888;
    }
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 8pt;
        color: #888;
    }
}

@page :first {
    @top-right { content: ""; }
    @bottom-center { content: ""; }
}

* { box-sizing: border-box; }

body {
    font-family: "Source Sans Pro", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.55;
    color: #1a1a2e;
    background: white;
}

/* ── CAPA ── */
.capa {
    page: capa;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 25cm;
    text-align: center;
    padding: 3cm 1cm;
    border-bottom: 4px solid #16213e;
    margin-bottom: 2cm;
    page-break-after: always;
}
@page capa {
    margin: 0;
    @top-right { content: ""; }
    @bottom-center { content: ""; }
}
.capa-badge {
    display: inline-block;
    background: #16213e;
    color: white;
    font-size: 9pt;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 6px 18px;
    border-radius: 3px;
    margin-bottom: 2cm;
}
.capa h1 {
    font-size: 28pt;
    font-weight: 700;
    color: #16213e;
    line-height: 1.15;
    margin: 0 0 0.3cm 0;
    border: none;
}
.capa h2 {
    font-size: 16pt;
    font-weight: 300;
    color: #444;
    margin: 0 0 1.5cm 0;
    border: none;
    padding: 0;
}
.capa-meta {
    font-size: 10pt;
    color: #555;
    line-height: 2;
    margin-top: 1.5cm;
}
.capa-meta strong { color: #16213e; }
.capa-footer {
    margin-top: 2cm;
    font-size: 8pt;
    color: #999;
    border-top: 1px solid #ddd;
    padding-top: 0.5cm;
}

/* ── HEADINGS ── */
h1 {
    font-size: 20pt;
    font-weight: 700;
    color: #16213e;
    border-bottom: 3px solid #0f3460;
    padding-bottom: 0.2cm;
    margin: 0.8cm 0 0.4cm 0;
    page-break-after: avoid;
}
h2 {
    font-size: 14pt;
    font-weight: 600;
    color: #0f3460;
    border-left: 4px solid #e94560;
    padding-left: 0.35cm;
    margin: 0.7cm 0 0.3cm 0;
    page-break-after: avoid;
}
h3 {
    font-size: 11pt;
    font-weight: 600;
    color: #16213e;
    margin: 0.5cm 0 0.2cm 0;
    page-break-after: avoid;
}
h4 {
    font-size: 10.5pt;
    font-weight: 600;
    color: #333;
    margin: 0.4cm 0 0.15cm 0;
    page-break-after: avoid;
}

/* ── TABLES ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.4cm 0;
    font-size: 9pt;
    page-break-inside: avoid;
}
thead tr {
    background: #16213e;
    color: white;
}
th {
    padding: 6px 10px;
    text-align: left;
    font-weight: 600;
}
td {
    padding: 5px 10px;
    border-bottom: 1px solid #e0e0e0;
    vertical-align: top;
}
tr:nth-child(even) td { background: #f7f9fc; }

/* ── CODE ── */
pre {
    background: #f4f4f8;
    border-left: 3px solid #0f3460;
    border-radius: 4px;
    padding: 0.4cm;
    font-size: 8pt;
    font-family: "Courier New", monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow: hidden;
    page-break-inside: avoid;
    margin: 0.3cm 0;
}
code {
    background: #f0f0f5;
    font-family: "Courier New", monospace;
    font-size: 8.5pt;
    padding: 1px 4px;
    border-radius: 3px;
}
pre code { background: transparent; padding: 0; }

/* ── BLOCKQUOTE ── */
blockquote {
    border-left: 4px solid #e94560;
    background: #fff8f8;
    margin: 0.3cm 0;
    padding: 0.3cm 0.5cm;
    font-style: italic;
    font-size: 9.5pt;
    color: #444;
    page-break-inside: avoid;
}
blockquote p { margin: 0; }

/* ── PARAGRAPHS / LISTS ── */
p { margin: 0.2cm 0; }
ul, ol { margin: 0.2cm 0 0.2cm 0.8cm; padding: 0; }
li { margin: 0.1cm 0; }

/* ── HR ── */
hr { border: none; border-top: 1px solid #ddd; margin: 0.6cm 0; }

/* ── HIGHLIGHTS ── */
strong { color: #16213e; }
em { color: #555; }

/* ── IMAGENS INLINE ── */
.img-inline {
    margin: 0.6cm 0 0.8cm 0;
    page-break-inside: avoid;
}
.img-inline-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4cm;
    justify-content: center;
    margin-bottom: 0.3cm;
}
.img-bloco {
    flex: 1 1 auto;
    max-width: 100%;
    text-align: center;
    page-break-inside: avoid;
}
.img-bloco-metade {
    flex: 1 1 45%;
    max-width: 48%;
    text-align: center;
    page-break-inside: avoid;
}
.img-bloco img, .img-bloco-metade img {
    max-width: 100%;
    max-height: 9cm;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}
.img-titulo {
    font-size: 8.5pt;
    font-weight: 600;
    color: #16213e;
    margin: 0.1cm 0 0.03cm 0;
}
.img-desc {
    font-size: 7.5pt;
    color: #666;
    margin: 0 0 0.3cm 0;
    font-style: italic;
}
"""

# ==============================================================================
# SECÇÕES A EXCLUIR DO PDF (conteúdo detalhado para desenvolvedores)
# ==============================================================================
PDF_EXCLUDE_HEADINGS = [
    "### 2.6",   # Pipeline — algoritmos detalhados
    "### 2.7",   # Bugs identificados e corrigidos
    "## 6.",     # Catálogo de arquivos gerados
    "## 7.",     # Metodologia PM² — rastreabilidade
    "## 8.",     # Execução do pipeline
]

# ==============================================================================
# MAPA DE IMAGENS INLINE — injetadas após as seções relevantes
# ==============================================================================
# Formato: { "heading_fragment": [ (arquivo, título, descrição, layout) ] }
# layout: "full" | "half" (side-by-side para pares)
IMAGENS_INLINE = [
    {
        # Injeta após a seção de Discovery (3.2.1)
        "heading": "3.2.1 Descoberta",
        "imgs": [
            ("dfg_frequencia.png",
             "Fig. A1 — DFG de Frequência (subset 2025, arcos ≥ 2% do máximo)",
             "Nós = atividades; espessura do arco = frequência. Arcos mais grossos = fluxo principal. "
             "Atividades cartoriais (confirmação, expedição, juntada) dominam — não atividades jurisdicionais.",
             "full"),
            ("dfg_performance.png",
             "Fig. A2 — DFG de Performance (tempo médio em dias entre transições, subset 2025)",
             "Mesma estrutura do DFG de frequência com rótulos de tempo médio em dias. "
             "Arco lento + frequente = gargalo sistêmico urgente. Arco raro + lento = exceção.",
             "full"),
            ("petri_net.png",
             "Fig. A3 — Rede de Petri — Log Completo (Inductive Miner, noise=0.2, subset 2025)",
             "Modelo formal descoberto sobre 1.277 casos ajuizados em 2025. "
             "Círculos = places (estados); retângulos = transitions (atividades); τ = transições silenciosas. "
             "Fitness 96.49% — modelo reproduz 96% das traces com fidelidade. "
             "Precision 14.3% esperada: processo ad hoc com 13.234 variantes únicas.",
             "full"),
            ("petri_net_cluster_dominante.png",
             "Fig. A4 — Rede de Petri — Cluster Dominante (Cluster 0, 48.4% dos casos, noise=0.4)",
             "Inductive Miner sobre o Cluster 0 (6.408 casos, mediana 588d). "
             "noise=0.4 filtra comportamentos em menos de 40% dos traces — modelo mais limpo. "
             "Representa o padrão comportamental dominante: casos sem recursos e encerramentos diretos.",
             "full"),
            ("petri_net_cluster3_top20v.png",
             "Fig. A5 — Rede de Petri — Top-20 Variantes do Cluster Dominante (noise=0.3)",
             "Modelo mais legível: restringe o Cluster 0 às 20 variantes mais frequentes antes da mineração. "
             "Reduz τ-transitions causadas por comportamento ad hoc. "
             "Mostra o rito predominante sem ruído das variantes raras.",
             "full"),
        ],
    },
    {
        # Injeta após a seção de Variantes (3.2.2)
        "heading": "3.2.2 Análise de Variantes",
        "imgs": [
            ("variantes_pareto.png",
             "Fig. B1 — Pareto de Variantes",
             "13.234 variantes únicas para 13.234 casos — cada processo seguiu caminho completamente distinto.",
             "full"),
        ],
    },
    {
        # Injeta após Performance Temporal (3.2.3)
        "heading": "3.2.3 Análise de Performance",
        "imgs": [
            ("throughput_time.png",
             "Fig. B2 — Throughput Time (Tempo de Ciclo)",
             "Mediana: 755 dias. P90: 1.489 dias. Cauda longa indica casos extremos.",
             "half"),
            ("sojourn_time.png",
             "Fig. B3 — Transition Time — Top 15 Atividades",
             "Tempo médio de espera após cada atividade. Proxy de sojourn time.",
             "half"),
        ],
    },
    {
        # Injeta após Gargalos (3.2.4)
        "heading": "3.2.4 Análise de Gargalos",
        "imgs": [
            ("bottlenecks.png",
             "Fig. B4 — Top 10 Gargalos — Transições A→B mais lentas",
             "Média ≈ mediana: problema sistêmico. Média >> mediana: outliers isolados.",
             "full"),
        ],
    },
    {
        # Injeta após Rework (3.2.5)
        "heading": "3.2.5 Análise de Rework",
        "imgs": [
            ("rework.png",
             "Fig. C1 — Rework — 100% dos casos com pelo menos 1 repetição",
             "Top 15 atividades por total de repetições no mesmo processo.",
             "full"),
        ],
    },
    {
        # Injeta após Organizacional (3.2.6)
        "heading": "3.2.6 Perspectiva Organizacional",
        "imgs": [
            ("organizacional.png",
             "Fig. C2 — Volume e Duração Mediana por Vara (Órgão Julgador)",
             "Variação de desempenho entre varas indica despadronização de gestão.",
             "full"),
        ],
    },
    {
        # Injeta após Conformance (3.2.7)
        "heading": "3.2.7 Conformance",
        "imgs": [
            ("conformance_fitness.png",
             "Fig. D1 — Fitness Token Based Replay (subset 2025, amostra 500 casos)",
             "Fitness médio: 96.49%. Concentração em 1.0 = alta conformidade com modelo descoberto.",
             "full"),
        ],
    },
    {
        # Injeta após K-Means (3.2.8)
        "heading": "3.2.8 Agrupamento",
        "imgs": [
            ("TJPR_Acao_Penal___Procedimento_Ordinario_clusters.png",
             "Fig. E1 — K-Means: 4 Clusters de Comportamento Processual",
             "Cluster 0: 48.4% (6.408 casos, med. 588d). Cluster 1: 27.1% (3.583 casos, med. 1.072d).",
             "full"),
        ],
    },
    {
        # Injeta após seção de Violência Doméstica (5.3)
        "heading": "Violência Doméstica",
        "imgs": [
            ("violencia_vs_geral.png",
             "Fig. F1 — Duração Total: Violência/Protetiva vs. Outros AP",
             "Mediana violência > outros AP — ausência de prioridade operacional (CNJ Res. 254/2018).",
             "half"),
            ("violencia_sla_total.png",
             "Fig. F2 — Distribuição de Duração por Categoria (Violência/Protetiva)",
             "55% dos casos acima de 365 dias. Máximo: 2.113 dias.",
             "half"),
            ("violencia_por_cluster.png",
             "Fig. F3 — Violência por Cluster K-Means",
             "Distribuição dos 8.585 casos de violência/protetiva pelos 4 clusters.",
             "full"),
        ],
    },
]


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

_MAX_PX = 3000   # largura máxima antes de rescale (pixels)

def img_to_b64(path: str) -> str | None:
    """
    Lê PNG e retorna base64. Se PIL disponível, redimensiona imagens muito
    largas/altas (> _MAX_PX px) para evitar falhas no WeasyPrint com
    imagens de Petri Net de dezenas de milhares de pixels.
    """
    if not os.path.exists(path):
        return None

    if _PIL_OK:
        try:
            _PILImage.MAX_IMAGE_PIXELS = None   # desabilita decompression bomb check
            with _PILImage.open(path) as img:
                w, h = img.size
                if w > _MAX_PX or h > _MAX_PX:
                    ratio = min(_MAX_PX / w, _MAX_PX / h)
                    new_w = max(1, int(w * ratio))
                    new_h = max(1, int(h * ratio))
                    img   = img.resize((new_w, new_h), _PILImage.LANCZOS)
                    print(f"      [resize] {os.path.basename(path)}: {w}×{h} → {new_w}×{new_h}")
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                return base64.b64encode(buf.getvalue()).decode("ascii")
        except Exception as e:
            print(f"      [AVISO] PIL falhou para {path}: {e} — usando arquivo original")

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def build_img_block_html(fname: str, titulo: str, desc: str, layout: str,
                         imgs_dir: str) -> str:
    """Retorna HTML de um bloco de imagem. layout: 'full' ou 'half'."""
    fpath = os.path.join(imgs_dir, fname)
    b64   = img_to_b64(fpath)
    if b64 is None:
        return f'<p style="color:#bbb;font-size:7pt;">[{fname} — imagem não encontrada]</p>'
    css_class = "img-bloco-metade" if layout == "half" else "img-bloco"
    return (
        f'<div class="{css_class}">'
        f'<p class="img-titulo">{titulo}</p>'
        f'<img src="data:image/png;base64,{b64}" />'
        f'<p class="img-desc">{desc}</p>'
        f'</div>'
    )


def build_inline_section_html(entrada: dict, imgs_dir: str) -> str:
    """Monta o bloco HTML de imagens para um grupo."""
    imgs     = entrada["imgs"]
    has_half = any(layout == "half" for _, _, _, layout in imgs)

    if has_half:
        # Agrupa blocos "half" em linhas de 2; "full" sozinhos
        html_parts = ['<div class="img-inline">']
        i = 0
        while i < len(imgs):
            fname, titulo, desc, layout = imgs[i]
            if layout == "half" and i + 1 < len(imgs) and imgs[i + 1][3] == "half":
                # Par side-by-side
                html_parts.append('<div class="img-inline-row">')
                html_parts.append(build_img_block_html(fname, titulo, desc, "half", imgs_dir))
                fn2, tt2, dd2, _ = imgs[i + 1]
                html_parts.append(build_img_block_html(fn2, tt2, dd2, "half", imgs_dir))
                html_parts.append('</div>')
                i += 2
            else:
                html_parts.append(build_img_block_html(fname, titulo, desc, "full", imgs_dir))
                i += 1
        html_parts.append('</div>')
        return "\n".join(html_parts)
    else:
        # Todos "full"
        parts = ['<div class="img-inline">']
        for fname, titulo, desc, layout in imgs:
            parts.append(build_img_block_html(fname, titulo, desc, "full", imgs_dir))
        parts.append('</div>')
        return "\n".join(parts)


def strip_sections(md_text: str, headings_to_exclude: list[str]) -> str:
    """
    Remove seções do Markdown a partir de um heading específico
    até o próximo heading do mesmo nível ou superior.

    Ignora linhas dentro de fenced code blocks (``` ... ```) para não
    confundir comentários bash (# step) com headings Markdown.
    """
    lines      = md_text.split("\n")
    result     = []
    skipping   = False
    skip_lvl   = 0
    in_fence   = False      # dentro de bloco ```...```

    for line in lines:
        # Controle de fenced code block
        if line.strip().startswith("```"):
            in_fence = not in_fence

        # Só interpretar headings fora de code blocks
        if not in_fence:
            m = re.match(r"^(#{1,6})\s", line)
            if m:
                lvl = len(m.group(1))
                # Terminar skip se alcançamos heading de nível igual/superior
                if skipping and lvl <= skip_lvl:
                    skipping = False
                # Verificar se este heading deve ser excluído
                if not skipping:
                    for h in headings_to_exclude:
                        if line.startswith(h):
                            skipping = True
                            skip_lvl = lvl
                            break

        if not skipping:
            result.append(line)

    return "\n".join(result)


def inject_images_inline(html: str, imgs_dir: str,
                         injections: list[dict]) -> str:
    """
    Insere blocos de imagem no HTML após seções específicas.

    Para cada entrada em injections, localiza o heading HTML que contenha
    o fragmento de texto e insere o bloco de imagens ANTES do próximo
    heading de nível igual ou superior (ou seja, no final da seção).
    """
    for entrada in injections:
        frag = entrada["heading"]
        # Regex: qualquer <h2>...<h3>...<h4> que contenha o fragmento
        pattern = rf'(<h[234][^>]*>[^<]*{re.escape(frag)}[^<]*</h[234]>)'
        m = re.search(pattern, html, re.IGNORECASE)
        if not m:
            # Tentar match parcial sem re.escape (para acentos)
            pattern2 = rf'(<h[234][^>]*>(?=[^<]*{frag[:12]})[^<]*</h[234]>)'
            m = re.search(pattern2, html, re.IGNORECASE)
        if not m:
            continue

        # Determinar onde termina a seção atual (antes do próximo heading ≤ mesmo nível)
        heading_tag = m.group(1)
        cur_lvl_m   = re.match(r"<h([234])", heading_tag)
        cur_lvl     = int(cur_lvl_m.group(1)) if cur_lvl_m else 4

        search_from = m.end()
        # Procurar próximo heading do mesmo nível ou superior
        next_h      = re.search(rf'<h[{1}{cur_lvl}]', html[search_from:])
        if next_h:
            insert_at = search_from + next_h.start()
        else:
            insert_at = len(html)

        img_html  = build_inline_section_html(entrada, imgs_dir)
        html      = html[:insert_at] + img_html + html[insert_at:]

    return html


def md_to_html(md_text: str) -> str:
    """Converte Markdown → HTML com extensões de tabela e blocos de código."""
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    return md.convert(md_text)


def build_capa_html() -> str:
    return """
<div class="capa">
  <span class="capa-badge">Projeto Acadêmico — Mineração de Processos</span>
  <h1>Ação Penal — Procedimento Ordinário<br>no TJPR</h1>
  <h2>Análise via PM² Process Mining Methodology</h2>
  <div class="capa-meta">
    <strong>Tribunal:</strong> Tribunal de Justiça do Paraná (TJPR)<br>
    <strong>Período de ajuizamento:</strong> 01/01/2020 → 16/05/2026<br>
    <strong>Classe processual:</strong> Ação Penal - Procedimento Ordinário (CPP arts. 394–405)<br>
    <strong>Total de casos:</strong> 13.234 processos fechados (50.000 extraídos)<br>
    <strong>~64,9% dos casos:</strong> violência doméstica/protetiva (Lei Maria da Penha)<br>
    <strong>Tipo de log:</strong> LO — Log Original (API CNJ Datajud)
  </div>
</div>
"""


# ==============================================================================
# MAIN
# ==============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Gera PDF do Relatório PM²")
    parser.add_argument(
        "--output",
        default=os.path.join(ROOT, "output", "RELATORIO_PM2_AcaoPenal.pdf"),
        help="Caminho do PDF de saída",
    )
    parser.add_argument(
        "--sem-filtro", action="store_true",
        help="Incluir no PDF todas as seções (sem remover seções técnicas)",
    )
    args = parser.parse_args()

    md_path  = os.path.join(ROOT, "RELATORIO_PM2.md")
    imgs_dir = os.path.join(ROOT, "analises", "imgs")
    out_path = args.output

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if not os.path.exists(md_path):
        sys.exit(f"[ERRO] Arquivo não encontrado: {md_path}")

    print(f"[INFO] Lendo {md_path}...")
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()

    # Remover seções técnicas/verbosas do PDF
    if not args.sem_filtro:
        print("[INFO] Filtrando seções técnicas para o PDF...")
        md_text = strip_sections(md_text, PDF_EXCLUDE_HEADINGS)

    print("[INFO] Convertendo Markdown → HTML...")
    body_html = md_to_html(md_text)

    print("[INFO] Injetando imagens inline nas seções relevantes...")
    body_html = inject_images_inline(body_html, imgs_dir, IMAGENS_INLINE)

    capa_html = build_capa_html()

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Relatório PM² — Ação Penal · TJPR</title>
</head>
<body>
{capa_html}
<div class="conteudo">
{body_html}
</div>
</body>
</html>"""

    print(f"[INFO] Gerando PDF → {out_path} ...")
    css = CSS(string=CSS_STYLE)
    HTML(string=full_html, base_url=ROOT).write_pdf(out_path, stylesheets=[css])

    size_mb = os.path.getsize(out_path) / 1_048_576
    print(f"[INFO] PDF gerado: {out_path}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
