"""
Camada de transformação: converte hits crus da API Datajud em traces
estruturados e prontos para serialização XES.

Responsabilidades:
  - Navegar o JSON aninhado com segurança
  - Montar nomes de atividade com granularidade máxima (nome + complemento)
  - Injetar atributos obrigatórios IEEE XES (lifecycle, org:resource)
  - Ordenar e deduplicar eventos dentro de cada trace
"""

import logging

from datajud.config import CAMPOS_TRACE, CAMPOS_EVENTO_EXTRAS

log = logging.getLogger(__name__)


def get_nested(obj, path):
    """
    Navega um caminho aninhado de forma segura.
    Suporta chaves string e índices inteiros de lista.
    Exemplos de path: ["classe", "nome"] | ["assuntos", 0, "nome"]
    """
    for key in path:
        if obj is None:
            return None
        if isinstance(key, int):
            obj = obj[key] if isinstance(obj, list) and len(obj) > key else None
        else:
            obj = obj.get(key) if isinstance(obj, dict) else None
    return obj


def build_activity_name(mov: dict) -> str:
    """
    Monta o nome da atividade com granularidade máxima:
      "Nome do Movimento - Complemento Principal"

    O complemento é adicionado apenas quando presente, tornando atividades
    genéricas (ex: "Juntada de Petição") mais informativas para análise PM.
    """
    nome = (mov.get("nome") or "").strip()
    complemento = get_nested(mov, ["complementosTabelados", 0, "nome"])
    if complemento:
        return f"{nome} - {str(complemento).strip()}"
    return nome


def _dedup_events(events: list) -> list:
    """
    Remove eventos duplicados dentro de um mesmo trace.
    Critério: mesmo código TPU + mesmo timestamp → mantém só o primeiro.
    Eventos sem código são deduplicados por nome + timestamp.
    """
    seen   = set()
    result = []
    for evt in events:
        codigo    = evt.get("_codigo_interno")
        timestamp = evt.get("time:timestamp", ("", "date"))[0]
        nome      = evt.get("concept:name",   ("", "string"))[0]
        key = (codigo, timestamp) if codigo is not None else (nome, timestamp)
        if key not in seen:
            seen.add(key)
            result.append(evt)
    return result


def hit_to_trace(hit: dict, tribunal_nome: str) -> dict | None:
    """
    Converte um hit cru da API em um dict com:
      - 'attrs'  : atributos do trace (nível processo) — (valor, tipo_xes)
      - 'events' : lista de dicts de atributos de evento — (valor, tipo_xes)

    Retorna None se o processo não tiver movimentos válidos.
    """
    source     = hit.get("_source", {})
    movimentos = source.get("movimentos", [])

    if not movimentos:
        return None

    # ── Atributos do trace ────────────────────────────────────────────────────
    attrs = {}
    for xes_key, path, xes_type in CAMPOS_TRACE:
        val = get_nested(source, path)
        if val is not None:
            attrs[xes_key] = (val, xes_type)

    attrs.setdefault("case:tribunal", (tribunal_nome, "string"))

    # Órgão julgador do processo como fallback para movimentos sem recurso próprio
    orgao_processo = get_nested(source, ["orgaoJulgador", "nome"]) or tribunal_nome

    # ── Eventos (movimentos) ──────────────────────────────────────────────────
    events = []
    for mov in movimentos:
        timestamp = mov.get("dataHora")
        if not timestamp:
            continue

        activity = build_activity_name(mov)
        if not activity:
            continue

        # Cada movimento tem seu próprio orgaoJulgador; usa o do processo como fallback
        recurso = get_nested(mov, ["orgaoJulgador", "nome"]) or orgao_processo

        evt = {
            # Obrigatórios IEEE XES
            "concept:name":         (activity,   "string"),
            "time:timestamp":       (timestamp,  "date"),
            "lifecycle:transition": ("complete", "string"),
            "org:resource":         (recurso,    "string"),
            # Controle interno — removido antes de serializar
            "_codigo_interno": mov.get("codigo"),
        }

        for xes_key, path, xes_type in CAMPOS_EVENTO_EXTRAS:
            val = get_nested(mov, path)
            if val is not None:
                evt[xes_key] = (val, xes_type)

        events.append(evt)

    if not events:
        return None

    events.sort(key=lambda e: e.get("time:timestamp", ("", "date"))[0])
    events = _dedup_events(events)

    for evt in events:
        evt.pop("_codigo_interno", None)

    return {"attrs": attrs, "events": events}


def hits_to_traces(hits_gen, tribunal_nome: str):
    """Gerador: converte hits em traces prontos para o XES."""
    skipped = 0
    for hit in hits_gen:
        trace = hit_to_trace(hit, tribunal_nome)
        if trace:
            yield trace
        else:
            skipped += 1
    if skipped:
        log.info(f"[{tribunal_nome}] {skipped} processo(s) descartados (sem movimentos válidos).")
