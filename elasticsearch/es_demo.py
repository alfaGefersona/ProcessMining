"""
Demo Elasticsearch — Seminário NoSQL #05
========================================
Demonstra 6 features do Elasticsearch usando dados judiciais (TJPR).

Executar DEPOIS de es_indexer.py.

Uso:
    python elasticsearch/es_demo.py

Features demonstradas:
    1. Full-text search  — relevance score automático
    2. Multi-match       — busca em múltiplos campos com boost
    3. Bool query        — must + should + filter combinados
    4. Highlight         — marca trechos que casaram com a busca
    5. Aggregations      — contagem, histograma temporal, termos
    6. search_after      — paginação eficiente (como Datajud usa)
"""

import json
import sys
from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
INDEX  = "processos_judiciais"

SEPARATOR = "=" * 60


def _pp(data: dict | list, indent: int = 2) -> str:
    return json.dumps(data, ensure_ascii=False, indent=indent)


def _header(titulo: str):
    print(f"\n{SEPARATOR}")
    print(f"  {titulo}")
    print(SEPARATOR)


def _hits_summary(hits: list[dict], max_show: int = 3):
    print(f"  Total retornado: {len(hits)} (mostrando até {max_show})\n")
    for hit in hits[:max_show]:
        src   = hit["_source"]
        score = hit.get("_score", "n/a")
        print(f"  score={score}")
        print(f"    processo  : {src.get('numeroProcesso')}")
        print(f"    classe    : {src.get('classe')}")
        print(f"    assunto   : {src.get('assunto_principal')}")
        print(f"    tribunal  : {src.get('tribunal')}")
        print(f"    eventos   : {src.get('total_eventos')}")
        if "highlight" in hit:
            print(f"    highlight : {hit['highlight']}")
        print()


# ---------------------------------------------------------------------------
# Demo 1 — Full-text search
# ---------------------------------------------------------------------------

def demo_fulltext(es: Elasticsearch):
    _header("DEMO 1 — Full-text Search (relevance scoring)")
    print("  Busca: assunto contém 'violência doméstica'")
    print("  ES tokeniza, aplica stemmer PT, calcula TF-IDF/BM25.\n")

    resp = es.search(
        index=INDEX,
        query={
            "match": {
                "assunto_principal": {
                    "query":    "violência doméstica",
                    "operator": "or",   # retorna docs com qualquer termo
                }
            }
        },
        size=3,
    )

    _hits_summary(resp["hits"]["hits"])
    print(f"  Total estimado no índice: {resp['hits']['total']['value']}")


# ---------------------------------------------------------------------------
# Demo 2 — Multi-match com boost
# ---------------------------------------------------------------------------

def demo_multimatch(es: Elasticsearch):
    _header("DEMO 2 — Multi-match com boost de campo")
    print("  Busca 'homicídio feminicídio' em classe E assunto.")
    print("  assunto_principal^2 → peso dobrado no score.\n")

    resp = es.search(
        index=INDEX,
        query={
            "multi_match": {
                "query":  "homicídio feminicídio",
                "fields": ["assunto_principal^2", "classe", "atividades"],
                "type":   "best_fields",
            }
        },
        size=3,
    )

    _hits_summary(resp["hits"]["hits"])


# ---------------------------------------------------------------------------
# Demo 3 — Bool query (must + should + filter)
# ---------------------------------------------------------------------------

def demo_bool(es: Elasticsearch):
    _header("DEMO 3 — Bool Query (must + should + filter)")
    print("  must  : classe contém 'Ordinário'")
    print("  should: assunto contém 'Lesão' OU 'Ameaça' (aumenta score)")
    print("  filter: grau = 'G1' (não afeta score, só filtra)\n")

    resp = es.search(
        index=INDEX,
        query={
            "bool": {
                "must": [
                    {"match": {"classe": "Ordinário"}}
                ],
                "should": [
                    {"match": {"assunto_principal": "Lesão"}},
                    {"match": {"assunto_principal": "Ameaça"}},
                ],
                "filter": [
                    {"term": {"grau": "G1"}}
                ],
                "minimum_should_match": 1,
            }
        },
        size=3,
    )

    _hits_summary(resp["hits"]["hits"])
    print(f"  Total estimado: {resp['hits']['total']['value']}")


# ---------------------------------------------------------------------------
# Demo 4 — Highlight
# ---------------------------------------------------------------------------

def demo_highlight(es: Elasticsearch):
    _header("DEMO 4 — Highlight (marca onde o texto casou)")
    print("  Busca 'estupro' e retorna trecho com <em> ao redor do match.\n")

    resp = es.search(
        index=INDEX,
        query={
            "match": {"assunto_principal": "estupro"}
        },
        highlight={
            "fields": {
                "assunto_principal": {
                    "pre_tags":  [">>> "],
                    "post_tags": [" <<<"],
                }
            }
        },
        size=3,
    )

    _hits_summary(resp["hits"]["hits"])


