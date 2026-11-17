#!/usr/bin/env python3
"""SecondBrain — interface nativa (GTK4 + libadwaita + WebKitGTK) sobre a memória cruzada (xmem).

Lê o MESMO índice que o Claude usa. Somente leitura sobre os seus arquivos: nada é gravado nos vaults.
Páginas: Notas (busca híbrida + leitor), Grafo (todas as notas e relações), Pendências (itens parados).
"""
import html
import json
import os
import re
import sys
import threading
import urllib.parse

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gio, GLib, Gtk, Pango, WebKit  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (os.path.join(HERE, "..", "scripts"), os.path.expanduser("~/.local/share/secondbrain/bin")):
    if os.path.isfile(os.path.join(cand, "xmem.py")):
        sys.path.insert(0, cand)
        break
import xmem  # noqa: E402

APP_ID = "io.github.eltobsjr.SecondBrain"
PALETTE = ["#8aadf4", "#a6da95", "#f5a97f", "#c6a0f6", "#eed49f", "#8bd5ca", "#ed8796", "#f5bde6", "#91d7e3", "#b7bdf8", "#f0c6c6", "#7dc4e4"]


def md_to_html(body, wikimap):
    """Markdown -> HTML seguro: HTML cru é escapado antes; wikilinks viram sb://note/<id>."""
    body = body.replace("<", "&lt;")

    def wl(m):
        target = m.group(1)
        label = (m.group(2) or target.split("|")[0]).strip()
        key = os.path.basename(target.split("|")[0].split("#")[0].strip().lower())
        key = key[:-3] if key.endswith(".md") else key
        nid = wikimap.get(key)
        return f"[{label}](sb://note/{nid})" if nid else f"*{label}*"

    body = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", wl, body)
    try:
        import markdown
        return markdown.markdown(body, extensions=["tables", "fenced_code", "sane_lists", "nl2br"])
    except Exception:
        return "<pre>" + html.escape(body) + "</pre>"


READER_CSS = """
:root{color-scheme:light dark;--fg:#2e3440;--mut:#6b7385;--bg:#fff;--card:#f3f4f8;--ac:#4a6fd8;--bd:#dde1ea}
.dark{--fg:#cad3f5;--mut:#939ab7;--bg:#24273a;--card:#1e2030;--ac:#8aadf4;--bd:#363a4f}
body{font:15px/1.6 system-ui,sans-serif;color:var(--fg);background:var(--bg);margin:0;padding:22px 28px;max-width:860px}
h1{font-size:1.5em;margin:.2em 0 .4em}h2{font-size:1.2em;margin-top:1.4em;border-bottom:1px solid var(--bd);padding-bottom:.2em}
a{color:var(--ac);text-decoration:none}a:hover{text-decoration:underline}
code{background:var(--card);padding:.1em .35em;border-radius:5px;font-size:.92em}pre{background:var(--card);padding:12px;border-radius:10px;overflow:auto}pre code{background:none;padding:0}
table{border-collapse:collapse}td,th{border:1px solid var(--bd);padding:4px 9px}blockquote{margin:0;padding-left:14px;border-left:3px solid var(--bd);color:var(--mut)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 14px}.chip{background:var(--card);border:1px solid var(--bd);border-radius:999px;padding:1px 10px;font-size:12px;color:var(--mut)}
.chip.lock{color:#d98a1c;border-color:#d98a1c}.path{font-size:12px;color:var(--mut);word-break:break-all}
.side{margin-top:26px;border-top:1px solid var(--bd);padding-top:10px}.side h3{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
.side li{margin:3px 0}.inact{opacity:.5;text-decoration:line-through}.tag{font-size:11px;color:var(--mut)}
"""


