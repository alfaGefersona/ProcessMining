"""
Configuração central do projeto.
Edite este arquivo para controlar o que é extraído e como é mapeado no XES.
"""

import os

# Diretório de saída dos arquivos XES (relativo à raiz do projeto)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

# ==============================================================================
# API
# ==============================================================================

API_KEY  = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
BASE_URL = "https://api-publica.datajud.cnj.jus.br"

# ==============================================================================
# TRIBUNAIS
# alias Elasticsearch → nome legível
# ==============================================================================

TRIBUNAIS = {
    "api_publica_tjpr": "TJPR",
    # "api_publica_tjrs": "TJRS",
}

# ==============================================================================
# PAGINAÇÃO E REDE
# ==============================================================================

# Processos por requisição (máx. 10 000 pela API)
PAGE_SIZE = 100

# Delay entre requisições em segundos — evita rate-limit
REQUEST_DELAY_SEC = 0.5

# Timeout por requisição em segundos (a API é lenta — não reduza abaixo de 60)
REQUEST_TIMEOUT = 90

# Tentativas por página antes de desistir e salvar o progresso parcial
MAX_RETRIES = 3

# Limite de processos por tribunal (None = sem limite)
MAX_PROCESSOS = 50000  # AP Ordinária sem filtro assunto 2023-2026

# ==============================================================================
# CAMPOS DO PROCESSO — trace no XES
# Formato: (chave_xes, caminho_no_json, tipo_xes)
# Tipos: "string" | "date" | "int" | "float" | "boolean"
# ==============================================================================

CAMPOS_TRACE = [
    # chave XES                  caminho no _source                tipo
    ("concept:name",             ["numeroProcesso"],               "string"),
    ("case:tribunal",            ["tribunal"],                     "string"),
    ("case:classe",              ["classe", "nome"],               "string"),
    ("case:assunto_principal",   ["assuntos", 0, "nome"],          "string"),
    ("case:orgao_julgador",      ["orgaoJulgador", "nome"],        "string"),
    ("case:data_ajuizamento",    ["dataAjuizamento"],              "date"),
    ("case:grau",                ["grau"],                         "string"),
    ("case:nivel_sigilo",        ["nivelSigilo"],                  "int"),
    # Adicione novos campos aqui. Exemplos:
    # ("case:valor_causa",       ["valorCausa"],                   "float"),
    # ("case:sistema",           ["sistema", "nome"],              "string"),
    # ("case:codigo_classe",     ["classe", "codigo"],             "int"),
]

# ==============================================================================
# CAMPOS EXTRAS DO MOVIMENTO — evento no XES
# concept:name, time:timestamp, lifecycle:transition e org:resource
# são controlados pela lógica de transformação e não devem ser listados aqui.
# Liste apenas campos adicionais que queira incluir no evento.
# ==============================================================================

CAMPOS_EVENTO_EXTRAS = [
    # chave XES               caminho dentro do movimento      tipo
    ("event:codigo_tpu",      ["codigo"],                      "int"),
    # Adicione novos campos aqui. Exemplos:
    # ("event:codigo_complemento", ["complementosTabelados", 0, "codigo"], "int"),
]

# ==============================================================================
# QUERY ELASTICSEARCH
# Modifique para filtrar os processos extraídos.
#
# Exemplos:
#   Por período:
#     "query": {"range": {"dataAjuizamento": {"gte": "20240101", "lte": "20241231"}}}
#
#   Por classe processual:
#     "query": {"term": {"classe.codigo": 7}}
#
#   Combinando:
#     "query": {"bool": {"must": [
#         {"range": {"dataAjuizamento": {"gte": "20240101"}}},
#         {"term": {"classe.codigo": 7}}
#     ]}}
# ==============================================================================

