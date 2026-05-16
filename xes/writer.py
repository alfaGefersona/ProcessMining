"""
Camada de geração XES: serializa traces no formato IEEE XES 1.0.

Conformidade:
  ✓ Extensões declaradas: concept, time, lifecycle, org
  ✓ <global scope="trace"> e <global scope="event"> com atributos default
  ✓ <classifier> para atividade e recurso
  ✓ Timestamps em ISO 8601 com timezone
  ✓ Suporte ao formato de data Datajud: "20210407140205" (YYYYMMDDHHmmss)
"""

import os
import logging
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from xml.dom import minidom

log = logging.getLogger(__name__)

XES_NS   = "http://www.xes-standard.org/"
XES_EXTS = {
    "concept":   ("Concept",    "http://www.xes-standard.org/concept.xesext"),
    "time":      ("Time",       "http://www.xes-standard.org/time.xesext"),
    "lifecycle": ("Lifecycle",  "http://www.xes-standard.org/lifecycle.xesext"),
    "org":       ("Org",        "http://www.xes-standard.org/org.xesext"),
}

_INVALID = "__INVALID__"

# Ordem de prioridade dos atributos dentro de um evento (legibilidade e conformidade)
_EVENT_ATTR_ORDER = ["concept:name", "time:timestamp", "lifecycle:transition", "org:resource"]


def format_date(val) -> str:
    """
    Normaliza qualquer representação de data para ISO 8601 com timezone.
    Formatos suportados:
      "20210407140205"        → Datajud (YYYYMMDDHHmmss, 14 dígitos)
      "2021-04-07T14:02:05Z" → ISO com Z
      "2021-04-07"           → YYYY-MM-DD
    """
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    s = str(val).strip()
    if len(s) == 14 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}T{s[8:10]}:{s[10:12]}:{s[12:14]}+00:00"
    if len(s) == 10 and s[4] == "-":
        return f"{s}T00:00:00+00:00"
    if "T" in s and "+" not in s and "Z" not in s:
        return f"{s}+00:00"
    return s.replace("Z", "+00:00")


def _add_attr(parent: ET.Element, xes_key: str, value, xes_type: str):
    """Adiciona um atributo XES tipado ao elemento pai."""
    str_val = format_date(value) if xes_type == "date" else str(value)
    ET.SubElement(parent, xes_type, key=xes_key, value=str_val)


def _build_log_element(label: str) -> ET.Element:
    """
    Cria o elemento raiz <log> com extensões, globais e classificadores.
    """
    ET.register_namespace("", XES_NS)
    log_el = ET.Element("log", {
        "xmlns":         XES_NS,
        "xes.version":   "1.0",
        "xes.features":  "nested-attributes",
    })

    # Extensões
    for prefix, (name, uri) in XES_EXTS.items():
        ext = ET.SubElement(log_el, "extension")
        ext.set("name",   name)
        ext.set("prefix", prefix)
        ext.set("uri",    uri)

    # Globais de trace
    g_trace = ET.SubElement(log_el, "global", scope="trace")
    ET.SubElement(g_trace, "string", key="concept:name", value=_INVALID)

    # Globais de evento
    g_event = ET.SubElement(log_el, "global", scope="event")
    ET.SubElement(g_event, "string", key="concept:name",         value=_INVALID)
    ET.SubElement(g_event, "date",   key="time:timestamp",       value="1970-01-01T00:00:00+00:00")
    ET.SubElement(g_event, "string", key="lifecycle:transition", value="complete")
    ET.SubElement(g_event, "string", key="org:resource",         value=_INVALID)

    # Classificadores
    ET.SubElement(log_el, "classifier", name="Activity classifier", keys="concept:name")
    ET.SubElement(log_el, "classifier", name="Resource classifier", keys="org:resource")

    # Metadado do log
    ET.SubElement(log_el, "string",
                  key="concept:name",
                  value=f"Datajud - {label} - {datetime.now().date()}")

    return log_el


def write_xes(traces_gen, output_path: str, label: str) -> tuple[int, int]:
    """
    Consome o gerador de traces e escreve o arquivo .xes em disco.

    Args:
        traces_gen:  gerador de dicts {'attrs': ..., 'events': [...]}
        output_path: caminho completo do arquivo de saída
        label:       rótulo do log (ex: "TJPR") usado no metadado

    Returns:
        (n_traces, n_events)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    log_el   = _build_log_element(label)
    n_traces = 0
    n_events = 0

    for trace_data in traces_gen:
        trace_el = ET.SubElement(log_el, "trace")

        # concept:name sempre primeiro no trace
        sorted_attrs = sorted(
            trace_data["attrs"].items(),
            key=lambda kv: (0 if kv[0] == "concept:name" else 1)
        )
        for xes_key, (value, xes_type) in sorted_attrs:
            _add_attr(trace_el, xes_key, value, xes_type)

        # Eventos com atributos obrigatórios na frente
        for evt_data in trace_data["events"]:
            evt_el = ET.SubElement(trace_el, "event")
            sorted_evt = sorted(
                evt_data.items(),
                key=lambda kv: (
                    _EVENT_ATTR_ORDER.index(kv[0])
                    if kv[0] in _EVENT_ATTR_ORDER
                    else len(_EVENT_ATTR_ORDER)
                )
            )
            for xes_key, (value, xes_type) in sorted_evt:
                _add_attr(evt_el, xes_key, value, xes_type)
            n_events += 1

        n_traces += 1

    raw    = ET.tostring(log_el, encoding="unicode", xml_declaration=False)
    pretty = minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8")

    with open(output_path, "wb") as f:
        f.write(pretty)

    log.info(f"XES salvo: {output_path}  ({n_traces} traces | {n_events} eventos)")
    return n_traces, n_events