def reader_html(d, dark, wikimap):
    n = d["note"]
    chips = [f'<span class="chip">{html.escape(n["project"])}</span>', f'<span class="chip">{html.escape(n["tipo"] or n["kind"])}</span>']
    if n["data"]:
        chips.append(f'<span class="chip">{html.escape(n["data"])}</span>')
    if n["status"]:
        chips.append(f'<span class="chip">{html.escape(n["status"])}</span>')
    if n["sens"] == "alta":
        chips.append('<span class="chip lock">🔒 sensibilidade alta</span>')
    if n["inactive"]:
        chips.append('<span class="chip">inativa (substituída)</span>')

    def li(e):
        cls = ' class="inact"' if e["inactive"] else ""
        lock = " 🔒" if e["sens"] == "alta" else ""
        return f'<li{cls}><a href="sb://note/{e["id"]}">{html.escape(e["title"])}</a>{lock} <span class="tag">{e["project"]} · {e["type"]}{" %.2f" % e["score"] if e["origin"] == "auto" else ""}</span></li>'

    side = ""
    if d["lineage"] and len(d["lineage"]) > 1:
        items = "".join(f'<li{" class=inact" if x["inactive"] else ""}><a href="sb://note/{x["id"]}">{html.escape(x["title"])}</a> <span class="tag">{x["data"]}</span></li>' for x in d["lineage"])
        side += f"<h3>Linhagem (antiga → atual)</h3><ul>{items}</ul>"
    if d["out"]:
        side += "<h3>Relacionadas</h3><ul>" + "".join(li(e) for e in d["out"][:14]) + "</ul>"
    if d["in"]:
        side += "<h3>Citada por</h3><ul>" + "".join(li(e) for e in d["in"][:14]) + "</ul>"
    body = md_to_html(d["body"], wikimap)
    return (f'<!doctype html><meta charset="utf-8"><style>{READER_CSS}</style><body class="{"dark" if dark else ""}">'
            f'<h1>{html.escape(n["title"])}</h1><div class="chips">{"".join(chips)}</div>{body}'
            f'<div class="side">{side}<p class="path">{html.escape(n["path"])}</p></div></body>')