QUERY_BODY = {
    # Ação Penal - Procedimento Ordinário — violência (geral) + medidas protetivas/doméstica
    #
    # Filtros de assunto baseados na TPU-CNJ e Lei Maria da Penha (11.340/2006):
    #   L1 (baseline): toda AP Ordinária com qualquer tipo de violência
    #   L2 (subconjunto): violência contra mulher/doméstica/protetiva — filtrado em pós-processamento
    #
    # Termos de violência geral (L1):
    #   "Violência"   → cobre Violência Doméstica, Violência Psicológica, Violência Patrimonial
    #   "Lesão"       → Lesão Corporal, Lesão Cometida em Razão da Condição de Mulher
    #   "Homicídio"   → inclui Feminicídio (homicídio qualificado CP art. 121 §2º-A)
    #   "Feminicídio" → tipo qualificado de homicídio contra mulher
    #   "Estupro"     → crimes sexuais (Lei 12.015/2009)
    #   "Ameaça"      → crime comum em contextos de violência doméstica (CP art. 147)
    #
    # Termos específicos de medidas protetivas/doméstica (L2 — refinado em pós-processamento):
    #   "Doméstica"   → Violência Doméstica Contra a Mulher (Lei 11.340/2006)
    #   "Protetiva"   → Descumprimento de Medida Protetiva de Urgência
    #   "Mulher"      → Contra a Mulher, Lesão/Condição de Mulher, Violência Psicológica
    #
    # ⚠️  Filtro de FINALIZADOS não é possível via Elasticsearch (API não expõe campo
    # de status/situação). Filtragem de processos encerrados ocorre em pós-processamento:
    #   → exportar_filtrado.py detecta atividades terminais (Baixa Definitiva, Trânsito em julgado, etc.)
    #
    "query": {
        "bool": {
            "must": [
                {"match": {"classe.nome": "Procedimento Ordinário"}},
                {"range": {"dataAjuizamento": {
                    "gte": "20200101000000",   # 2020-01-01 — casos mais antigos têm maior % finalizados
                    "lte": "20260516235959",   # 2026-05-16 — data atual
                }}},
            ],
            "should": [
                # Violência geral (L1)
                {"match": {"assuntos.nome": "Violência"}},
                {"match": {"assuntos.nome": "Lesão"}},
                {"match": {"assuntos.nome": "Homicídio"}},
                {"match": {"assuntos.nome": "Feminicídio"}},
                {"match": {"assuntos.nome": "Estupro"}},
                {"match": {"assuntos.nome": "Ameaça"}},
                # Medidas protetivas / doméstica / mulher (L2)
                {"match": {"assuntos.nome": "Doméstica"}},
                {"match": {"assuntos.nome": "Protetiva"}},
                {"match": {"assuntos.nome": "Mulher"}},
            ],
            "minimum_should_match": 1,
        }
    },
    "sort": [
        {"dataHoraUltimaAtualizacao": {"order": "asc"}}
    ],
    "_source": True,
}

# ==============================================================================
# RE-EXTRAÇÃO PARA ANÁLISE DE HAPPY PATH (processos fechados)
# ==============================================================================
#
# O dataset padrão captura os 10.000 processos ordenados por última atualização,
# o que resulta em processos majoritariamente em andamento para tribunais ativos
# como o TJPR. Para análise de happy path é necessário ter processos que
# iniciaram E encerraram dentro do mesmo período.
#
# Para re-extrair TJPR com processos concluídos (ajuizados entre 2013 e 2026,
# tempo suficiente para encerramento), substitua QUERY_BODY acima por:
#
#   QUERY_BODY = {
#       "query": {
#           "range": {"dataAjuizamento": {
#               "gte": "20150101000000",   # formato: YYYYMMDDHHmmss (14 dígitos)
#               "lte": "20181231235959"
#           }}
#       },
#       "sort": [{"dataHoraUltimaAtualizacao": {"order": "asc"}}],
#       "_source": True,
#   }
#
#   Nota: filtro por classe.codigo não funciona nesta API pública.
#   Filtrar por classe após extração via: exportar_filtrado.py --classe "..."
#
# Códigos de classe comuns (TPU CNJ):
#   7   = Procedimento Comum Cível
#   40  = Execução Fiscal
#   436 = Termo Circunstanciado
#   1116 = Execução de Título Extrajudicial
#
# Após re-extração rode:
#   python analises/happy_path_report.py \
#       --classe "Procedimento Comum Cível" \
#       --data-inicio 2023-01-01 \
#       --data-fim 2026-12-31
# ==============================================================================
