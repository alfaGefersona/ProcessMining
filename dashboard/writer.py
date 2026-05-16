"""
Geração de dashboard HTML para visualização do event log.

Gera um arquivo .html auto-contido (sem servidor) com:
  - KPI cards (processos, eventos, atividades, duração média)
  - Grafo de Fluxo Direto (DFG) interativo via vis.js
  - Gráfico de top atividades e evolução temporal via Chart.js
  - Histograma de duração dos processos
  - Tabela do event log com busca em tempo real
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime

log = logging.getLogger(__name__)


def _compute_stats(traces: list[dict], label: str) -> dict:
    from xes.writer import format_date

    activity_counts: dict[str, int] = defaultdict(int)
    dfg_counts: dict[tuple, int]    = defaultdict(int)
    start_acts: dict[str, int]      = defaultdict(int)
    end_acts: dict[str, int]        = defaultdict(int)
    events_by_month: dict[str, int] = defaultdict(int)
    case_durations: list[int]       = []
    sample_rows: list[dict]         = []
    sample_headers: list[str]       = []
    seen_hdrs: set[str]             = set()

    for trace in traces:
        events = trace["events"]
        if not events:
            continue

        # Monta dict de atributos do caso (colunas case:*)
        case_row: dict = {}
        for k, (v, t) in trace["attrs"].items():
            col = "case:concept:name" if k == "concept:name" else k
            case_row[col] = format_date(v) if t == "date" else v
            if col not in seen_hdrs:
                seen_hdrs.add(col)
                sample_headers.append(col)

        prev_act = None
        timestamps: list[str] = []
        n_evts = len(events)

        for i, evt in enumerate(events):
            activity = evt.get("concept:name", ("",))[0]
            ts_raw   = evt.get("time:timestamp", ("",))[0]
            ts_iso   = format_date(ts_raw) if ts_raw else ""

            activity_counts[activity] += 1
            if i == 0:
                start_acts[activity] += 1
            if i == n_evts - 1:
                end_acts[activity] += 1
            if prev_act:
                dfg_counts[(prev_act, activity)] += 1
            prev_act = activity

            if ts_iso and len(ts_iso) >= 7:
                events_by_month[ts_iso[:7]] += 1
                timestamps.append(ts_iso)

            if len(sample_rows) < 1000:
                row = dict(case_row)
                for k, (v, t) in evt.items():
                    row[k] = format_date(v) if t == "date" else v
                    if k not in seen_hdrs:
                        seen_hdrs.add(k)
                        sample_headers.append(k)
                sample_rows.append(row)

        if len(timestamps) >= 2:
            try:
                ts_s = sorted(timestamps)
                d1 = datetime.fromisoformat(ts_s[0][:19])
                d2 = datetime.fromisoformat(ts_s[-1][:19])
                case_durations.append((d2 - d1).days)
            except Exception:
                pass

    n_traces      = len(traces)
    n_events_tot  = sum(activity_counts.values())
    avg_dur       = round(sum(case_durations) / len(case_durations), 1) if case_durations else 0

    # ── DFG: top 25 atividades ────────────────────────────────────────────────
    sorted_acts = sorted(activity_counts.items(), key=lambda x: -x[1])
    top_25_set  = {a for a, _ in sorted_acts[:25]}
    max_count   = sorted_acts[0][1] if sorted_acts else 1
    max_edge    = max(dfg_counts.values(), default=1)

    dfg_nodes = []
    for act, cnt in activity_counts.items():
        if act not in top_25_set:
            continue
        ratio = cnt / max_count
        # Cor: #e2e8f0 (baixa freq) → #2E4057 (alta freq)
        r = round(226 - (226 - 46)  * ratio)
        g = round(232 - (232 - 64)  * ratio)
        b = round(240 - (240 - 87)  * ratio)
        color      = f"#{r:02x}{g:02x}{b:02x}"
        font_color = "#ffffff" if ratio > 0.45 else "#1e293b"
        size       = round(18 + ratio * 42)  # 18 → 60
        dfg_nodes.append({
            "id":    act,
            "label": f"{act}\n({cnt:,})",
            "title": f"<b>{act}</b><br>{cnt:,} ocorrências",
            "color": {"background": color, "border": "#2E4057",
                      "highlight": {"background": "#4361ee", "border": "#2E4057"}},
            "font":  {"color": font_color, "size": 12},
            "size":  size,
        })

    dfg_nodes += [
        {"id": "__START__", "label": "▶ START", "shape": "ellipse",
         "color": {"background": "#2dc653", "border": "#1a7f37",
                   "highlight": {"background": "#22c55e", "border": "#1a7f37"}},
         "font": {"color": "#fff", "size": 13}, "size": 22},
        {"id": "__END__",   "label": "■ END",   "shape": "ellipse",
         "color": {"background": "#e63946", "border": "#9b1c1c",
                   "highlight": {"background": "#ef4444", "border": "#9b1c1c"}},
         "font": {"color": "#fff", "size": 13}, "size": 22},
    ]

    dfg_edges = []
    for (src, dst), cnt in dfg_counts.items():
        if src not in top_25_set or dst not in top_25_set:
            continue
        w = max(1, round(cnt / max_edge * 7))
        dfg_edges.append({
            "from": src, "to": dst,
            "value": cnt,
            "width": w,
            "label": str(cnt),
            "title": f"{src} → {dst}: {cnt:,}×",
            "color": {"color": "#94a3b8", "highlight": "#4361ee"},
            "font":  {"size": 9, "color": "#475569", "align": "middle"},
            "smooth": {"type": "curvedCW", "roundness": 0.15},
        })
    for act, cnt in start_acts.items():
        if act not in top_25_set:
            continue
        dfg_edges.append({
            "from": "__START__", "to": act, "value": cnt,
            "width": max(1, round(cnt / max_edge * 7)),
            "label": str(cnt), "title": f"START → {act}: {cnt:,}×",
            "color": {"color": "#4ade80"}, "font": {"size": 9},
            "smooth": {"type": "curvedCW", "roundness": 0.15},
        })
    for act, cnt in end_acts.items():
        if act not in top_25_set:
            continue
        dfg_edges.append({
            "from": act, "to": "__END__", "value": cnt,
            "width": max(1, round(cnt / max_edge * 7)),
            "label": str(cnt), "title": f"{act} → END: {cnt:,}×",
            "color": {"color": "#f87171"}, "font": {"size": 9},
            "smooth": {"type": "curvedCW", "roundness": 0.15},
        })

    # ── Histograma de duração (buckets de 30 dias) ────────────────────────────
    dur_hist: dict[int, int] = defaultdict(int)
    for d in case_durations:
        dur_hist[(d // 30) * 30] += 1

    return {
        "label":          label,
        "generated_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "n_traces":       n_traces,
        "n_events":       n_events_tot,
        "n_activities":   len(activity_counts),
        "avg_duration":   avg_dur,
        "top_activities": [[a, c] for a, c in sorted_acts[:20]],
        "events_by_month":[[k, v] for k, v in sorted(events_by_month.items())],
        "dur_histogram":  [[k, v] for k, v in sorted(dur_hist.items())],
        "dfg_nodes":      dfg_nodes,
        "dfg_edges":      dfg_edges,
        "max_edge_val":   max_edge,
        "sample_headers": sample_headers,
        "sample_rows":    sample_rows,
    }


# ── Template HTML ─────────────────────────────────────────────────────────────

_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ProcessMining — __LABEL__</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/dist/vis-network.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/dist/dist/vis-network.min.css">
<style>
:root{
  --primary:#2E4057; --accent:#4361ee; --success:#16a34a; --danger:#dc2626;
  --warn:#d97706; --bg:#f1f5f9; --card:#fff; --text:#1e293b;
  --muted:#64748b; --border:#e2e8f0;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);font-size:14px}

/* ── Navbar ── */
.nav{background:var(--primary);color:#fff;padding:12px 28px;display:flex;
  align-items:center;justify-content:space-between;position:sticky;top:0;z-index:200;
  box-shadow:0 2px 8px rgba(0,0,0,.25)}
.nav h1{font-size:17px;font-weight:600;letter-spacing:.3px}
.nav .meta{font-size:12px;opacity:.65}

/* ── Layout ── */
.wrap{max-width:1440px;margin:0 auto;padding:24px}
.section{background:var(--card);border-radius:10px;padding:20px;
  box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:24px}
.sec-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.sec-title{font-size:15px;font-weight:600;color:var(--primary)}

/* ── KPI row ── */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.kpi{background:var(--card);border-radius:10px;padding:18px 20px;
  box-shadow:0 1px 4px rgba(0,0,0,.08);border-left:4px solid var(--accent)}
.kpi:nth-child(2){border-left-color:var(--success)}
.kpi:nth-child(3){border-left-color:var(--warn)}
.kpi:nth-child(4){border-left-color:var(--danger)}
.kpi-lbl{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);margin-bottom:5px}
.kpi-val{font-size:30px;font-weight:700;line-height:1}
.kpi-sub{font-size:11px;color:var(--muted);margin-top:4px}

/* ── DFG ── */
.dfg-ctrl{display:flex;gap:10px;align-items:center;flex-wrap:wrap;
  padding:10px 14px;background:#f8fafc;border-radius:8px;margin-bottom:12px}
.dfg-ctrl label{font-size:12px;color:var(--muted)}
.dfg-ctrl input[type=range]{width:140px;accent-color:var(--accent)}
.btn{padding:5px 13px;border:none;border-radius:6px;cursor:pointer;
  font-size:12px;font-weight:500;transition:opacity .15s}
.btn-pri{background:var(--accent);color:#fff}
.btn-out{background:#fff;color:var(--text);border:1px solid var(--border)}
.btn:hover{opacity:.8}
#dfg{height:520px;border:1px solid var(--border);border-radius:8px;background:#fafafa}
.dfg-legend{display:flex;gap:14px;font-size:11px;color:var(--muted);
  margin-top:8px;align-items:center}
.legend-dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:4px}

/* ── Charts ── */
.charts2{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px}
.chart-box{position:relative;height:280px}

/* ── Table ── */
.tbl-ctrl{display:flex;gap:10px;margin-bottom:10px}
.srch{flex:1;padding:7px 12px;border:1px solid var(--border);border-radius:6px;
  font-size:13px;outline:none}
.srch:focus{border-color:var(--accent)}
.tbl-info{font-size:12px;color:var(--muted);margin-bottom:6px}
.tbl-wrap{overflow:auto;max-height:420px}
table{width:100%;border-collapse:collapse;font-size:12px}
thead th{background:var(--primary);color:#fff;padding:7px 10px;text-align:left;
  position:sticky;top:0;white-space:nowrap;cursor:pointer;user-select:none}
thead th:hover{background:#3d5470}
thead th.sort-asc::after{content:" ▲"}
thead th.sort-desc::after{content:" ▼"}
tbody tr:nth-child(even){background:#f8fafc}
tbody tr:hover{background:#eff6ff}
td{padding:5px 10px;border-bottom:1px solid #f1f5f9;white-space:nowrap;
  max-width:220px;overflow:hidden;text-overflow:ellipsis}

@media(max-width:900px){
  .kpis{grid-template-columns:1fr 1fr}
  .charts2{grid-template-columns:1fr}
}
</style>
</head>
<body>

<nav class="nav">
  <h1 id="nav-title">ProcessMining Dashboard</h1>
  <span class="meta" id="nav-meta"></span>
</nav>

<div class="wrap">

  <!-- KPIs -->
  <div class="kpis">
    <div class="kpi">
      <div class="kpi-lbl">Processos (casos)</div>
      <div class="kpi-val" id="kpi-t">—</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">Eventos</div>
      <div class="kpi-val" id="kpi-e">—</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">Atividades únicas</div>
      <div class="kpi-val" id="kpi-a">—</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">Duração média</div>
      <div class="kpi-val" id="kpi-d">—</div>
      <div class="kpi-sub">dias por processo</div>
    </div>
  </div>

  <!-- DFG -->
  <div class="section">
    <div class="sec-hdr">
      <span class="sec-title">Grafo de Fluxo Direto (DFG)</span>
      <span style="font-size:12px;color:var(--muted)" id="dfg-info"></span>
    </div>
    <div class="dfg-ctrl">
      <label>Min. freq. aresta: <strong id="thresh-lbl">1</strong></label>
      <input type="range" id="thresh" min="1" value="1" step="1">
      <button class="btn btn-out" id="btn-fit">⊞ Ajustar tela</button>
      <button class="btn btn-out" id="btn-phy">⚙ Física: ON</button>
      <button class="btn btn-out" id="btn-lay">↕ Layout: Livre</button>
    </div>
    <div id="dfg"></div>
    <div class="dfg-legend">
      <span><span class="legend-dot" style="background:#e2e8f0;border:1px solid #94a3b8"></span>baixa freq.</span>
      <span><span class="legend-dot" style="background:#2E4057"></span>alta freq.</span>
      <span><span class="legend-dot" style="background:#2dc653"></span>START</span>
      <span><span class="legend-dot" style="background:#e63946"></span>END</span>
      <span style="margin-left:8px">Arraste nós · Scroll para zoom · Duplo clique para fixar</span>
    </div>
  </div>

  <!-- Charts row -->
  <div class="charts2">
    <div class="section">
      <div class="sec-hdr"><span class="sec-title">Top Atividades</span></div>
      <div class="chart-box"><canvas id="ch-acts"></canvas></div>
    </div>
    <div class="section">
      <div class="sec-hdr"><span class="sec-title">Eventos por Mês</span></div>
      <div class="chart-box"><canvas id="ch-time"></canvas></div>
    </div>
  </div>

  <!-- Duration histogram -->
  <div class="section" id="sec-dur">
    <div class="sec-hdr">
      <span class="sec-title">Distribuição de Duração dos Processos</span>
      <span style="font-size:12px;color:var(--muted)" id="dur-info"></span>
    </div>
    <div class="chart-box" style="height:200px"><canvas id="ch-dur"></canvas></div>
  </div>

  <!-- Event log table -->
  <div class="section">
    <div class="sec-hdr">
      <span class="sec-title">Event Log</span>
      <span style="font-size:12px;color:var(--muted)" id="tbl-cap"></span>
    </div>
    <div class="tbl-ctrl">
      <input class="srch" id="srch" placeholder="Buscar em qualquer coluna..." type="search">
    </div>
    <div class="tbl-info" id="tbl-info"></div>
    <div class="tbl-wrap">
      <table>
        <thead id="thead"></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>

</div><!-- /wrap -->

<script>
const D = __DATA__;
const fmt = n => n.toLocaleString('pt-BR');

// ── KPIs ────────────────────────────────────────────────────────────────────
document.getElementById('nav-title').textContent = `ProcessMining — ${D.label}`;
document.getElementById('nav-meta').textContent  = `Gerado em ${D.generated_at}`;
document.getElementById('kpi-t').textContent = fmt(D.n_traces);
document.getElementById('kpi-e').textContent = fmt(D.n_events);
document.getElementById('kpi-a').textContent = fmt(D.n_activities);
document.getElementById('kpi-d').textContent = D.avg_duration > 0 ? fmt(D.avg_duration) : '—';

// ── DFG ─────────────────────────────────────────────────────────────────────
const allNodes = D.dfg_nodes;
const allEdges = D.dfg_edges;
const maxEdge  = D.max_edge_val || 1;

const nodesDS = new vis.DataSet([]);
const edgesDS = new vis.DataSet([]);

const visOpts = {
  physics:{
    enabled:true,
    solver:'forceAtlas2Based',
    forceAtlas2Based:{gravitationalConstant:-80,centralGravity:.01,
      springLength:220,springConstant:.05,damping:.4},
    stabilization:{iterations:250,updateInterval:20},
  },
  edges:{
    arrows:'to',
    smooth:{type:'curvedCW',roundness:.12},
    font:{size:9,align:'middle'},
  },
  nodes:{
    shape:'box',
    borderWidth:1,
    borderWidthSelected:2,
    font:{multi:false},
  },
  interaction:{hover:true,tooltipDelay:150,navigationButtons:false,keyboard:true},
  configure:{enabled:false},
};

const network = new vis.Network(
  document.getElementById('dfg'),
  {nodes:nodesDS, edges:edgesDS},
  visOpts
);

const slider = document.getElementById('thresh');
slider.max   = Math.max(1, maxEdge);

function refreshDFG(){
  const min = +slider.value;
  document.getElementById('thresh-lbl').textContent = fmt(min);

  const filtEdges = allEdges.filter(e => (e.value||0) >= min);
  const connected = new Set(['__START__','__END__']);
  filtEdges.forEach(e=>{ connected.add(e.from); connected.add(e.to); });
  const filtNodes = allNodes.filter(n => connected.has(n.id));

  nodesDS.clear(); edgesDS.clear();
  nodesDS.add(filtNodes);
  edgesDS.add(filtEdges);

  const acts = filtNodes.filter(n=>!n.id.startsWith('__')).length;
  document.getElementById('dfg-info').textContent =
    `${acts} atividades · ${filtEdges.length} transições`;
}

slider.addEventListener('input', refreshDFG);
refreshDFG();

document.getElementById('btn-fit').onclick = () => network.fit({animation:{duration:400}});

let phyOn = true;
document.getElementById('btn-phy').onclick = function(){
  phyOn = !phyOn;
  network.setOptions({physics:{enabled:phyOn}});
  this.textContent = `⚙ Física: ${phyOn?'ON':'OFF'}`;
};

let hierOn = false;
document.getElementById('btn-lay').onclick = function(){
  hierOn = !hierOn;
  if(hierOn){
    network.setOptions({
      layout:{hierarchical:{enabled:true,direction:'LR',sortMethod:'directed',
        levelSeparation:220,nodeSpacing:110}},
      physics:{enabled:false}
    });
    phyOn = false;
    document.getElementById('btn-phy').textContent = '⚙ Física: OFF';
    this.textContent = '↕ Layout: Hierárquico';
  } else {
    network.setOptions({
      layout:{hierarchical:{enabled:false}},
      physics:{enabled:true}
    });
    phyOn = true;
    document.getElementById('btn-phy').textContent = '⚙ Física: ON';
    this.textContent = '↕ Layout: Livre';
  }
  refreshDFG();
};

// ── Chart: Top Atividades ────────────────────────────────────────────────────
{
  const acts = D.top_activities.slice(0,15);
  new Chart(document.getElementById('ch-acts'),{
    type:'bar',
    data:{
      labels: acts.map(([a])=>a.length>38?a.slice(0,38)+'…':a),
      datasets:[{data:acts.map(([,c])=>c),
        backgroundColor:'#4361ee',borderRadius:3,barThickness:14}]
    },
    options:{
      indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{
        label:ctx=>' '+fmt(ctx.parsed.x)+' eventos'
      }}},
      scales:{x:{beginAtZero:true,ticks:{font:{size:11}}},
              y:{ticks:{font:{size:11}}}},
    }
  });
}

// ── Chart: Eventos por Mês ───────────────────────────────────────────────────
{
  const months = D.events_by_month;
  new Chart(document.getElementById('ch-time'),{
    type:'line',
    data:{
      labels: months.map(([m])=>m),
      datasets:[{data:months.map(([,v])=>v),
        borderColor:'#4361ee',backgroundColor:'rgba(67,97,238,.12)',
        fill:true,tension:.35,pointRadius:3,pointHoverRadius:5}]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{
        label:ctx=>' '+fmt(ctx.parsed.y)+' eventos'
      }}},
      scales:{y:{beginAtZero:true,ticks:{font:{size:11}}},
              x:{ticks:{font:{size:11},maxRotation:45}}},
    }
  });
}

// ── Chart: Duração ───────────────────────────────────────────────────────────
{
  const hist = D.dur_histogram;
  if(hist.length > 0){
    const total = hist.reduce((s,[,v])=>s+v,0);
    document.getElementById('dur-info').textContent =
      `${fmt(total)} processos com duração registrada`;
    new Chart(document.getElementById('ch-dur'),{
      type:'bar',
      data:{
        labels: hist.map(([d])=>`${d}–${d+29} dias`),
        datasets:[{data:hist.map(([,v])=>v),
          backgroundColor:'#f59e0b',borderRadius:3}]
      },
      options:{
        responsive:true,maintainAspectRatio:false,
        plugins:{legend:{display:false},tooltip:{callbacks:{
          label:ctx=>' '+fmt(ctx.parsed.y)+' processos'
        }}},
        scales:{y:{beginAtZero:true,ticks:{font:{size:11}}},
                x:{ticks:{font:{size:11},maxRotation:45}}},
      }
    });
  } else {
    document.getElementById('sec-dur').style.display='none';
  }
}

// ── Event Log Table ──────────────────────────────────────────────────────────
{
  const hdrs = D.sample_headers;
  const rows = D.sample_rows;

  document.getElementById('tbl-cap').textContent =
    rows.length >= 1000 ? '(primeiras 1 000 linhas)' : '';

  // Header
  const thead = document.getElementById('thead');
  const htr   = document.createElement('tr');
  hdrs.forEach((h,i) => {
    const th = document.createElement('th');
    th.textContent = h;
    th.dataset.col = i;
    th.dataset.dir = '0';
    th.onclick = function(){
      const dir = this.dataset.dir === '1' ? -1 : 1;
      this.dataset.dir = dir === 1 ? '1' : '-1';
      thead.querySelectorAll('th').forEach(t=>{
        t.classList.remove('sort-asc','sort-desc');
      });
      this.classList.add(dir===1?'sort-asc':'sort-desc');
      const col = h;
      const sorted = [...current].sort((a,b)=>{
        const va = String(a[col]||''), vb = String(b[col]||'');
        return dir * va.localeCompare(vb, 'pt-BR', {numeric:true});
      });
      renderRows(sorted);
    };
    htr.appendChild(th);
  });
  thead.appendChild(htr);

  let current = rows;

  function renderRows(data){
    const tbody = document.getElementById('tbody');
    tbody.innerHTML = '';
    const slice = data.slice(0,500);
    const frag  = document.createDocumentFragment();
    slice.forEach(row => {
      const tr = document.createElement('tr');
      hdrs.forEach(h => {
        const td = document.createElement('td');
        const v  = row[h] !== undefined ? String(row[h]) : '';
        td.textContent = v;
        td.title = v;
        tr.appendChild(td);
      });
      frag.appendChild(tr);
    });
    tbody.appendChild(frag);
    document.getElementById('tbl-info').textContent =
      `Exibindo ${fmt(Math.min(data.length,500))} de ${fmt(data.length)} linhas`;
  }

  renderRows(rows);

  document.getElementById('srch').addEventListener('input', function(){
    const q = this.value.toLowerCase().trim();
    if(!q){ current = rows; renderRows(rows); return; }
    current = rows.filter(row => hdrs.some(h => String(row[h]||'').toLowerCase().includes(q)));
    renderRows(current);
  });
}
</script>
</body>
</html>
"""


def write_html(traces: list[dict], output_path: str, label: str) -> tuple[int, int]:
    """
    Gera dashboard HTML auto-contido com visualizações do event log.

    Args:
        traces:      lista de dicts {'attrs': ..., 'events': [...]}
        output_path: caminho completo do arquivo .html de saída
        label:       rótulo do tribunal (ex: "TJPR")

    Returns:
        (n_traces, n_events)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    stats     = _compute_stats(traces, label)
    data_json = json.dumps(stats, ensure_ascii=False, default=str)
    html      = _HTML.replace("__DATA__", data_json).replace("__LABEL__", label)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    log.info(f"HTML salvo: {output_path}  ({stats['n_traces']} traces | {stats['n_events']} eventos)")
    return stats["n_traces"], stats["n_events"]
