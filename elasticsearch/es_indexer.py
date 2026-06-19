"""
Indexador Elasticsearch — Seminário NoSQL
=========================================
Lê o CSV gerado pelo pipeline (output/*.csv), agrupa por processo,
cria índice com mapping explícito e indexa via bulk API.

Uso:
    python elasticsearch/es_indexer.py
    python elasticsearch/es_indexer.py --csv output/TJPR_20240101_120000.csv

Requisito:
    pip install elasticsearch==8.13.0
"""

import argparse
import csv
import glob
import logging
import os
import sys
from collections import defaultdict

from elasticsearch import Elasticsearch, helpers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ES_URL   = "http://localhost:9200"
INDEX    = "processos_judiciais"

# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------
MAPPING = {
    "settings": {
        "analysis": {
            "filter": {
                "pt_stop": {
                    "type":      "stop",
                    "stopwords": "_portuguese_",
                },
                "pt_stem": {
                    "type":     "stemmer",
                    "language": "portuguese",
                },
                # Expansão de sinônimos antes do stemming.
                # Grupos derivacionais que o Snowball PT não conflui automaticamente.
                "pt_synonyms": {
                    "type": "synonym",
                    "synonyms": [
                        "violento, violenta, violentos, violentas, violência, violências => violência",
                        "doméstico, doméstica, domésticos, domésticas => doméstica",
                        "homicida, homicídio, homicídios => homicídio",
                        "feminicida, feminicídio, feminicídios => feminicídio",
                        "lesionado, lesionada, lesão, lesões => lesão",
                        "ameaçado, ameaçada, ameaça, ameaças => ameaça",
                        "estuprado, estuprada, estupro, estupros => estupro",
                    ],
                },
            },
            "analyzer": {
                "pt_custom": {
                    "type":      "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "pt_stop",
                        "pt_synonyms",    # sinônimos ANTES do stem
                        "pt_stem",
                    ],
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "numeroProcesso":   {"type": "keyword"},
            "tribunal":         {"type": "keyword"},
            "classe":           {
                "type":     "text",
                "analyzer": "pt_custom",
                "fields":   {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
            "assunto_principal": {
                "type":     "text",
                "analyzer": "pt_custom",
                "fields":   {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
            "orgao_julgador":   {"type": "keyword"},
            "data_ajuizamento": {"type": "date"},
            "grau":             {"type": "keyword"},
            "nivel_sigilo":     {"type": "integer"},
            # Array com nomes de todas as atividades do processo
            "atividades": {
                "type":     "text",
                "analyzer": "pt_custom",
            },
            "total_eventos":    {"type": "integer"},
        }
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_latest_csv() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    pattern = os.path.join(root, "output", "*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        log.error("Nenhum CSV encontrado em output/. Rode run_pipeline.py primeiro.")
        sys.exit(1)
    latest = files[-1]
    log.info(f"CSV encontrado: {latest}")
    return latest


def _read_csv(path: str) -> dict[str, dict]:
    """
    Agrupa linhas do event-log CSV por processo (case:concept:name).
    Retorna dict: numeroProcesso -> doc
    """
    processos: dict[str, dict] = defaultdict(lambda: {
        "atividades": [],
        "total_eventos": 0,
    })

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            num = row.get("case:concept:name", "").strip()
            if not num:
                continue

            p = processos[num]

            # Atributos do trace — preenchidos na primeira ocorrência
            if "numeroProcesso" not in p:
                p["numeroProcesso"]   = num
                p["tribunal"]         = row.get("case:tribunal", "")
                p["classe"]           = row.get("case:classe", "")
                p["assunto_principal"] = row.get("case:assunto_principal", "")
                p["orgao_julgador"]   = row.get("case:orgao_julgador", "")
                p["grau"]             = row.get("case:grau", "")

                # data: pode ser ISO ou vazio
                dt = row.get("case:data_ajuizamento", "").strip()
                p["data_ajuizamento"] = dt if dt else None

                try:
                    p["nivel_sigilo"] = int(row.get("case:nivel_sigilo", 0) or 0)
                except ValueError:
                    p["nivel_sigilo"] = 0

            # Atividade do evento
            atividade = row.get("concept:name", "").strip()
            if atividade:
                p["atividades"].append(atividade)
                p["total_eventos"] += 1

    return dict(processos)


def _bulk_actions(processos: dict[str, dict]):
    for doc in processos.values():
        yield {
            "_index": INDEX,
            "_id":    doc["numeroProcesso"],
            "_source": doc,
        }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Indexa processos judiciais no Elasticsearch.")
    parser.add_argument("--csv",  default=None, help="Caminho do CSV (padrão: último em output/)")
    parser.add_argument("--host", default=ES_URL, help=f"URL do ES (padrão: {ES_URL})")
    parser.add_argument("--reset", action="store_true", help="Apaga e recria o índice antes de indexar")
    args = parser.parse_args()

    csv_path = args.csv or _find_latest_csv()

    es = Elasticsearch(args.host)

    if not es.ping():
        log.error(f"Elasticsearch não responde em {args.host}. Suba com: docker compose up -d")
        sys.exit(1)

    log.info(f"Conectado: {es.info()['version']['number']}")

    # Cria ou recria índice
    if args.reset and es.indices.exists(index=INDEX):
        es.indices.delete(index=INDEX)
        log.info(f"Índice '{INDEX}' removido.")

    if not es.indices.exists(index=INDEX):
        es.indices.create(index=INDEX, body=MAPPING)
        log.info(f"Índice '{INDEX}' criado com mapping.")
    else:
        log.info(f"Índice '{INDEX}' já existe. Use --reset para recriar.")

    # Lê e indexa
    log.info("Lendo CSV e agrupando por processo...")
    processos = _read_csv(csv_path)
    log.info(f"{len(processos)} processos únicos encontrados.")

    ok, errors = helpers.bulk(
        es,
        _bulk_actions(processos),
        chunk_size=500,
        raise_on_error=False,
    )

    log.info(f"Indexados: {ok} documentos")
    if errors:
        log.warning(f"Erros: {len(errors)}")
        for e in errors[:5]:
            log.warning(str(e))

    es.indices.refresh(index=INDEX)
    count = es.count(index=INDEX)["count"]
    log.info(f"Total no índice '{INDEX}': {count} documentos")


if __name__ == "__main__":
    main()