GRAPH_HTML = r"""<!doctype html><meta charset="utf-8"><style>
:root{--bg:#fff;--fg:#2e3440;--mut:#6b7385;--card:#f3f4f8;--bd:#dde1ea}.dark{--bg:#24273a;--fg:#cad3f5;--mut:#939ab7;--card:#1e2030;--bd:#363a4f}
html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--fg);font:13px system-ui,sans-serif}
canvas{display:block;width:100%;height:100%}#bar{position:absolute;top:10px;left:10px;display:flex;gap:8px;align-items:center;background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:6px 10px}
#legend{position:absolute;bottom:10px;left:10px;max-width:46%;background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:8px 10px;display:flex;flex-wrap:wrap;gap:4px 12px}
.lg{cursor:pointer;display:flex;align-items:center;gap:5px;opacity:1}.lg.off{opacity:.35}.dot{width:10px;height:10px;border-radius:50%}
#tip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:5px 9px;display:none;max-width:340px}
input[type=range]{width:90px}</style><body class="{{DARK}}">
<canvas id="c"></canvas>
<div id="bar"><b id="cnt"></b><label>similaridade ≥ <span id="sv">0.30</span> <input id="min" type="range" min="0.15" max="0.8" step="0.05" value="0.30"></label>
<label><input id="inact" type="checkbox"> substituídas</label><label><input id="auto" type="checkbox" checked> auto</label></div>
<div id="legend"></div><div id="tip"></div>
<script>
const DATA={{DATA}}, COLORS={{COLORS}};
const cv=document.getElementById('c'),ctx=cv.getContext('2d'),tip=document.getElementById('tip');
let W=0,H=0,dpr=window.devicePixelRatio||1,scale=1,ox=0,oy=0,hover=null,drag=null,pan=null,sel=null,tick=0;
const projs=[...new Set(DATA.nodes.map(n=>n.project))].sort(); const off=new Set(); let nodes=[],edges=[],byId={};
function build(){const mn=+document.getElementById('min').value,showIn=document.getElementById('inact').checked,showAuto=document.getElementById('auto').checked;
 const prev=byId; nodes=DATA.nodes.filter(n=>!off.has(n.project)&&(showIn||!n.inactive)).map(n=>{const o=prev[n.id];return o||Object.assign({},n,{x:(Math.random()-.5)*900,y:(Math.random()-.5)*600,vx:0,vy:0})});
 byId={};nodes.forEach(n=>byId[n.id]=n);
 edges=DATA.edges.filter(e=>byId[e.src]&&byId[e.dst]&&(e.origin!=='auto'||(showAuto&&e.score>=mn)));
 nodes.forEach(n=>n.g=0);edges.forEach(e=>{byId[e.src].g++;byId[e.dst].g++});
 document.getElementById('cnt').textContent=nodes.length+' notas · '+edges.length+' relações';tick=0}
function legend(){const L=document.getElementById('legend');L.innerHTML='';projs.forEach(p=>{const d=document.createElement('div');d.className='lg'+(off.has(p)?' off':'');d.innerHTML='<span class="dot" style="background:'+COLORS[p]+'"></span>'+p;d.onclick=()=>{off.has(p)?off.delete(p):off.add(p);legend();build()};L.appendChild(d)})}
function resize(){W=cv.clientWidth;H=cv.clientHeight;cv.width=W*dpr;cv.height=H*dpr}
function step(){const N=nodes.length;for(let i=0;i<N;i++){const a=nodes[i];for(let j=i+1;j<N;j++){const b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+.01;if(d2>90000)continue;const f=1400/d2,d=Math.sqrt(d2);dx/=d;dy/=d;a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f}}
 edges.forEach(e=>{const a=byId[e.src],b=byId[e.dst];let dx=b.x-a.x,dy=b.y-a.y;const d=Math.sqrt(dx*dx+dy*dy)+.01,k=(e.origin==='auto'?.0016:.004)*(d-(e.origin==='auto'?110:70));dx/=d;dy/=d;a.vx+=dx*k*d;a.vy+=dy*k*d;b.vx-=dx*k*d;b.vy-=dy*k*d});
 const cool=Math.max(.15,1-tick/500);nodes.forEach(n=>{n.vx-=n.x*.0009;n.vy-=n.y*.0009;if(n!==drag){n.x+=Math.max(-12,Math.min(12,n.vx))*cool;n.y+=Math.max(-12,Math.min(12,n.vy))*cool}n.vx*=.55;n.vy*=.55});tick++}
const ECOL={supersedes:'#ed8796',contradicts:'#f5a97f',extends:'#a6da95',implements:'#8bd5ca',references:'#c6a0f6',related_to:'#939ab7',links_to:'#6b7385'};
function sx(x){return (x*scale+ox+W/2)}function sy(y){return (y*scale+oy+H/2)}
function draw(){ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
 edges.forEach(e=>{const a=byId[e.src],b=byId[e.dst],hl=hover&&(hover===a||hover===b)||sel&&(sel===a||sel===b);ctx.beginPath();ctx.moveTo(sx(a.x),sy(a.y));ctx.lineTo(sx(b.x),sy(b.y));
  ctx.strokeStyle=ECOL[e.type]||'#939ab7';ctx.globalAlpha=hl?.95:(e.origin==='auto'?.14:.35);ctx.lineWidth=hl?2:(e.origin==='auto'?.6:1.1);ctx.setLineDash(e.type==='supersedes'?[5,4]:[]);ctx.stroke()});
 ctx.setLineDash([]);
 nodes.forEach(n=>{const r=(3+Math.min(10,Math.sqrt(n.g)*2.2))*Math.min(1.6,Math.max(.7,scale));ctx.globalAlpha=n.inactive?.3:1;ctx.beginPath();ctx.arc(sx(n.x),sy(n.y),r,0,7);ctx.fillStyle=COLORS[n.project];ctx.fill();
  if(n.sens==='alta'){ctx.lineWidth=2;ctx.strokeStyle='#d98a1c';ctx.stroke()}if(n===sel||n===hover){ctx.lineWidth=2.5;ctx.strokeStyle=getComputedStyle(document.body).color;ctx.stroke()}});
 ctx.globalAlpha=1;if(scale>1.3||nodes.length<120){ctx.fillStyle=getComputedStyle(document.body).color;ctx.font='11px system-ui';nodes.forEach(n=>{if(n.g>2||scale>2)ctx.fillText(n.title.slice(0,34),sx(n.x)+8,sy(n.y)+3)})}}
function loop(){if(tick<700||drag)step();draw();requestAnimationFrame(loop)}
function pick(mx,my){let best=null,bd=1e9;nodes.forEach(n=>{const d=Math.hypot(sx(n.x)-mx,sy(n.y)-my),r=8+Math.min(10,Math.sqrt(n.g)*2.2);if(d<r&&d<bd){best=n;bd=d}});return best}
cv.onmousemove=ev=>{const r=cv.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;if(drag){drag.x=(mx-ox-W/2)/scale;drag.y=(my-oy-H/2)/scale;tick=Math.min(tick,400);return}
 if(pan){ox+=ev.movementX;oy+=ev.movementY;return}hover=pick(mx,my);if(hover){tip.style.display='block';tip.style.left=(mx+14)+'px';tip.style.top=(my+14)+'px';tip.innerHTML='<b>'+hover.title.replace(/</g,'&lt;')+'</b><br>'+hover.project+' · '+(hover.tipo||hover.kind)+' · '+(hover.data||'')+(hover.sens==='alta'?' · 🔒':'')}else tip.style.display='none'};
cv.onmousedown=ev=>{const r=cv.getBoundingClientRect(),n=pick(ev.clientX-r.left,ev.clientY-r.top);if(n)drag=n;else pan=true};
window.onmouseup=()=>{if(drag){sel=drag;try{window.webkit.messageHandlers.sb.postMessage(String(drag.id))}catch(e){}}drag=null;pan=null};
cv.onwheel=ev=>{ev.preventDefault();const k=ev.deltaY<0?1.12:.89;scale=Math.max(.2,Math.min(6,scale*k))};
window.onresize=resize;['min','inact','auto'].forEach(i=>document.getElementById(i).oninput=()=>{document.getElementById('sv').textContent=(+document.getElementById('min').value).toFixed(2);build()});
window.focusNode=id=>{const n=byId[id];if(n){sel=n;ox=-n.x*scale;oy=-n.y*scale}};
resize();legend();build();loop();
</script>"""


