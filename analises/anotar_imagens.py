"""
Adiciona painel de interpretacao abaixo de cada imagem de analise.
Gera versoes _annotado.png sem sobrescrever os originais.
"""
import os
import textwrap
import warnings
warnings.filterwarnings("ignore")

from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None  # desabilita limite de decompressao

IMGS = os.path.join(os.path.dirname(__file__), "imgs")

# -----------------------------------------------------------------------
# Textos de anotacao por imagem
# -----------------------------------------------------------------------
ANOTACOES = {
    "dfg_frequencia.png": {
        "titulo": "DFG de Frequencia — Como Interpretar",
        "linhas": [
            "TIPO: Directly-Follows Graph (DFG) — mostra quantas vezes B ocorreu imediatamente apos A",
            "NOS: tamanho/cor proporcional a frequencia da atividade no dataset",
            "ARCOS: espessura proporcional ao numero de vezes que a transicao A→B ocorreu",
            "LOOPS: arcos que voltam ao mesmo no = atividade repetida no mesmo processo (rework)",
            "FILTRO TJPR: 1.277 casos de 2025; arcos >= 2% do maximo (201 de 3.497 arcos totais)",
            "ACHADO: caminho principal visivel pelos arcos mais grossos; bifurcacoes = desvios processuais",
        ],
    },
    "dfg_performance.png": {
        "titulo": "DFG de Performance — Como Interpretar",
        "linhas": [
            "TIPO: Directly-Follows Graph com tempo medio entre atividades (em dias)",
            "ARCOS: numero = tempo medio em dias entre A e B (nao frequencia)",
            "ARCO GROSSO + NUMERO ALTO: gargalo sistemico urgente (muitos casos demoram nessa transicao)",
            "ARCO FINO + NUMERO ALTO: excecao ou desvio raro com demora extrema",
            "GARGALO #1 TJPR: Mero expediente → Recebimento = 235,9 dias medios",
            "INTERPRETACAO: processos aguardam distribuicao/recebimento por quase 8 meses em media",
        ],
    },
    "petri_net.png": {
        "titulo": "Rede de Petri (Inductive Miner, noise=0.2) — Como Interpretar",
        "linhas": [
            "TIPO: Modelo formal de processo descoberto automaticamente pelo Inductive Miner",
            "CIRCULOS (places): estados do processo (o que esta esperando acontecer)",
            "RETANGULOS COLORIDOS (transitions): atividades processuais observadas nos dados",
            "RETANGULOS PRETOS (tau/silent): logica de roteamento — XOR-split, AND-join, loops; nao sao erros",
            "MUITOS TAU: cada variante no dataset = caminho unico → o minerador precisou de muitos desvios para cobrir tudo",
            "BASE: 1.277 casos de 2025 | 194 places / 367 transitions | noise_threshold=0.2",
            "USO: base para conformance check (token replay) — mede se casos reais seguiram este modelo",
        ],
    },
    "petri_net_noise01.png": {
        "titulo": "Rede de Petri (noise=0.1) — Versao Compacta",
        "linhas": [
            "TIPO: Inductive Miner com noise_threshold=0.1 — aceita menos ruido, modelo mais simples",
            "ESTRUTURA: 58 places / 121 transitions (55 rotuladas + 66 tau)",
            "COMPARACAO: noise=0.2 tem 194 places/367 transitions — noise=0.1 e ~3x mais compacto",
            "PARADOXO: noise=0.3 e 0.5 sao mais complexos que 0.2 para este dataset (alta variancia de variantes)",
            "INTERPRETACAO: modelo simplificado captura fluxo principal mas ignora mais casos excepcionais",
        ],
    },
    "variantes_pareto.png": {
        "titulo": "Pareto de Variantes — Como Interpretar",
        "linhas": [
            "TIPO: Barras (frequencia por variante) + linha cumulativa (curva de Pareto)",
            "VARIANTE: sequencia unica de atividades de um processo — cada caminho diferente = variante diferente",
            "CURVA INGREME COM POUCAS VARIANTES: processo padronizado (poucos caminhos concentram maioria dos casos)",
            "CURVA PLANA COM MUITAS VARIANTES: alta heterogeneidade — cada caso segue caminho proprio",
            "ACHADO TJPR: 6.499 variantes unicas para 6.499 casos fechados — MAXIMA heterogeneidade processual",
            "IMPLICACAO: sem padronizacao de fluxo; cada processo e tratado de forma diferente pelas varas",
        ],
    },
    "throughput_time.png": {
        "titulo": "Throughput Time — Como Interpretar",
        "linhas": [
            "TIPO: Histograma de duracao total (ajuizamento → encerramento) com linha de mediana",
            "EIXO X: duracao em dias | EIXO Y: numero de casos naquela faixa",
            "LINHA VERTICAL: mediana — metade dos casos termina antes, metade depois deste valor",
            "DISTRIBUICAO CONCENTRADA: processos resolvidos em tempo similar (padronizado)",
            "CAUDA LONGA A DIREITA: maioria razoavel, mas outliers extremos existem",
            "ACHADO TJPR: Mediana=537d | P90=943d | P95=1.035d | Max=1.181d — alta variancia",
            "REFERENCIA: CF art. 5 LXXVIII garante 'razoavel duracao do processo' — 537d indica problema sistemico",
        ],
    },
    "sojourn_time.png": {
        "titulo": "Sojourn Time — Como Interpretar",
        "linhas": [
            "TIPO: Barras horizontais com top 15 atividades de maior tempo de espera medio",
            "O QUE MEDE: tempo que o processo FICA PARADO naquela atividade antes de avancar",
            "DIFERENCA DO DFG: sojourn = tempo NA atividade; DFG performance = tempo ENTRE atividades",
            "ALTO SOJOURN: fila acumulada — cartorio ou gabinete com trabalho pendente nessa etapa",
            "USO: identificar onde o processo 'trava' (espera acoes internas) vs onde demora a transicao (espera externas)",
        ],
    },
    "bottlenecks.png": {
        "titulo": "Gargalos (Bottlenecks) — Como Interpretar",
        "linhas": [
            "TIPO: Barras duplas — azul=media / laranja=mediana por transicao A→B (top 10 mais lentas)",
            "MEDIA >> MEDIANA: outliers puxam a media — problema em casos individuais extremos, nao sistemico",
            "MEDIA ≈ MEDIANA: problema sistemico uniforme — TODOS os casos demoram nessa transicao",
            "GARGALO #1 TJPR: Mero expediente → Recebimento = 235,9d media ≈ mediana → ESTRUTURAL",
            "PRIORIDADE: intervir nas transicoes com media ≈ mediana e valores altos (problema real e uniforme)",
        ],
    },
    "rework.png": {
        "titulo": "Rework — Como Interpretar",
        "linhas": [
            "TIPO: Barras horizontais com top 15 atividades mais repetidas (rework = mesma atividade > 1x no mesmo caso)",
            "ALTO REWORK: atividade volta — decisao revisada, correcao, ciclo processual repetitivo",
            "REWORK OPERACIONAL: erro de registro, juntada duplicada — indica problema de SI ou cartorio",
            "REWORK ESTRUTURAL: recurso/impugnacao retorna o processo a etapa anterior — previsto em lei",
            "ACHADO TJPR: 100% dos casos (6.498/6.499) tem pelo menos 1 repeticao — rework sistemico",
            "CANDIDATOS A REDESENHO: atividades com mais rework sao alvos de automacao ou simplificacao",
        ],
    },
    "organizacional.png": {
        "titulo": "Perspectiva Organizacional — Como Interpretar",
        "linhas": [
            "TIPO: Dois graficos — (1) volume de eventos por vara (top 20) e (2) duracao mediana por vara",
            "VARA ALTO VOLUME + ALTA DURACAO: sobrecarregada e lenta → intervencao prioritaria",
            "VARA BAIXO VOLUME + ALTA DURACAO: possivel problema de gestao ou casos excepcionalmente complexos",
            "VARIACAO GRANDE ENTRE VARAS: desigualdade de desempenho — falta padronizacao de gestao",
            "ACHADO TJPR: mediana minima 695d, maxima 878d — variacao de 183d entre varas criminais",
            "IMPLICACAO: risco constitucional (CF art. 5 LXXVIII) e violacao isonomia processual entre varas",
        ],
    },
    "conformance_fitness.png": {
        "titulo": "Conformance — Como Interpretar",
        "linhas": [
            "TIPO: Histograma de fitness (Token Based Replay) em amostra de 500 casos",
            "FITNESS 1.0: caso seguiu perfeitamente o modelo descoberto | FITNESS 0.0: nenhuma atividade compativel",
            "CONCENTRACAO EM 1.0: maioria dos casos seguiu o modelo (alta conformidade)",
            "FITNESS < 0.8: caso desviou significativamente — excecao, erro de registro ou rework extremo",
            "METRICAS TJPR (500-sample de 6.499 casos): Fitness=95,51% | Precisao=14,28% | Generalizacao=88,96% | Simplicidade=60,58%",
            "PRECISAO BAIXA (14%): modelo permite muitos caminhos que nao ocorreram — reflete as 6.499 variantes unicas",
            "ATENCAO: modelo aqui e o DESCOBERTO (real), NAO o normativo do CPP",
        ],
    },
    "TJPR_Acao_Penal___Procedimento_Ordinario_clusters.png": {
        "titulo": "Clusters K-Means — Como Interpretar",
        "linhas": [
            "TIPO: 4 subplots — scatter duracao×eventos, tamanho dos clusters, mediana por cluster, variantes por cluster",
            "SCATTER: cada ponto = 1 caso; cor = cluster; clusters bem separados = comportamentos distintos identificaveis",
            "CLUSTER 0 (1.733 casos, 26,7%): mediana 742d, 218 eventos — processos longos e complexos",
            "CLUSTER 1 (3.273 casos, 50,3%): mediana 438d, 154 eventos — fluxo padrao (cluster dominante)",
            "CLUSTER 2 (7 casos, 0,1%): mediana 805d — casos extremos/atipicos, amostra minuscula",
            "CLUSTER 3 (1.486 casos, 22,8%): mediana 532d, 126 eventos — processos intermediarios",
            "VIOLENCIA: cluster 0 tem 80,6% violencia + maior duracao (742d) = pior cenario operacional",
        ],
    },
    "violencia_sla_liminar.png": {
        "titulo": "SLA Liminar por Categoria — Como Interpretar",
        "linhas": [
            "TIPO: Boxplot + swarmplot de dias ate liminar por categoria | Linha vermelha = 2 dias (Lei Maria da Penha art. 18)",
            "POR QUE QUASE VAZIO: AP Ordinaria NAO e o instrumento de medidas de urgencia",
            "CORRETO: liminares protetivas sao apreciadas em AUTOS SEPARADOS (cautelar autonoma, art. 19 Lei 11.340/2006)",
            "ACHADO TJPR: apenas 4/5.405 casos (0,07%) tiveram liminar registrada na AP",
            "DOS 4 CASOS: 2 dentro do prazo (0,31d e 0,64d) | 1 levemente acima (2,56d) | 1 muito acima (19,1d)",
            "GRAFICO VAZIO = ACHADO ESTRUTURAL: fluxo de urgencia esta corretamente segregado do processo penal principal",
        ],
    },
    "violencia_sla_total.png": {
        "titulo": "Duracao Total por Caso — Como Interpretar",
        "linhas": [
            "TIPO: Barras horizontais (1 barra = 1 caso), cor por categoria | Linha vermelha = 365 dias (CNJ Res. 254/2018)",
            "BARRAS A DIREITA DA LINHA: casos acima do alerta de 365 dias",
            "Contra a Mulher (2.687 casos): mediana 419,9d | 41,7% acima de 365d | max 1.163d",
            "Lesao/Condicao de Mulher (2.022 casos): mediana 400,6d | 41,9% acima de 365d | max 1.113d",
            "Desc. Medida Protetiva (651 casos): mediana 255,2d | 22,4% acima de 365d — mais rapido (prova mais simples)",
            "Violencia Psicologica (41 casos): mediana 372,6d | 41,5% acima de 365d",
            "TOTAL: 2.133/5.405 casos (39,5%) ultrapassaram 365 dias | candidatos a auditoria: filtrar alerta_total==True no CSV",
        ],
    },
    "violencia_vs_geral.png": {
        "titulo": "Violin Plot: Violencia vs. Outros AP — Como Interpretar",
        "linhas": [
            "TIPO: Violin plot — largura em cada altura = densidade de casos naquela duracao",
            "EIXO Y: duracao total em dias (ajuizamento → transito em julgado)",
            "LINHA INTERNA: mediana | CAIXA: IQR 25-75% | CAUDA: outliers",
            "VIOLINO MAIS LARGO EM FAIXA: mais casos concentrados naquela duracao",
            "SE PRIORIDADE EXISTISSE: violino violencia deveria estar deslocado para BAIXO (duracoes menores)",
            "ACHADO TJPR: mediana violencia=391,1d > outros AP=366,5d — INVERSO do que CNJ Res. 254/2018 exige",
            "AMBOS TEM CAUDA LONGA: problema sistemico em toda AP, mas violencia e proporcionalmente pior",
        ],
    },
    "violencia_sla_cumprimento.png": {
        "titulo": "% Casos por Faixa de Prazo de Liminar — Como Interpretar",
        "linhas": [
            "TIPO: Barras verticais com % de casos por faixa: <=2d / 3-7d / 8-30d / >30d",
            "BARRA <=2 DIAS ALTA: boa conformidade com Lei Maria da Penha art. 18 (prazo de 48h)",
            "ACHADO TJPR: 5.401/5.405 casos (99,93%) sem liminar registrada na AP — barras praticamente vazias",
            "POR QUE: AP Ordinaria nao usa liminar como instrumento central (medidas protetivas = autos separados)",
            "USO CORRETO: esta analise e relevante para mandados de segurança e cautelares de medida protetiva de urgencia",
            "PARA MEDIR CNJ ART. 18: necessario analisar autos de medida protetiva de urgencia (classe processual distinta)",
        ],
    },
    "violencia_por_cluster.png": {
        "titulo": "Violencia por Cluster K-Means — Como Interpretar",
        "linhas": [
            "TIPO: Stacked bar — proporcao violencia/protetiva (escuro) vs. outros AP (claro) por cluster",
            "Cluster 0 (1.733 casos): 80,6% violencia | mediana 742d — mais lento, alta concentracao de violencia",
            "Cluster 1 (3.273 casos, dominante): 83,5% violencia | mediana 438d — fluxo padrao",
            "Cluster 2 (7 casos): 57,1% violencia | mediana 805d — atipico, amostra minuscula",
            "Cluster 3 (1.486 casos): 85,5% violencia | mediana 532d — maior proporcao violencia de todos",
            "SE CNJ 254/2018 FUNCIONASSE: violencia deveria concentrar nos clusters MAIS RAPIDOS",
            "ACHADO: cluster mais lento (742d) tem 80,6% violencia = 1.397 casos sem tratamento prioritario",
        ],
    },
}