# ---------------------------------------------------------------------------
# Demo 5 — Aggregations
# ---------------------------------------------------------------------------

def demo_aggregations(es: Elasticsearch):
    _header("DEMO 5 — Aggregations (análise sem sair do ES)")

    # 5a: Distribuição por tribunal
    print("  [5a] Processos por tribunal (terms agg):\n")
    resp = es.search(
        index=INDEX,
        size=0,   # não precisa dos docs, só aggs
        aggs={
            "por_tribunal": {
                "terms": {"field": "tribunal", "size": 10}
            }
        },
    )
    for bucket in resp["aggregations"]["por_tribunal"]["buckets"]:
        print(f"    {bucket['key']:30s}  {bucket['doc_count']:>6} processos")

    # 5b: Distribuição por classe (top 5)
    print("\n  [5b] Top 5 classes processuais:\n")
    resp = es.search(
        index=INDEX,
        size=0,
        aggs={
            "por_classe": {
                "terms": {"field": "classe.keyword", "size": 5}
            }
        },
    )
    for bucket in resp["aggregations"]["por_classe"]["buckets"]:
        print(f"    {bucket['key']:40s}  {bucket['doc_count']:>6}")

    # 5c: Ajuizamentos por ano
    print("\n  [5c] Processos ajuizados por ano:\n")
    resp = es.search(
        index=INDEX,
        size=0,
        query={"exists": {"field": "data_ajuizamento"}},
        aggs={
            "por_ano": {
                "date_histogram": {
                    "field":             "data_ajuizamento",
                    "calendar_interval": "year",
                    "format":            "yyyy",
                    "min_doc_count":     1,
                }
            }
        },
    )
    for bucket in resp["aggregations"]["por_ano"]["buckets"]:
        bar = "#" * (bucket["doc_count"] // max(1, resp["hits"]["total"]["value"] // 40))
        print(f"    {bucket['key_as_string']}  {bar} {bucket['doc_count']}")


# ---------------------------------------------------------------------------
# Demo 6 — search_after (paginação eficiente)
# ---------------------------------------------------------------------------

def demo_search_after(es: Elasticsearch):
    _header("DEMO 6 — search_after (paginação sem degradar com offset)")
    print("  Método usado pelo Datajud para paginar 50k+ processos.")
    print("  Mais eficiente que from/size para grandes volumes.\n")

    # Página 1
    resp = es.search(
        index=INDEX,
        query={"match_all": {}},
        sort=[
            {"data_ajuizamento": {"order": "asc", "unmapped_type": "date"}},
            {"numeroProcesso":   {"order": "asc"}},
        ],
        size=3,
    )

    hits = resp["hits"]["hits"]
    print(f"  Página 1 — {len(hits)} docs")
    for h in hits:
        print(f"    {h['_source'].get('numeroProcesso')}  |  {h['_source'].get('data_ajuizamento', 'sem data')}")

    if not hits:
        print("  Sem resultados.")
        return

    last_sort = hits[-1]["sort"]
    print(f"\n  Cursor (sort values da última linha): {last_sort}")

    # Página 2
    resp2 = es.search(
        index=INDEX,
        query={"match_all": {}},
        sort=[
            {"data_ajuizamento": {"order": "asc", "unmapped_type": "date"}},
            {"numeroProcesso":   {"order": "asc"}},
        ],
        size=3,
        search_after=last_sort,
    )

    hits2 = resp2["hits"]["hits"]
    print(f"\n  Página 2 (após cursor) — {len(hits2)} docs")
    for h in hits2:
        print(f"    {h['_source'].get('numeroProcesso')}  |  {h['_source'].get('data_ajuizamento', 'sem data')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    es = Elasticsearch(ES_URL)

    if not es.ping():
        print(f"ERRO: Elasticsearch não responde em {ES_URL}.")
        print("      Suba com: docker compose up -d")
        sys.exit(1)

    count = es.count(index=INDEX)["count"]
    print(f"\nElasticsearch OK — índice '{INDEX}' com {count} documentos.\n")

    if count == 0:
        print("AVISO: índice vazio. Rode primeiro: python elasticsearch/es_indexer.py")
        sys.exit(1)

    demo_fulltext(es)
    demo_multimatch(es)
    demo_bool(es)
    demo_highlight(es)
    demo_aggregations(es)
    demo_search_after(es)

    print(f"\n{SEPARATOR}")
    print("  Kibana disponível em: http://localhost:5601")
    print("  Crie um Data View com index pattern: processos_judiciais")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
