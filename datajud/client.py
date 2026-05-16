"""
Camada de busca: comunica com a API pública do Datajud (Elasticsearch).
Responsável por autenticação, paginação via search_after, retry com backoff
e sinalização de interrupção para permitir salvamento parcial.
"""

import time
import logging
import requests

from datajud.config import (
    API_KEY, BASE_URL, PAGE_SIZE, REQUEST_DELAY_SEC,
    MAX_PROCESSOS, QUERY_BODY, REQUEST_TIMEOUT, MAX_RETRIES,
)

log = logging.getLogger(__name__)

# Backoff entre tentativas (segundos): 5s → 15s → 45s
RETRY_BACKOFF = [5, 15, 45]


def _headers() -> dict:
    return {
        "Authorization": f"APIKey {API_KEY}",
        "Content-Type":  "application/json",
    }


def _fetch_page_with_retry(alias: str, search_after, pagina: int, tribunal_nome: str) -> dict | None:
    """
    Tenta buscar uma página até MAX_RETRIES vezes com backoff exponencial.
    Retorna None se todas as tentativas falharem.
    """
    url  = f"{BASE_URL}/{alias}/_search"
    body = {**QUERY_BODY, "size": PAGE_SIZE}
    if search_after:
        body["search_after"] = search_after

    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, headers=_headers(), json=body, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()

        except requests.Timeout:
            espera = RETRY_BACKOFF[tentativa - 1] if tentativa <= len(RETRY_BACKOFF) else RETRY_BACKOFF[-1]
            log.warning(
                f"[{tribunal_nome}] Timeout na página {pagina} "
                f"(tentativa {tentativa}/{MAX_RETRIES}). Aguardando {espera}s ..."
            )
            if tentativa < MAX_RETRIES:
                time.sleep(espera)

        except requests.HTTPError as e:
            log.error(f"[{tribunal_nome}] HTTP {e.response.status_code} na página {pagina}: {e}")
            return None  # erro HTTP não é transitório — não tenta novamente

        except requests.RequestException as e:
            log.error(f"[{tribunal_nome}] Erro de rede na página {pagina}: {e}")
            return None

    log.error(f"[{tribunal_nome}] Página {pagina} falhou após {MAX_RETRIES} tentativas. "
              f"Salvando o que foi extraído até aqui.")
    return None


def fetch_all_hits(alias: str, tribunal_nome: str):
    """
    Gerador que itera todas as páginas do tribunal via search_after.
    Produz hits crus da API um a um.

    Em caso de falha irrecuperável, encerra o gerador normalmente para que
    os dados já produzidos possam ser salvos (sem perder o progresso).
    """
    log.info(f"[{tribunal_nome}] Iniciando extração ...")
    search_after   = None
    total_extraido = 0
    pagina         = 0

    while True:
        pagina += 1
        data = _fetch_page_with_retry(alias, search_after, pagina, tribunal_nome)

        if data is None:
            # Falha irrecuperável — encerra mas não levanta exceção para preservar dados já coletados
            break

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            log.info(f"[{tribunal_nome}] Extração concluída após {pagina - 1} página(s).")
            break

        total_disponivel = data.get("hits", {}).get("total", {}).get("value", "?")
        log.info(f"[{tribunal_nome}] Página {pagina} — {len(hits)} hits "
                 f"(total estimado: {total_disponivel})")

        for hit in hits:
            yield hit
            total_extraido += 1
            if MAX_PROCESSOS and total_extraido >= MAX_PROCESSOS:
                log.info(f"[{tribunal_nome}] Limite de {MAX_PROCESSOS} processos atingido.")
                log.info(f"[{tribunal_nome}] Total extraído: {total_extraido} processos.")
                return

        search_after = hits[-1].get("sort")
        if not search_after:
            break

        time.sleep(REQUEST_DELAY_SEC)

    log.info(f"[{tribunal_nome}] Total extraído: {total_extraido} processos.")