def fazer_painel_texto(titulo, linhas, largura_px, dpi=150):
    """Gera imagem PIL com painel de texto."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    n_linhas = len(linhas)
    altura_pol = 0.5 + n_linhas * 0.38
    largura_pol = largura_px / dpi

    fig, ax = plt.subplots(figsize=(largura_pol, altura_pol))
    fig.patch.set_facecolor("#f0f4f8")
    ax.set_facecolor("#f0f4f8")
    ax.axis("off")

    y = 0.97
    ax.text(0.01, y, titulo,
            transform=ax.transAxes,
            fontsize=11, fontweight="bold", color="#1a3a5c",
            va="top", ha="left",
            fontfamily="monospace")
    y -= 0.07

    step = 0.85 / max(n_linhas, 1)
    for linha in linhas:
        # separar prefixo em negrito (ate primeiro ':')
        if ":" in linha[:25]:
            partes = linha.split(":", 1)
            ax.text(0.01, y, partes[0] + ":",
                    transform=ax.transAxes,
                    fontsize=9, fontweight="bold", color="#c0392b",
                    va="top", ha="left", fontfamily="monospace")
            # medir largura do prefixo
            txt_obj = ax.text(0.01, y, partes[0] + ":",
                              transform=ax.transAxes,
                              fontsize=9, fontweight="bold", color="#c0392b",
                              va="top", ha="left", fontfamily="monospace",
                              alpha=0)
            # offset aproximado pelo comprimento do prefixo
            offset = (len(partes[0]) + 2) * 0.008
            ax.text(0.01 + offset, y, partes[1].strip(),
                    transform=ax.transAxes,
                    fontsize=9, color="#2c3e50",
                    va="top", ha="left", fontfamily="monospace")
        else:
            ax.text(0.01, y, "• " + linha,
                    transform=ax.transAxes,
                    fontsize=9, color="#2c3e50",
                    va="top", ha="left", fontfamily="monospace")
        y -= step

    fig.tight_layout(pad=0.3)

    # converter para PIL
    from io import BytesIO
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).copy()


def anotar(nome_arquivo):
    if nome_arquivo not in ANOTACOES:
        print(f"  [SKIP] sem anotacao para {nome_arquivo}")
        return

    caminho = os.path.join(IMGS, nome_arquivo)
    if not os.path.exists(caminho):
        print(f"  [SKIP] arquivo nao encontrado: {nome_arquivo}")
        return

    print(f"  Anotando {nome_arquivo} ...", end=" ", flush=True)

    # abrir imagem original
    img_orig = Image.open(caminho).convert("RGB")
    w, h = img_orig.size

    # redimensionar imagens muito grandes para nao explodir memoria
    MAX_W = 4000
    if w > MAX_W:
        escala = MAX_W / w
        img_orig = img_orig.resize((MAX_W, int(h * escala)), Image.LANCZOS)
        w, h = img_orig.size

    # gerar painel de texto com mesma largura
    info = ANOTACOES[nome_arquivo]
    painel = fazer_painel_texto(info["titulo"], info["linhas"], w)

    # redimensionar painel para largura exata
    pw, ph = painel.size
    if pw != w:
        painel = painel.resize((w, int(ph * w / pw)), Image.LANCZOS)

    # empilhar verticalmente
    total_h = h + painel.height
    composto = Image.new("RGB", (w, total_h), (240, 244, 248))
    composto.paste(img_orig, (0, 0))
    composto.paste(painel, (0, h))

    # salvar
    base, ext = os.path.splitext(nome_arquivo)
    saida = os.path.join(IMGS, base + "_annotado.png")
    composto.save(saida, "PNG", optimize=True)
    print(f"-> {os.path.basename(saida)} ({composto.size[0]}x{composto.size[1]})")


if __name__ == "__main__":
    print("=== Anotando imagens ===")
    for nome in ANOTACOES:
        anotar(nome)
    print("\nConcluido.")