class Win(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SecondBrain", default_width=1280, default_height=800)
        self.c = xmem.connect()
        self.dark = Adw.StyleManager.get_default().get_dark()
        self.project = None
        self.cur_id = None
        self.wikimap = {}
        self.colors = {}
        self.build_ui()
        self.refresh_all()
        threading.Thread(target=self.bg_index, daemon=True).start()

    # ------------------------------------------------------------ UI
    def build_ui(self):
        split = Adw.OverlaySplitView(sidebar_width_fraction=0.2, min_sidebar_width=220, max_sidebar_width=320)
        # barra lateral
        sb = Adw.ToolbarView()
        hb = Adw.HeaderBar(show_title=True)
        hb.set_title_widget(Gtk.Label(label="Projetos", css_classes=["heading"]))
        sb.add_top_bar(hb)
        self.plist = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, css_classes=["navigation-sidebar"])
        self.plist.connect("row-selected", self.on_project)
        sb.set_content(Gtk.ScrolledWindow(child=self.plist, vexpand=True))
        split.set_sidebar(sb)
        # conteúdo
        tv = Adw.ToolbarView()
        hb2 = Adw.HeaderBar()
        self.entry = Gtk.SearchEntry(placeholder_text="Buscar em todas as notas…", hexpand=True)
        self.entry.connect("search-changed", lambda *_: self.do_search())
        self.recall = Gtk.ToggleButton(label="Outros projetos", tooltip_text="Recall: procurar fora do projeto selecionado")
        self.recall.connect("toggled", lambda *_: self.do_search())
        self.inact = Gtk.ToggleButton(label="Substituídas", tooltip_text="Incluir notas substituídas/inativas")
        self.inact.connect("toggled", lambda *_: self.do_search())
        box = Gtk.Box(spacing=6)
        box.append(self.entry)
        box.append(self.recall)
        box.append(self.inact)
        hb2.set_title_widget(box)
        self.stack = Adw.ViewStack()
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        hb2.pack_start(switcher)
        rb = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Reindexar vaults")
        rb.connect("clicked", lambda *_: threading.Thread(target=self.bg_index, daemon=True).start())
        hb2.pack_end(rb)
        tv.add_top_bar(hb2)
        # página notas
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, position=430, shrink_start_child=False, shrink_end_child=False)
        self.results = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, css_classes=["boxed-list-separate"])
        self.results.set_margin_start(8)
        self.results.set_margin_end(8)
        self.results.set_margin_top(8)
        self.results.connect("row-selected", self.on_result)
        paned.set_start_child(Gtk.ScrolledWindow(child=self.results, hscrollbar_policy=Gtk.PolicyType.NEVER, width_request=330))
        self.reader = self.make_webview(js=False)
        paned.set_end_child(self.reader)
        self.stack.add_titled_with_icon(paned, "notas", "Notas", "text-x-generic-symbolic")
        # página grafo
        self.graph = self.make_webview(js=True)
        self.graph.get_user_content_manager().register_script_message_handler("sb")
        self.graph.get_user_content_manager().connect("script-message-received::sb", self.on_graph_click)
        self.stack.add_titled_with_icon(self.graph, "grafo", "Grafo", "network-workgroup-symbolic")
        self.stack.connect("notify::visible-child-name", self.on_page)
        # página pendências
        self.todos = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE, css_classes=["boxed-list"])
        for m in ("start", "end", "top", "bottom"):
            getattr(self.todos, f"set_margin_{m}")(14)
        self.stack.add_titled_with_icon(Gtk.ScrolledWindow(child=self.todos), "pendencias", "Pendências", "task-due-symbolic")
        tv.set_content(self.stack)
        split.set_content(tv)
        self.status = Gtk.Label(xalign=0, css_classes=["dim-label", "caption"], margin_start=12, margin_bottom=4)
        tv.add_bottom_bar(self.status)
        self.set_content(split)

    def make_webview(self, js):
        wv = WebKit.WebView(vexpand=True, hexpand=True)
        st = wv.get_settings()
        st.set_enable_javascript(js)
        st.set_auto_load_images(False)
        st.set_enable_developer_extras(False)
        wv.connect("decide-policy", self.on_policy)
        return wv

    # ------------------------------------------------------------ dados
    def bg_index(self):
        GLib.idle_add(self.status.set_text, "Indexando vaults…")
        try:
            xmem.index(quiet=True)
        except Exception as e:  # noqa: BLE001
            GLib.idle_add(self.status.set_text, f"Falha ao indexar: {e}")
            return
        GLib.idle_add(self.refresh_all)

    def refresh_all(self):
        self.c = xmem.connect()
        projs = xmem.projects_summary(self.c)
        self.colors = {p["project"]: PALETTE[i % len(PALETTE)] for i, p in enumerate(projs)}
        while (r := self.plist.get_first_child()):
            self.plist.remove(r)
        allrow = Adw.ActionRow(title="Todos os projetos", subtitle=f"{sum(p['n'] for p in projs)} notas")
        allrow.proj = None
        self.plist.append(allrow)
        for p in projs:
            sub = f"{p['n']} notas · devtrack {p['last_devtrack'] or '—'}"
            row = Adw.ActionRow(title=p["project"], subtitle=sub)
            dot = Gtk.Label(label="●")
            dot.add_css_class("title-3")
            row.add_prefix(dot)
            dot.set_markup(f'<span foreground="{self.colors[p["project"]]}">●</span>')
            if p["sens"] == "alta":
                row.add_suffix(Gtk.Label(label="🔒"))
            if p["stale"]:
                row.add_suffix(Gtk.Label(label=f"⚠ {p['stale']}", css_classes=["caption", "dim-label"], tooltip_text="itens em aberto parados há mais de 14 dias"))
            row.proj = p["project"]
            self.plist.append(row)
        self.plist.select_row(self.plist.get_row_at_index(0))
        self.do_search()
        self.load_graph()
        self.fill_todos()
        self.status.set_text(f"{self.c.execute('select count(*) from notes').fetchone()[0]} notas · {len(projs)} projetos · índice {xmem.DB_PATH}")

    def on_project(self, _lb, row):
        self.project = getattr(row, "proj", None) if row else None
        self.do_search()
        self.fill_todos()

    def do_search(self):
        q = self.entry.get_text().strip()
        self.results.remove_all()
        rows = []
        if q:
            cur = self.project
            hits = xmem.hybrid(self.c, q, k=40, project=None if self.recall.get_active() else self.project,
                               exclude_project=cur if self.recall.get_active() else None, include_inactive=self.inact.get_active())
            rows = [(h["row"], xmem.snippet(h["row"]["text"], q, 140)) for h in hits]
        else:
            where, args = ("where project=?", (self.project,)) if self.project else ("", ())
            for r in self.c.execute(f"select * from notes {where} order by data desc, id desc limit 80", args):
                rows.append((r, ""))
        for r, snip in rows:
            row = Adw.ActionRow(title=GLib.markup_escape_text(r["title"]), subtitle=GLib.markup_escape_text(f"{r['project']} · {r['tipo'] or r['kind']} · {r['data']}" + (("\n" + snip) if snip else "")))
            row.set_subtitle_lines(3)
            row.set_title_lines(2)
            if r["sens"] == "alta":
                row.add_suffix(Gtk.Label(label="🔒"))
            row.nid = r["id"]
            self.results.append(row)
        self.status.set_text(f"{len(rows)} resultado(s)" + (f" para “{q}”" if q else " (recentes)"))

    def on_result(self, _lb, row):
        if row is not None:
            self.open_note(row.nid)

    def open_note(self, nid):
        d = xmem.note_detail(self.c, nid)
        if not d:
            return
        self.cur_id = nid
        # wikilinks resolvidos pelas arestas do próprio vault
        self.wikimap = {}
        for r in self.c.execute("select n.id,n.rel from notes n where n.vault=(select vault from notes where id=?)", (nid,)):
            stem = os.path.basename(r["rel"].lower())
            self.wikimap[stem[:-3] if stem.endswith(".md") else stem] = r["id"]
        self.reader.load_html(reader_html(d, self.dark, self.wikimap), "sb://reader/")
        self.stack.set_visible_child_name("notas")

    def load_graph(self):
        g = xmem.graph_data(self.c, None, 0.15)
        data = json.dumps({"nodes": [{k: n[k] for k in ("id", "project", "title", "tipo", "kind", "data", "sens", "inactive")} for n in g["nodes"]],
                           "edges": [{"src": e["src"], "dst": e["dst"], "type": e["type"], "score": e["score"], "origin": e["origin"]} for e in g["edges"]]}, ensure_ascii=False).replace("<", "\\u003c")
        html_ = GRAPH_HTML.replace("{{DATA}}", data).replace("{{COLORS}}", json.dumps(self.colors)).replace("{{DARK}}", "dark" if self.dark else "")
        self.graph.load_html(html_, "sb://graph/")

    def on_page(self, *_):
        pass

    def on_graph_click(self, _ucm, value):
        try:
            nid = int(value.to_string())
        except (ValueError, AttributeError):
            return
        self.open_note(nid)
        self.stack.set_visible_child_name("notas")

    def fill_todos(self):
        self.todos.remove_all()
        items = [t for t in xmem.open_items(self.c, project=self.project, limit=400) if t["idade"] > xmem.STALE_OPEN_DAYS]
        for t in items[:150]:
            row = Adw.ActionRow(title=GLib.markup_escape_text(t["text"][:160]), subtitle=GLib.markup_escape_text(f"{t['project']} · {t['rel'][:-3]} · parado há {t['idade']} dias"))
            row.set_title_lines(2)
            self.todos.append(row)
        if not items:
            self.todos.append(Adw.ActionRow(title="Nenhum item parado", subtitle="Itens em aberto há mais de 14 dias aparecem aqui."))

    def on_policy(self, wv, decision, ptype):
        if ptype != WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            return False
        uri = decision.get_navigation_action().get_request().get_uri()
        if uri.startswith(("sb://reader", "sb://graph", "about:")):
            return False
        if uri.startswith("sb://note/"):
            decision.ignore()
            try:
                self.open_note(int(uri.rsplit("/", 1)[1]))
            except ValueError:
                pass
            return True
        decision.ignore()
        if uri.startswith(("http://", "https://")):
            Gtk.UriLauncher.new(uri).launch(self, None, None)
        return True


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.selftest = "--selftest" in sys.argv

    def do_activate(self):
        Gtk.Window.set_default_icon_name(APP_ID)  # ícone instalado por scripts/install-tools.sh
        win = Win(self)
        win.present()
        if self.selftest:  # fumaça: abre, indexa, fecha sozinho
            GLib.timeout_add(7000, lambda: (print("selftest: janela e dados ok"), self.quit()))


if __name__ == "__main__":
    sys.exit(App().run([a for a in sys.argv[:1]]))
