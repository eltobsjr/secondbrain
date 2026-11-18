#!/usr/bin/env python3
"""SecondBrain — interface nativa (GTK4 + libadwaita + WebKitGTK) sobre a memória cruzada (xmem).

Lê o MESMO índice que o Claude usa. Só o Quadro grava, e só `quadro.md` (com backup fora do vault); notas nunca são alteradas.
Páginas: Notas (busca híbrida + leitor), Grafo (todas as notas e relações), Quadro (kanban das pendências).
"""
import hashlib
import html
import json
import os
import re
import sys
import threading
import time
import urllib.parse

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango, WebKit  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (os.path.join(HERE, "..", "scripts"), os.path.expanduser("~/.local/share/secondbrain/bin")):
    if os.path.isfile(os.path.join(cand, "xmem.py")):
        sys.path.insert(0, cand)
        break
import xmem  # noqa: E402

if HERE not in sys.path:  # `python3 -I` não põe a pasta do script no caminho
    sys.path.insert(0, HERE)
import theme  # noqa: E402
import board  # noqa: E402  (scripts/ ou ~/.local/share/secondbrain/bin)
import board_page  # noqa: E402

APP_ID = "io.github.eltobsjr.SecondBrain"
PALETTE = theme.PALETTE


def md_render(body, wikimap):
    """Markdown -> (HTML seguro, sumário). HTML cru é escapado antes; wikilinks viram sb://note/<id>."""
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
        md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "nl2br", "toc"])
        out = md.convert(body)
        toc = []

        def walk(tokens):
            for t in tokens:
                if t["level"] in (2, 3):
                    toc.append((t["level"], t["name"], t["id"]))
                walk(t.get("children", []))

        walk(md.toc_tokens)
        return out, toc
    except Exception:
        return "<pre>" + html.escape(body) + "</pre>", []


def md_to_html(body, wikimap):
    return md_render(body, wikimap)[0]


EDGE_LABEL = {"links_to": "Cita", "related_to": "Semelhante", "supersedes": "Substitui", "extends": "Estende",
              "contradicts": "Contradiz", "implements": "Implementa", "references": "Referencia"}


def reader_html(d, dark, wikimap):
    n = d["note"]
    chips = [f'<span class="chip kind">{html.escape(n["tipo"] or n["kind"])}</span>']
    if n["status"]:
        chips.append(f'<span class="chip ok">{html.escape(n["status"])}</span>')
    if n["data"]:
        chips.append(f'<span class="chip">{html.escape(fmt_date(n["data"]))}</span>')
    if n["sens"] == "alta":
        chips.append('<span class="chip warn">Sensível</span>')
    if n["inactive"]:
        chips.append('<span class="chip">Inativa (substituída)</span>')

    def li(e, label=None):
        cls = ' class="inact"' if e["inactive"] else ""
        sens = " · sensível" if e["sens"] == "alta" else ""
        label = label or EDGE_LABEL.get(e["type"], e["type"])
        score = f" {e['score']:.2f}".replace(".", ",") if e["origin"] == "auto" else ""
        return (f'<li{cls}><a href="sb://note/{e["id"]}">{html.escape(e["title"])}</a>'
                f'<span class="tag">{label}{score} · {html.escape(e["project"])}{sens}</span></li>')

    body_md = re.sub(r"\A\s*# [^\n]*\n", "", d["body"], count=1)  # o título já aparece no cabeçalho da página
    body, toc = md_render(body_md, wikimap)
    toc_li = "".join(f'<li class="l{lv}"><a href="#{i}">{html.escape(nm)}</a></li>' for lv, nm, i in toc)
    blocks = []
    if len(toc) >= 3:
        blocks.append(f'<div class="blk toc toc-wide"><h3>Nesta nota</h3><ul>{toc_li}</ul></div>')
    if d["lineage"] and len(d["lineage"]) > 1:
        items = "".join(f'<li{" class=inact" if x["inactive"] else ""}><a href="sb://note/{x["id"]}">{html.escape(x["title"])}</a>'
                        f'<span class="tag">{html.escape(fmt_date(x["data"] or ""))}</span></li>' for x in d["lineage"])
        blocks.append(f'<div class="blk"><h3>Linhagem (da mais antiga à atual)</h3><ul>{items}</ul></div>')
    if d["out"]:
        blocks.append('<div class="blk"><h3>Relacionadas</h3><ul>' + "".join(li(e) for e in d["out"][:10]) + "</ul></div>")
    if d["in"]:
        blocks.append('<div class="blk"><h3>Citada por</h3><ul>' + "".join(li(e, "Cita esta nota") for e in d["in"][:10]) + "</ul></div>")
    todos = d.get("todos") or []
    if todos:
        rows = "".join(f'<li class="todo{" done" if t["checked"] else ""}"><i></i><span>{html.escape(t["text"][:140])}</span></li>' for t in todos[:12])
        abertos = sum(1 for t in todos if not t["checked"])
        blocks.append(f'<div class="blk"><h3>Itens desta nota ({abertos} em aberto)</h3><ul>{rows}</ul></div>')
    blocks.append(f'<p class="path">{html.escape(n["path"])}</p>')
    narrow_toc = f'<div class="toc-narrow"><h3>Nesta nota</h3><ul>{toc_li}</ul></div>' if len(toc) >= 3 else ""
    crumb = f'{html.escape(n["project"])} › {html.escape(n["kind"])}'
    return (f'<!doctype html><meta charset="utf-8"><style>{theme.reader_css(dark)}</style><body>'
            f'<div class="layout"><article class="page"><div class="crumb">{crumb}</div><h1>{html.escape(n["title"])}</h1>'
            f'<div class="chips">{"".join(chips)}</div>{narrow_toc}{body}</article>'
            f'<aside class="ctx">{"".join(blocks)}</aside></div></body>')


def graph_theme():
    """Variáveis do grafo (claro em :root, escuro em body.dark), vindas dos mesmos tokens do resto da interface."""
    def vars_(t):
        return (f"--bg:{t['base']};--fg:{t['text']};--mut:{t['sub0']};--card:{t['mantle']}f2;--bd:{t['s0']};"
                f"--ac:{t['blue']};--halo:{t['base']};--panel:{t['mantle']};--chip:{t['s0']};--chip-fg:{t['sub1']};"
                f"--warn:{t['peach']};--ok:{t['green']};--kind:{t['mauve']};--err:{t['red']};--on-ac:{t['on_accent']}")
    return f":root{{{vars_(theme.LIGHT)};color-scheme:light}}\nbody.dark{{{vars_(theme.DARK)};color-scheme:dark}}"


GRAPH_HTML = r"""<!doctype html><meta charset="utf-8"><title>Grafo</title><style>
{{THEME}}
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--fg);font:14px/1.45 Inter,Cantarell,system-ui,sans-serif}
button,select,input{font:inherit;color:inherit}
#app{display:grid;grid-template-columns:268px minmax(0,1fr) 0;height:100%;transition:grid-template-columns .18s ease}
#app.sel{grid-template-columns:268px minmax(0,1fr) 344px}
#left,#right{background:var(--panel);overflow:auto}
#left{grid-column:1}#main{grid-column:2;grid-row:1}#right{grid-column:3;grid-row:1}
#left{border-right:1px solid var(--bd);padding:22px 20px;display:flex;flex-direction:column;gap:24px}
#right{border-left:1px solid var(--bd);padding:0;visibility:hidden}
#app.sel #right{visibility:visible;padding:24px}
.sec{font-size:12px;font-weight:600;color:var(--mut);letter-spacing:.02em;margin:0 0 8px}
.lh{display:flex;align-items:center;justify-content:space-between}
.lh h2{margin:0;font-size:16px;font-weight:700}
.lnk{border:0;background:transparent;color:var(--ac);font-size:13px;font-weight:500;cursor:pointer;padding:2px 0}
.lnk:hover{text-decoration:underline}
#plist{display:flex;flex-direction:column;gap:1px;margin:0 -6px}
.prj{display:flex;align-items:center;gap:10px;border:0;background:transparent;text-align:left;padding:5px 6px;border-radius:8px;cursor:pointer;font-size:14px;color:var(--fg)}
.prj:hover{background:var(--chip)}
.prj .box{width:16px;height:16px;border-radius:5px;border:2px solid;flex:none;background:currentColor}
.prj.off{color:var(--mut)}.prj.off .box{background:transparent!important}
.prj .t{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.prj .n{color:var(--mut);font-size:12px}
.row2{display:flex;gap:14px;margin-top:6px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 12px;border-radius:999px;border:0;background:var(--chip);color:var(--chip-fg);font-size:13px;font-weight:500;cursor:pointer}
.chip.on{background:var(--ac);color:var(--on-ac);font-weight:600}
.chip .n{font-size:12px;opacity:.8}
.static{cursor:default}
select{width:100%;height:36px;border-radius:10px;border:1px solid var(--bd);background-color:var(--bg);color:var(--fg);padding:0 10px}
input[type=range]{width:100%;accent-color:var(--ac)}
.hint{font-size:12px;line-height:1.5;color:var(--mut);margin:6px 0 0}
.leg{display:flex;flex-direction:column;gap:9px;margin-top:auto;font-size:13px;color:var(--chip-fg)}
.leg span{display:flex;align-items:center;gap:10px}
.leg i{display:inline-block;width:26px;height:0;border-top:2px solid}
#main{display:flex;flex-direction:column;min-width:0;min-height:0;background:var(--bg)}
#top{height:64px;flex:none;display:flex;align-items:center;gap:14px;padding:0 20px;border-bottom:1px solid var(--bd);background:var(--panel)}
#q{flex:1 1 140px;min-width:110px;max-width:300px;height:40px;border-radius:10px;border:1px solid var(--bd);background:var(--bg);padding:0 14px;outline:none}
#q:focus{border-color:var(--ac)}
.seg{display:flex;padding:3px;border-radius:10px;background:var(--bg);border:1px solid var(--bd)}
.seg button{border:0;background:transparent;border-radius:8px;padding:6px 12px;font-size:13px;font-weight:500;color:var(--mut);cursor:pointer;white-space:nowrap}
.seg button:hover{color:var(--fg)}
.seg button.on{background:var(--chip);color:var(--fg)}
#crumb{display:none;align-items:center;gap:10px;white-space:nowrap}
#crumb.show{display:flex}
#crumb b{font-size:15px}
#hops{display:none}
#hops.show{display:flex}
#stats{margin-left:auto;color:var(--mut);font-size:13px;white-space:nowrap}
#stage{position:relative;flex:1;min-height:0}
canvas{position:absolute;inset:0;width:100%;height:100%;cursor:grab}canvas.drag{cursor:grabbing}
.zoom{position:absolute;left:18px;bottom:18px;display:flex;flex-direction:column;gap:6px}
.zoom button{width:40px;height:40px;border-radius:10px;border:1px solid var(--bd);background:var(--panel);cursor:pointer;font-size:20px;color:var(--chip-fg);display:flex;align-items:center;justify-content:center}
.zoom button:hover{border-color:var(--ac);color:var(--ac)}
#right .tags{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
#right .tag{display:inline-flex;align-items:center;height:24px;padding:0 10px;border-radius:999px;background:var(--chip);color:var(--chip-fg);font-size:12px;font-weight:500}
#right .tag.warn{color:var(--warn)}#right .tag.ok{color:var(--ok)}#right .tag.kind{color:var(--kind)}
#right h3{margin:0 0 8px;font-size:20px;line-height:1.3;font-weight:700;letter-spacing:-.01em}
#right .meta{display:flex;align-items:center;gap:8px;color:var(--mut);font-size:13px}
#right .meta i{width:9px;height:9px;border-radius:50%;flex:none}
.acts{display:flex;gap:10px;margin:18px 0 22px}
.btn{height:40px;padding:0 16px;border-radius:10px;border:0;background:var(--chip);color:var(--fg);font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center}
.btn.pri{flex:1;background:var(--ac);color:var(--on-ac)}
.btn:hover{filter:brightness(1.08)}
#rs .sec{margin-bottom:10px}
.nb{display:block;width:100%;text-align:left;border:0;background:var(--bg);color:var(--fg);padding:10px 12px;border-radius:10px;cursor:pointer;margin-bottom:8px;line-height:1.35}
.nb:hover{outline:1px solid var(--ac)}
.nb small{display:flex;align-items:center;gap:8px;margin-top:3px;color:var(--mut);font-size:12px}
.nb small i{width:8px;height:8px;border-radius:50%;flex:none}
#tip{position:absolute;pointer-events:none;background:var(--panel);border:1px solid var(--bd);border-radius:10px;padding:7px 11px;display:none;max-width:340px;font-size:13px;box-shadow:0 6px 18px rgba(0,0,0,.18);z-index:5}
#tip b{font-weight:600}#tip span{color:var(--mut)}
#ftog{display:none}
@media (max-width:1240px){
  #app,#app.sel{grid-template-columns:0 minmax(0,1fr) 0}
  #left,#right{position:absolute;z-index:6;top:0;bottom:0;box-shadow:0 0 28px rgba(0,0,0,.28);transition:transform .18s ease}
  #left{left:0;width:288px;transform:translateX(-102%)}
  #app.fo #left{transform:none}
  #right{right:0;width:344px;transform:translateX(102%);visibility:visible}
  #app.sel #right{transform:none}
  #ftog{display:inline-flex}
}
#empty{position:absolute;inset:0;display:none;align-items:center;justify-content:center;color:var(--mut);font-size:15px;pointer-events:none}
</style><body>
<div id="app">
  <aside id="left">
    <div class="lh"><h2>Filtros</h2><button class="lnk" id="reset">Limpar</button></div>
    <div><div class="sec">Projetos</div><div id="plist"></div>
      <div class="row2"><button class="lnk" id="allp">Todos</button><button class="lnk" id="nonep">Nenhum</button></div></div>
    <div><div class="sec">Camadas</div><div class="chips" id="groups"></div></div>
    <div><div class="sec">Tipo de nota</div><select id="tipo" title="Filtrar por tipo de nota"></select></div>
    <div><div class="lh"><span class="sec" style="margin:0">Semelhança mínima</span><b id="sv">0.30</b></div>
      <input id="min" type="range" min="0.16" max="0.75" step="0.02" value="0.30">
      <p class="hint">Mais alto mostra menos arestas automáticas: só as mais fortes.</p></div>
    <div class="leg"><div class="sec" style="margin-bottom:0">Legenda</div>
      <span><i style="border-color:var(--mut)"></i>Link direto</span>
      <span><i style="border-color:var(--mut);opacity:.5"></i>Semelhança automática</span>
      <span><i style="border-color:var(--ac)"></i>Entre projetos</span>
      <span style="color:var(--mut);font-size:12px">Duplo clique abre a nota</span></div>
  </aside>
  <section id="main">
    <div id="top">
      <div id="crumb"><button class="lnk" id="cback">← Todos os projetos</button><b id="crumbn"></b></div>
      <input id="q" placeholder="Buscar nota ou projeto no mapa" spellcheck="false">
      <button class="btn" id="ftog">Filtros</button>
      <div class="seg" id="modes">
        <button id="m-all" class="on">Tudo</button><button id="m-cross">Entre projetos</button><button id="m-local" title="Só a vizinhança da nota selecionada">Vizinhança</button><button id="m-iso" title="Notas sem nenhuma relação visível">Isoladas</button>
      </div>
      <div class="seg" id="hops"><button id="h1" class="on">1 salto</button><button id="h2">2 saltos</button></div>
      <span id="stats"></span>
    </div>
    <div id="stage">
      <canvas id="c"></canvas><div id="empty">Nenhuma nota com os filtros atuais</div><div id="tip"></div>
      <div class="zoom"><button id="zin" aria-label="Aproximar">+</button><button id="zout" aria-label="Afastar">−</button><button id="fit" title="Ajustar à tela (F)" aria-label="Ajustar à tela">⤢</button></div>
    </div>
  </section>
  <aside id="right">
    <div class="tags" id="rc"></div><h3 id="rt"></h3><div class="meta" id="rm"></div>
    <div class="acts"><button class="btn pri" id="open">Abrir nota</button><button class="btn" id="nbh">Vizinhança</button></div>
    <div id="rs" style="display:none"><div class="sec">Relações</div><div id="rn"></div></div>
  </aside>
</div>
<script>
const DATA={{DATA}}, COLORS={{COLORS}}, SIG="{{SIG}}", START_PROJECT={{PROJECT}};
const KG={tarefa:'t',decisao:'k',feature:'k',rfc:'k',nota:'k',analise:'k',padrao:'k',aprendizado:'k',postmortem:'k',release:'k','visao-geral':'k',
          memory:'m',devtrack:'r',commit:'r',estado:'r',prioridade:'r','claude-md':'r',checklist:'r',projeto:'r'};
const GROUP_LABEL={k:'Conhecimento',m:'Memória',t:'Tarefas',r:'Registro'};
const STATUS_VAR={fazendo:'--warn',bloqueado:'--err',revisao:'--kind'};
const cv=document.getElementById('c'),ctx=cv.getContext('2d'),tip=document.getElementById('tip');
const N=DATA.nodes.map(n=>Object.assign({},n));
const byId=new Map(N.map(n=>[n.id,n]));
const ADJ=new Map(N.map(n=>[n.id,[]]));
for(const e of DATA.edges){ if(!byId.has(e.src)||!byId.has(e.dst)) continue;
  ADJ.get(e.src).push({e,other:e.dst}); ADJ.get(e.dst).push({e,other:e.src}); }
const projects=[...new Set(N.map(n=>n.project))].sort((a,b)=>a.localeCompare(b));
const projCount={}; N.forEach(n=>{projCount[n.project]=(projCount[n.project]||0)+1});
const state={projects:new Set(projects),groups:new Set(['k','m','t']),min:0.30,cross:false,isolated:false,q:'',tipo:'',local:0,sel:null,hover:null,mode:'all',focus:null};
const cam={x:0,y:0,k:1};
let W=0,H=0,dpr=window.devicePixelRatio||1,dirty=true,raf=0,tween=null,pan=null,dragN=null,down=null,moved=false;
let vis={nodes:[],edges:[],deg:new Map(),projects:new Map()};

/* ---------- utilidades ---------- */
const rgb=(hex,a)=>{const m=/^#?([0-9a-f]{6})$/i.exec(hex||'');if(!m)return 'rgba(140,150,170,'+a+')';
  const n=parseInt(m[1],16);return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`;};
const esc=s=>String(s==null?'':s);
const sx=x=>(x+cam.x)*cam.k+W/2, sy=y=>(y+cam.y)*cam.k+H/2;
const wx=mx=>(mx-W/2)/cam.k-cam.x, wy=my=>(my-H/2)/cam.k-cam.y;
function schedule(){dirty=true;if(!raf)raf=requestAnimationFrame(frame)}
function frame(){raf=0;if(tween){const t=Math.min(1,(performance.now()-tween.t0)/tween.ms),e=1-Math.pow(1-t,3);
    cam.x=tween.x0+(tween.x-tween.x0)*e;cam.y=tween.y0+(tween.y-tween.y0)*e;cam.k=tween.k0+(tween.k-tween.k0)*e;
    if(t>=1){cam.x=tween.x;cam.y=tween.y;cam.k=tween.k;tween=null}dirty=true}
  if(dirty){draw();dirty=false}
  if(tween)schedule()}  /* animação em curso pede o próximo quadro (antes só avançava quando o mouse mexia) */

/* ---------- filtros ---------- */
function neighborhood(sel,hops,edges){
  const adj=new Map();
  for(const e of edges){
    if(!adj.has(e.src))adj.set(e.src,[]); if(!adj.has(e.dst))adj.set(e.dst,[]);
    adj.get(e.src).push(e.dst); adj.get(e.dst).push(e.src);
  }
  const dist=new Map([[sel,0]]); let front=[sel];
  for(let h=0;h<hops;h++){
    const nxt=[];
    for(const id of front)for(const o of adj.get(id)||[])if(!dist.has(o)){dist.set(o,h+1);nxt.push(o)}
    front=nxt;
  }
  return dist;
}
function build(){
  const q=state.q.trim().toLowerCase();
  const nodes=N.filter(n=>state.projects.has(n.project)&&state.groups.has(KG[n.kind]||'r')&&
    (!state.tipo||n.tipo===state.tipo)&&
    (!q||(n.title+' '+n.project+' '+(n.tipo||'')).toLowerCase().includes(q)));
  const ids=new Set(nodes.map(n=>n.id));
  const edges=DATA.edges.filter(e=>ids.has(e.src)&&ids.has(e.dst)&&
    (e.type!=='related_to'||e.score>=state.min)&&(!state.cross||e.cross));
  const deg=new Map(); for(const e of edges){deg.set(e.src,(deg.get(e.src)||0)+1);deg.set(e.dst,(deg.get(e.dst)||0)+1)}
  let shown;
  if(state.local&&state.sel&&ids.has(state.sel)){
    const dist=neighborhood(state.sel,state.local,edges);
    shown=nodes.filter(n=>dist.has(n.id));
  }else{
    shown=state.isolated||q||state.tipo||state.focus?nodes:nodes.filter(n=>deg.get(n.id));
  }
  const sid=new Set(shown.map(n=>n.id));
  const finalEdges=edges.filter(e=>sid.has(e.src)&&sid.has(e.dst));
  const projs=new Map();
  for(const n of shown){const s=projs.get(n.project)||{n:0,cx:0,cy:0,minx:1e9,maxx:-1e9,miny:1e9,maxy:-1e9};
    s.n++;s.cx+=n.x;s.cy+=n.y;s.minx=Math.min(s.minx,n.x);s.maxx=Math.max(s.maxx,n.x);s.miny=Math.min(s.miny,n.y);s.maxy=Math.max(s.maxy,n.y);projs.set(n.project,s)}
  for(const s of projs.values()){s.cx/=s.n;s.cy/=s.n}
  vis={nodes:shown,edges:finalEdges,deg,projects:projs,ids:sid};hubs=null;
  const cross=finalEdges.filter(e=>e.cross).length;
  document.getElementById('stats').textContent=`${shown.length} notas · ${finalEdges.length} relações · ${cross} entre projetos`
    +(state.local&&!state.sel?' · modo local: selecione uma nota':'');
  document.getElementById('empty').style.display=shown.length?'none':'flex';
  hulls=null;schedule();
}

/* ---------- cascas (hulls) ---------- */
let hulls=null;
function convexHull(pts){
  if(pts.length<3)return pts.slice();
  const p=pts.slice().sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  const cross=(o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);
  const lo=[],up=[];
  for(const q of p){while(lo.length>=2&&cross(lo[lo.length-2],lo[lo.length-1],q)<=0)lo.pop();lo.push(q)}
  for(let i=p.length-1;i>=0;i--){const q=p[i];while(up.length>=2&&cross(up[up.length-2],up[up.length-1],q)<=0)up.pop();up.push(q)}
  lo.pop();up.pop();return lo.concat(up);
}
function computeHulls(){
  const out=[];
  for(const [p,s] of vis.projects){ if(s.n<3||state.q.trim()) continue;
    const pts=vis.nodes.filter(n=>n.project===p).map(n=>[n.x,n.y]);
    if(s.maxx-s.minx<44||s.maxy-s.miny<44)continue;
    const h=convexHull(pts); if(h.length<3)continue;
    out.push({p,h,color:COLORS[p]||'#8a97b2'});}
  return out;
}
function smoothClosed(path,pts){
  if(pts.length<3)return false;
  const mid=(a,b)=>[(a[0]+b[0])/2,(a[1]+b[1])/2];
  let m=mid(pts[pts.length-1],pts[0]); path.moveTo(...m);
  for(let i=0;i<pts.length;i++){const cur=pts[i],nxt=pts[(i+1)%pts.length],mn=mid(cur,nxt);path.quadraticCurveTo(cur[0],cur[1],mn[0],mn[1])}
  path.closePath();return true;
}

/* ---------- desenho ---------- */
function draw(){
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
  ctx.fillStyle=getComputedStyle(document.body).getPropertyValue('--bg');ctx.fillRect(0,0,W,H);
  const bg=getComputedStyle(document.body).getPropertyValue('--bg').trim();
  if(!hulls)hulls=computeHulls();
  for(const h of hulls){ctx.beginPath();if(!smoothClosed(ctx,h.h.map(p=>[sx(p[0]),sy(p[1])])))continue;
    ctx.fillStyle=rgb(h.color,0.07);ctx.fill();ctx.strokeStyle=rgb(h.color,0.30);ctx.lineWidth=1.2;ctx.stroke()}
  drawProjectLabels()
  const sel=state.sel,hover=state.hover;
  const focus=sel||hover;
  const near=new Set(); if(focus){near.add(focus);for(const a of ADJ.get(focus)||[])near.add(a.other)}
  drawEdges(vis.edges,focus,near);
  let labels=[];
  for(const n of vis.nodes){
    const d=vis.deg.get(n.id)||0, r=3+Math.min(9,Math.sqrt(d)*1.7)*(0.75+Math.min(.55,cam.k*.18));
    const dim=focus&&!near.has(n.id);
    ctx.globalAlpha=dim?0.22:(n.inactive?0.5:1);
    if(n.kind==='tarefa'){const R=r+3,X=sx(n.x),Y=sy(n.y);ctx.beginPath();ctx.moveTo(X,Y-R);ctx.lineTo(X+R,Y);ctx.lineTo(X,Y+R);ctx.lineTo(X-R,Y);ctx.closePath();
      ctx.fillStyle=cssv(STATUS_VAR[n.tipo]||'--warn');ctx.fill();ctx.strokeStyle=bg;ctx.lineWidth=1.5;ctx.stroke();continue}
    ctx.beginPath();ctx.arc(sx(n.x),sy(n.y),r,0,6.2832);ctx.fillStyle=COLORS[n.project]||'#8a97b2';ctx.fill();
    if(n.sens==='alta'){ctx.strokeStyle=rgb('#d98a1c',.9);ctx.lineWidth=1.4;ctx.stroke()}
    if(n.inactive){ctx.setLineDash([2,2]);ctx.strokeStyle=bg;ctx.lineWidth=1.2;ctx.stroke();ctx.setLineDash([])}
    if(n.id===sel||n.id===hover){ctx.strokeStyle=getComputedStyle(document.body).color;ctx.lineWidth=2;ctx.beginPath();ctx.arc(sx(n.x),sy(n.y),r+2.5,0,6.2832);ctx.stroke()}
    if(focus&&near.has(n.id)&&n.id!==focus&&n.id!==sel)labels.push(n);
    if(cam.k>=1.8)labels.push(n);
  }
  ctx.globalAlpha=1;
  if(sel){/* rótulo sempre para a selecionada */}
  if(state.focus)labels=labels.concat(vis.nodes);
  if(!focus)labels=labels.concat(topHubs());
  if(sel&&byId.has(sel)&&vis.deg.has(sel))labels.push(byId.get(sel));
  if(hover&&byId.has(hover)&&vis.deg.has(hover))labels.push(byId.get(hover));
  drawLabels(labels);
  ctx.font='12px Inter,Cantarell,system-ui';ctx.fillStyle=getComputedStyle(document.body).getPropertyValue('--mut');
  ctx.fillText(cam.k<0.3?'Role para aproximar e ver os nomes':'',W-190,H-14);
}
let hubs=null;
function topHubs(){
  if(hubs)return hubs;
  hubs=vis.nodes.slice().sort((a,b)=>(vis.deg.get(b.id)||0)-(vis.deg.get(a.id)||0)).slice(0,22);
  return hubs;
}
function pill(x,y,text,color){
  ctx.font='600 12px Inter,Cantarell,system-ui';ctx.textBaseline='middle';
  const w=ctx.measureText(text).width+16,h=22;
  const bg=getComputedStyle(document.body).getPropertyValue('--card').trim()||'rgba(255,255,255,.9)';
  ctx.beginPath();
  if(ctx.roundRect)ctx.roundRect(x-w/2,y-h/2,w,h,11);else ctx.rect(x-w/2,y-h/2,w,h);
  ctx.globalAlpha=.92;ctx.fillStyle=bg;ctx.fill();ctx.globalAlpha=1;
  ctx.strokeStyle=rgb(color,.45);ctx.lineWidth=1;ctx.stroke();
  ctx.textAlign='center';ctx.fillStyle=color;ctx.fillText(text,x,y);
  ctx.textAlign='left';ctx.textBaseline='alphabetic';
  return w;
}
function drawProjectLabels(){
  const placed=[];pillRects=[];
  for(const [p,s] of vis.projects){
    if(s.n<3||state.q.trim())continue;
    const name=p,x=sx(s.cx),y=sy(s.miny)-18;
    ctx.font='600 12px Inter,Cantarell,system-ui';const w=ctx.measureText(name).width+12;
    if(placed.some(r=>Math.abs(x-r[0])<(w+r[1])/2+4&&Math.abs(y-r[2])<20))continue;
    placed.push([x,w,y]);
    const pw=pill(x,y,name,COLORS[p]||'#8a97b2');pillRects.push([x-pw/2,y-11,pw,22,p]);
  }
}
const TYPED={task:['--warn',[3,3]],supersedes:['--kind',[6,4]],extends:['--ok',[]],contradicts:['--err',[]],implements:['--warn',[]],references:['--mut',[2,3]]};
const cssv=v=>getComputedStyle(document.body).getPropertyValue(v).trim();
function drawEdges(edges,focus,near){
  const b={at:[],am:[],ct:[],cm:[]};
  for(const e of edges){
    const incident=focus&&(e.src===focus||e.dst===focus);
    if(incident||TYPED[e.type])continue;
    (e.cross?(e.type==='related_to'?b.ct:b.cm):(e.type==='related_to'?b.at:b.am)).push(e);
  }
  const stroke=(arr,color,alpha,width)=>{if(!arr.length)return;ctx.beginPath();
    for(const e of arr){const a=byId.get(e.src),c=byId.get(e.dst);if(!a||!c)continue;ctx.moveTo(sx(a.x),sy(a.y));ctx.lineTo(sx(c.x),sy(c.y))}
    ctx.strokeStyle=color;ctx.globalAlpha=alpha;ctx.lineWidth=width;ctx.stroke();ctx.globalAlpha=1};
  const mut=getComputedStyle(document.body).getPropertyValue('--mut').trim(),ac=getComputedStyle(document.body).getPropertyValue('--ac').trim();
  const faded=(focus&&!near.has(-1))?0.55:1;
  stroke(b.at,mut,0.26*faded,0.9);stroke(b.am,mut,0.50*faded,1.15);
  stroke(b.ct,ac,0.17*faded,0.85);stroke(b.cm,ac,0.55*faded,1.3);
  for(const [t,[v,dash]] of Object.entries(TYPED)){
    const arr=edges.filter(e=>e.type===t&&!(focus&&(e.src===focus||e.dst===focus)));if(!arr.length)continue;
    ctx.beginPath();
    for(const e of arr){const a=byId.get(e.src),c=byId.get(e.dst);if(!a||!c)continue;ctx.moveTo(sx(a.x),sy(a.y));ctx.lineTo(sx(c.x),sy(c.y))}
    ctx.setLineDash(dash);ctx.strokeStyle=cssv(v);ctx.globalAlpha=.9*faded;ctx.lineWidth=1.7;ctx.stroke();ctx.setLineDash([]);ctx.globalAlpha=1;
  }
  if(!focus)return;
  const a=byId.get(focus);if(!a)return;
  ctx.beginPath();
  for(const adj of ADJ.get(focus)||[]){const c=byId.get(adj.other);if(!c||!inVis(c.id))continue;
    ctx.moveTo(sx(a.x),sy(a.y));ctx.lineTo(sx(c.x),sy(c.y))}
  ctx.strokeStyle=getComputedStyle(document.body).getPropertyValue('--fg').trim();ctx.globalAlpha=.55;ctx.lineWidth=1.6;ctx.stroke();ctx.globalAlpha=1;
}
function inVis(id){return vis.ids.has(id)}
function drawLabels(nodes){
  const seen=new Set(),titles=new Set(),rects=[];
  const color=getComputedStyle(document.body).color,halo=getComputedStyle(document.body).getPropertyValue('--halo');
  ctx.font='12px Inter,Cantarell,system-ui';ctx.textAlign='left';ctx.textBaseline='middle';
  for(const n of nodes){
    if(!n||seen.has(n.id))continue;seen.add(n.id);
    if(titles.has(n.title)&&n.id!==state.sel)continue;
    const x=sx(n.x)+8,y=sy(n.y),t=n.title.length>42?n.title.slice(0,41)+'…':n.title;
    titles.add(n.title);
    const w=ctx.measureText(t).width;
    if(rects.some(r=>x<r[0]+r[2]+3&&x+w>r[0]-3&&y-9<r[1]+r[3]&&y+9>r[1]))continue;
    rects.push([x,y-9,w+4,18]);
    ctx.lineWidth=3;ctx.strokeStyle=halo;ctx.strokeText(t,x,y);ctx.fillStyle=color;ctx.fillText(t,x,y);
    if(rects.length>140)break;
  }
  ctx.textBaseline='alphabetic';
}

/* ---------- interação ---------- */
function pick(mx,my){
  let best=null,bd=1e9;
  for(const n of vis.nodes){const dx=sx(n.x)-mx,dy=sy(n.y)-my,d=Math.hypot(dx,dy);
    const r=(3+Math.min(9,Math.sqrt(vis.deg.get(n.id)||0)*1.7))*(0.75+Math.min(.55,cam.k*.18))+7;
    if(d<r&&d<bd){best=n;bd=d}}
  return best;
}
cv.addEventListener('pointerdown',ev=>{
  userCam=true;
  const r=cv.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;
  const n=pick(mx,my);down={mx,my};moved=false;
  if(n){dragN=n;cv.classList.add('drag');cv.setPointerCapture(ev.pointerId)}
  else{pan={mx,my,cx:cam.x,cy:cam.y};cv.classList.add('drag');cv.setPointerCapture(ev.pointerId)}
});
cv.addEventListener('pointermove',ev=>{
  const r=cv.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;
  if(down&&Math.hypot(mx-down.mx,my-down.my)>3)moved=true;
  if(dragN){dragN.x=wx(mx);dragN.y=wy(my);schedule();return}
  if(pan){cam.x=pan.cx+(mx-pan.mx)/cam.k;cam.y=pan.cy+(my-pan.my)/cam.k;schedule();return}
  const n=pick(mx,my);const id=n?n.id:null;
  cv.style.cursor=(!n&&!state.focus&&hitProject(mx,my))?'pointer':'';
  if(id!==state.hover){state.hover=id;schedule()}
  if(n){tip.style.display='block';tip.style.left=(mx+16)+'px';tip.style.top=(my+16)+'px';
    tip.innerHTML='<b>'+escapeHtml(n.title)+'</b><br><span>'+escapeHtml(n.project)+' · '+escapeHtml(n.tipo||n.kind)+(n.data?' · '+escapeHtml(n.data):'')+'</span>'}
  else tip.style.display='none';
});
cv.addEventListener('pointerup',ev=>{
  cv.classList.remove('drag');
  if(dragN&&!moved)select(dragN.id);
  else if(!dragN&&!moved){const r=cv.getBoundingClientRect(),hp=state.focus?null:hitProject(ev.clientX-r.left,ev.clientY-r.top);if(hp)focusProject(hp);else select(null)}
  dragN=null;pan=null;down=null;saveCam();schedule();
});
cv.addEventListener('pointerleave',()=>{tip.style.display='none';if(state.hover){state.hover=null;schedule()}});
cv.addEventListener('dblclick',ev=>{const r=cv.getBoundingClientRect();const n=pick(ev.clientX-r.left,ev.clientY-r.top);if(n)openNote(n.id)});
cv.addEventListener('wheel',ev=>{
  ev.preventDefault();
  const r=cv.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;
  const w={x:wx(mx),y:wy(my)};
  const k=Math.max(0.12,Math.min(5,cam.k*Math.pow(1.0015,-ev.deltaY)));
  userCam=true;cam.k=k;cam.x=(mx-W/2)/k-w.x;cam.y=(my-H/2)/k-w.y;saveCam();schedule();
},{passive:false});
function escapeHtml(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}

/* ---------- seleção e painel ---------- */
const EDGE_PT={links_to:'Cita',related_to:'Semelhante',supersedes:'Substitui',extends:'Estende',contradicts:'Contradiz',implements:'Implementa',references:'Referencia'};
function select(id){
  state.sel=id||null;
  const app=document.getElementById('app');
  if(!id){app.classList.remove('sel');if(state.local)build();schedule();return}
  const n=byId.get(id);if(!n)return;
  document.getElementById('rt').textContent=n.title;
  const rm=document.getElementById('rm');rm.innerHTML='';
  const dot=document.createElement('i');dot.style.background=COLORS[n.project]||'#8a97b2';rm.appendChild(dot);
  const deg=(ADJ.get(id)||[]).length;
  rm.appendChild(document.createTextNode(n.project+(n.data?' · '+n.data:'')+' · '+deg+' conexões'));
  const rc=document.getElementById('rc');rc.innerHTML='';
  const tag=(t,c)=>{const s=document.createElement('span');s.className='tag'+(c?' '+c:'');s.textContent=t;rc.appendChild(s)};
  tag(n.kind==='tarefa'?('Tarefa · '+n.tipo+(n.prio?' · '+n.prio:'')):(n.tipo||n.kind),'kind');
  if(n.sens==='alta')tag('Sensível','warn');
  if(n.inactive)tag('Substituída');
  const rel=(ADJ.get(id)||[]).slice().sort((a,b)=>b.e.score-a.e.score);
  const box=document.getElementById('rn');box.innerHTML='';
  document.getElementById('rs').style.display=rel.length?'block':'none';
  for(const a of rel.slice(0,12)){
    const o=byId.get(a.other);if(!o)continue;
    const b=document.createElement('button');b.className='nb';
    b.appendChild(document.createTextNode(o.title));
    const sm=document.createElement('small');
    const d2=document.createElement('i');d2.style.background=COLORS[o.project]||'#8a97b2';sm.appendChild(d2);
    const lab=EDGE_PT[a.e.type]||a.e.type;
    sm.appendChild(document.createTextNode(lab+(a.e.type==='related_to'?' '+a.e.score.toFixed(2).replace('.',','):'')+' · '+o.project));
    b.appendChild(sm);
    b.onclick=()=>{select(o.id);flyTo(o.x,o.y,Math.max(cam.k,1.1))};
    box.appendChild(b);
  }
  document.getElementById('open').onclick=()=>openNote(id);
  app.classList.add('sel');
  if(state.local)build();
  schedule();
}
function openNote(id){const n=byId.get(id);const target=n&&n.origin?n.origin:id;try{window.webkit.messageHandlers.sb.postMessage(String(target))}catch(e){}}
function flyTo(x,y,k,ms=280){
  tween={x0:cam.x,y0:cam.y,k0:cam.k,x:-x,y:-y,k:k||cam.k,t0:performance.now(),ms};
  schedule();
}

/* ---------- câmera ---------- */
function fit(animate){
  if(!vis.nodes.length)return;
  /* enquadra pelos percentis 3-97%: nós isolados na periferia não encolhem o mapa (continuam acessíveis com pan) */
  const pct=(arr,q)=>{const a=arr.slice().sort((x,y)=>x-y);return a[Math.min(a.length-1,Math.max(0,Math.round(q*(a.length-1))))]};
  const lo=vis.nodes.length>40?0.03:0,hi=1-lo;
  const xs=vis.nodes.map(n=>n.x),ys=vis.nodes.map(n=>n.y);
  const minx=pct(xs,lo),maxx=pct(xs,hi),miny=pct(ys,lo),maxy=pct(ys,hi);
  const bw=Math.max(80,maxx-minx),bh=Math.max(80,maxy-miny);
  const padL=48,padR=48,padTop=56,padBot=48;
  const k=Math.max(0.12,Math.min(2.4,Math.min((W-padL-padR)/bw,(H-padTop-padBot)/bh)));
  const cx=(minx+maxx)/2,cy=(miny+maxy)/2;
  const tx=(padL+(W-padL-padR)/2-W/2)/k-cx,ty=(padTop+(H-padTop-padBot)/2-H/2)/k-cy;
  if(animate!==false){tween={x0:cam.x,y0:cam.y,k0:cam.k,x:tx,y:ty,k,t0:performance.now(),ms:300};schedule()}
  else{cam.x=tx;cam.y=ty;cam.k=k;schedule()}
  saveCam();
}
function saveCam(){try{localStorage.setItem('sb.cam3.'+SIG,JSON.stringify(cam))}catch(e){}}
function loadCam(){try{const c=JSON.parse(localStorage.getItem('sb.cam3.'+SIG)||'null');if(c&&isFinite(c.x)&&isFinite(c.y)&&c.k>0){cam.x=c.x;cam.y=c.y;cam.k=c.k;return true}}catch(e){}return false}

/* ---------- controles ---------- */
function buildPanels(){
  const pl=document.getElementById('plist');pl.innerHTML='';
  for(const p of projects){
    const b=document.createElement('button');b.className='prj'+(state.projects.has(p)?'':' off');
    const d=document.createElement('span');d.className='box';d.style.borderColor=COLORS[p]||'#8a97b2';d.style.color=COLORS[p]||'#8a97b2';
    const t=document.createElement('span');t.className='t';t.textContent=p;
    const n=document.createElement('span');n.className='n';n.textContent=projCount[p];
    b.append(d,t,n);
    b.onclick=()=>{state.projects.has(p)?state.projects.delete(p):state.projects.add(p);buildPanels();build()};
    b.ondblclick=()=>focusProject(p);
    pl.appendChild(b);
  }
  const gc=document.getElementById('groups');gc.innerHTML='';
  for(const g of ['k','m','t','r']){
    let n=0;for(const x of N){if((KG[x.kind]||'r')===g&&state.projects.has(x.project))n++}
    const b=document.createElement('button');b.className='chip'+(state.groups.has(g)?' on':'');
    b.textContent=GROUP_LABEL[g];const s=document.createElement('span');s.className='n';s.textContent=n;b.appendChild(s);
    b.onclick=()=>{state.groups.has(g)?state.groups.delete(g):state.groups.add(g);buildPanels();build()};
    gc.appendChild(b);
  }
}
document.getElementById('fit').onclick=()=>fit();
document.getElementById('allp').onclick=()=>{state.projects=new Set(projects);buildPanels();build()};
document.getElementById('nonep').onclick=()=>{state.projects=new Set();buildPanels();build()};
/* ---------- foco em um projeto: aproxima e fica só nas notas dele ---------- */
let focusPrev=null,pillRects=[];
function focusProject(p){
  if(!p||state.focus===p)return;
  if(!state.focus)focusPrev={projects:new Set(state.projects),cam:{x:cam.x,y:cam.y,k:cam.k}};
  state.focus=p;state.projects=new Set([p]);
  if(state.sel)select(null);
  document.getElementById('crumb').classList.add('show');document.getElementById('crumbn').textContent=p;
  buildPanels();build();userCam=true;fit(true);
}
function exitFocus(){
  if(!state.focus)return;
  const prev=focusPrev;focusPrev=null;state.focus=null;
  state.projects=prev?prev.projects:new Set(projects);
  document.getElementById('crumb').classList.remove('show');
  buildPanels();build();
  if(prev){tween={x0:cam.x,y0:cam.y,k0:cam.k,x:prev.cam.x,y:prev.cam.y,k:prev.cam.k,t0:performance.now(),ms:320};schedule()}else fit(true);
}
function pointInPoly(x,y,pts){let ins=false;for(let i=0,j=pts.length-1;i<pts.length;j=i++){
  const xi=pts[i][0],yi=pts[i][1],xj=pts[j][0],yj=pts[j][1];
  if(((yi>y)!==(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi))ins=!ins}return ins}
function hitProject(mx,my){
  for(const r of pillRects)if(mx>=r[0]&&mx<=r[0]+r[2]&&my>=r[1]&&my<=r[1]+r[3])return r[4];
  if(!hulls)hulls=computeHulls();
  let best=null,ba=1e18;
  for(const h of hulls){const pts=h.h.map(q=>[sx(q[0]),sy(q[1])]);
    if(pointInPoly(mx,my,pts)){let a=0;for(let i=0;i<pts.length;i++){const j=(i+1)%pts.length;a+=pts[i][0]*pts[j][1]-pts[j][0]*pts[i][1]}a=Math.abs(a/2);
      if(a<ba){ba=a;best=h.p}}}
  return best;
}
document.getElementById('cback').onclick=()=>exitFocus();
function setMode(m){
  state.cross=m==='cross';state.isolated=m==='iso';
  if(m==='local'){if(!state.local)state.local=1}else state.local=0;
  state.mode=m;
  for(const k of ['all','cross','local','iso'])document.getElementById('m-'+k).classList.toggle('on',k===m);
  document.getElementById('hops').classList.toggle('show',m==='local');
  document.getElementById('h1').classList.toggle('on',state.local!==2);
  document.getElementById('h2').classList.toggle('on',state.local===2);
  build();if(m==='local')fit();
}
for(const k of ['all','cross','local','iso'])document.getElementById('m-'+k).onclick=()=>setMode(k);
document.getElementById('h1').onclick=()=>{state.local=1;setMode('local')};
document.getElementById('h2').onclick=()=>{state.local=2;setMode('local')};
document.getElementById('nbh').onclick=()=>{if(state.sel){setMode('local')}};
document.getElementById('ftog').onclick=()=>document.getElementById('app').classList.toggle('fo');
document.getElementById('zin').onclick=()=>zoomBy(1.25);
document.getElementById('zout').onclick=()=>zoomBy(1/1.25);
document.getElementById('reset').onclick=()=>{if(state.focus)exitFocus();state.projects=new Set(projects);state.groups=new Set(['k','m','t']);state.tipo='';state.min=0.30;state.q='';
  document.getElementById('q').value='';document.getElementById('tipo').value='';document.getElementById('min').value='0.30';document.getElementById('sv').textContent='0.30';
  buildPanels();setMode('all');fit()};
document.getElementById('min').oninput=ev=>{state.min=+ev.target.value;document.getElementById('sv').textContent=state.min.toFixed(2);build()};
function buildLegend(){
  const present=new Set(DATA.edges.map(e=>e.type));
  const names={supersedes:['Substitui','--kind','dashed'],extends:['Estende','--ok','solid'],contradicts:['Contradiz','--err','solid'],implements:['Implementa','--warn','solid'],references:['Referencia','--mut','dotted']};
  const leg=document.querySelector('.leg');
  for(const [t,[label,v,style]] of Object.entries(names)){
    if(!present.has(t))continue;
    const sp=document.createElement('span');const i=document.createElement('i');
    i.style.borderTop='2px '+style+' var('+v+')';sp.appendChild(i);sp.appendChild(document.createTextNode(label));
    leg.insertBefore(sp,leg.lastElementChild);
  }
}
function buildTipos(){
  const sel=document.getElementById('tipo'),count={};
  for(const n of N){if(n.tipo)count[n.tipo]=(count[n.tipo]||0)+1}
  sel.innerHTML='';
  const zero=document.createElement('option');zero.value='';zero.textContent='Todos os tipos';sel.appendChild(zero);
  for(const t of Object.keys(count).sort((a,b)=>count[b]-count[a]||a.localeCompare(b))){
    const o=document.createElement('option');o.value=t;o.textContent=t+' ('+count[t]+')';sel.appendChild(o);
  }
  sel.value=state.tipo;
}
document.getElementById('tipo').onchange=ev=>{state.tipo=ev.target.value;build();
  clearTimeout(qtimer);qtimer=setTimeout(()=>fit(),200)};
let qtimer=0;
document.getElementById('q').oninput=ev=>{state.q=ev.target.value;build();
  clearTimeout(qtimer);qtimer=setTimeout(()=>{if(state.q.trim().length>=2)fit()},200)};
document.getElementById('q').onkeydown=ev=>{if(ev.key==='Enter'){const n=vis.nodes[0];if(n){select(n.id);flyTo(n.x,n.y,Math.max(cam.k,1.2))}}};
window.addEventListener('keydown',ev=>{
  if(ev.target.tagName==='INPUT')return;
  if(ev.key==='f'||ev.key==='F')fit();
  else if(ev.key==='Escape'){if(state.focus)exitFocus();else select(null);document.getElementById('q').blur()}
  else if(ev.key==='+'||ev.key==='=')zoomBy(1.2);
  else if(ev.key==='-')zoomBy(1/1.2);
  else if(ev.key==='0'){cam.k=1;cam.x=0;cam.y=0;schedule()}
});
function zoomBy(f){cam.k=Math.max(0.12,Math.min(5,cam.k*f));schedule();saveCam()}
let userCam=false;
function resize(){W=cv.clientWidth;H=cv.clientHeight;dpr=window.devicePixelRatio||1;cv.width=W*dpr;cv.height=H*dpr;
  if(!userCam&&W>0&&H>0&&vis.nodes.length)fit(false);else schedule()}
new ResizeObserver(resize).observe(cv);
window.sbSetDark=on=>{document.body.classList.toggle('dark',!!on);schedule()};
window.sbSetProject=p=>{if(p&&projects.includes(p)){focusProject(p)}else{if(state.focus)exitFocus();state.projects=new Set(projects);buildPanels();build();fit(true)}};
window.sbRedraw=build;
window.sbSelect=id=>select(id);

buildTipos();buildLegend();buildPanels();resize();build();
if(!START_PROJECT&&loadCam()){userCam=true;schedule()}else fit(false);
if(START_PROJECT&&projects.includes(START_PROJECT))focusProject(START_PROJECT);
</script>"""


MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def fmt_date(s):
    """2026-11-17 -> 17 nov 2026 (cai de volta no texto original se não for uma data ISO)."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s or "")
    if not m:
        return s or ""
    return f"{int(m.group(3))} {MESES[int(m.group(2)) - 1]} {m.group(1)}"


def ago(seconds):
    if seconds < 60:
        return "agora"
    m = int(seconds // 60)
    if m < 60:
        return f"há {m} min"
    h = m // 60
    return f"há {h} h" if h < 48 else f"há {h // 24} dias"


class Win(Adw.ApplicationWindow):
    SCOPES = (("projeto", "Este projeto"), ("todos", "Todos"), ("outros", "Outros projetos"))

    def __init__(self, app):
        super().__init__(application=app, title="SecondBrain", default_width=1360, default_height=860)
        self.add_css_class("sb-win")
        self.c = xmem.connect()
        self.style = Adw.StyleManager.get_default()
        self.dark = self.style.get_dark()
        self.project = None
        self.scope = "projeto"
        self.include_inactive = False
        self.indexed_at = None
        self.total_notes = 0
        self.cur_id = None
        self.wikimap = {}
        self.colors = {}
        self.graph_sig = None
        self.css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.apply_css()
        self.style.connect("notify::dark", self.on_theme)
        self.build_ui()
        self.refresh_all()
        threading.Thread(target=self.bg_index, daemon=True).start()
        GLib.timeout_add_seconds(30, self.tick_footer)

    def apply_css(self):
        css = theme.gtk_css(self.dark)
        try:
            self.css.load_from_string(css)
        except AttributeError:  # GTK < 4.12
            self.css.load_from_data(css.encode("utf-8"))

    # ------------------------------------------------------------ UI
    def build_ui(self):
        split = Adw.OverlaySplitView(sidebar_width_fraction=0.18, min_sidebar_width=236, max_sidebar_width=300)
        split.set_sidebar(self.build_sidebar())
        tv = Adw.ToolbarView()
        hb = Adw.HeaderBar(show_title=False)
        rb = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Reindexar vaults")
        rb.connect("clicked", lambda *_: threading.Thread(target=self.bg_index, daemon=True).start())
        hb.pack_end(rb)
        tv.add_top_bar(hb)
        self.stack = Adw.ViewStack()
        self.stack.add_named(self.build_notes_page(), "notas")
        self.graph = self.make_webview(js=True)
        self.graph.get_user_content_manager().register_script_message_handler("sb")
        self.graph.get_user_content_manager().connect("script-message-received::sb", self.on_graph_click)
        self.stack.add_named(self.graph, "grafo")
        self.board_page = self.make_webview(js=True)
        self.board_loaded = False
        self.board_page.get_user_content_manager().register_script_message_handler("bd")
        self.board_page.get_user_content_manager().connect("script-message-received::bd", self.on_board_msg)
        self.stack.add_named(self.board_page, "quadro")
        self.stack.connect("notify::visible-child-name", self.sync_nav)
        tv.set_content(self.stack)
        split.set_content(tv)
        self.set_content(split)

    def build_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18, css_classes=["sb-side"], vexpand=True)
        brand = Gtk.Box(spacing=10, margin_top=20, margin_start=24, margin_end=16)
        brand.append(Gtk.Image(icon_name=APP_ID, pixel_size=28))
        brand.append(Gtk.Label(label="SecondBrain", xalign=0, css_classes=["sb-brand"]))
        box.append(brand)
        self.nav = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, css_classes=["sb-list"], margin_start=12, margin_end=12)
        for page, label, icon in (("notas", "Notas", "text-x-generic-symbolic"),
                                  ("grafo", "Grafo", "network-workgroup-symbolic"),
                                  ("quadro", "Quadro", "view-list-symbolic")):
            row = Gtk.ListBoxRow()
            line = Gtk.Box(spacing=12)
            line.append(Gtk.Image(icon_name=icon))
            line.append(Gtk.Label(label=label, xalign=0))
            row.set_child(line)
            row.page = page
            self.nav.append(row)
        self.nav.connect("row-selected", self.on_nav)
        box.append(self.nav)
        box.append(Gtk.Label(label="Projetos", xalign=0, css_classes=["sb-section"], margin_start=24))
        self.plist = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, css_classes=["sb-list"], margin_start=12, margin_end=12)
        self.plist.connect("row-selected", self.on_project)
        box.append(Gtk.ScrolledWindow(child=self.plist, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER))
        self.status = Gtk.Label(xalign=0, css_classes=["sb-foot"], margin_start=24, margin_bottom=16, margin_end=16,
                                ellipsize=Pango.EllipsizeMode.END)
        box.append(self.status)
        self.nav.select_row(self.nav.get_row_at_index(0))
        return box

    def build_notes_page(self):
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, position=400, shrink_start_child=False, shrink_end_child=False)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, css_classes=["sb-column"], width_request=360)
        self.entry = Gtk.SearchEntry(placeholder_text="Buscar em todas as notas…", css_classes=["sb-search"],
                                     margin_top=20, margin_start=20, margin_end=20)
        self.entry.connect("search-changed", lambda *_: self.do_search())
        col.append(self.entry)
        seg = Gtk.Box(css_classes=["sb-seg"], homogeneous=True, margin_start=20, margin_end=20)
        first = None
        for key, label in self.SCOPES:
            b = Gtk.ToggleButton(label=label)
            if first is None:
                first = b
                b.set_active(True)
            else:
                b.set_group(first)
            b.connect("toggled", self.on_scope, key)
            seg.append(b)
        col.append(seg)
        row = Gtk.Box(spacing=8, margin_start=20, margin_end=20)
        self.filter_btn = Gtk.MenuButton(label="Filtros", css_classes=["sb-filter"], tooltip_text="Filtros da busca")
        pop = Gtk.Popover()
        self.inact = Gtk.CheckButton(label="Incluir notas substituídas", margin_top=8, margin_bottom=8, margin_start=10, margin_end=10)
        self.inact.connect("toggled", self.on_inactive)
        pop.set_child(self.inact)
        self.filter_btn.set_popover(pop)
        row.append(self.filter_btn)
        col.append(row)
        self.count_line = Gtk.Label(xalign=0, css_classes=["sb-count-line"], margin_start=20, margin_end=20)
        col.append(self.count_line)
        self.results = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, css_classes=["sb-cards"])
        self.results.connect("row-selected", self.on_result)
        col.append(Gtk.ScrolledWindow(child=self.results, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER))
        paned.set_start_child(col)
        self.reader = self.make_webview(js=False)
        paned.set_end_child(self.reader)
        self.show_reader_empty()
        return paned

    def show_reader_empty(self):
        msg = ('<div class="page" style="margin-top:22vh;text-align:center"><h1 style="font-size:20px">Escolha uma nota</h1>'
               '<p style="color:var(--sub0);font-size:14px">Use a busca ou clique num resultado para ler aqui.</p></div>')
        self.reader.load_html(f'<!doctype html><meta charset="utf-8"><style>{theme.reader_css(self.dark)}</style><body>{msg}</body>', "sb://reader/")

    def make_webview(self, js):
        wv = WebKit.WebView(vexpand=True, hexpand=True)
        st = wv.get_settings()
        st.set_enable_javascript(js)
        st.set_auto_load_images(False)
        st.set_enable_developer_extras(False)
        wv.connect("decide-policy", self.on_policy)
        return wv

    # ------------------------------------------------------------ navegação
    def on_nav(self, _lb, row):
        if row is not None and hasattr(self, "stack"):  # a barra lateral nasce antes das páginas
            self.stack.set_visible_child_name(row.page)

    def sync_nav(self, *_):
        name = self.stack.get_visible_child_name()
        row = self.nav.get_selected_row()
        if row is not None and getattr(row, "page", None) == name:
            return
        for i in range(3):
            r = self.nav.get_row_at_index(i)
            if r is not None and r.page == name:
                self.nav.select_row(r)
                break

    def on_scope(self, btn, key):
        if btn.get_active():
            self.scope = key
            self.do_search()

    def on_inactive(self, btn):
        self.include_inactive = btn.get_active()
        self.filter_btn.set_label("Filtros · 1" if self.include_inactive else "Filtros")
        self.do_search()

    def tick_footer(self):
        self.update_footer()
        return True

    def update_footer(self):
        if self.indexed_at is None:
            self.status.set_text(f"{self.total_notes} notas")
        else:
            self.status.set_text(f"Índice atualizado {ago(time.time() - self.indexed_at)}")
        self.status.set_tooltip_text(f"{self.total_notes} notas · {xmem.DB_PATH}")

    # ------------------------------------------------------------ dados
    def bg_index(self):
        GLib.idle_add(self.status.set_text, "Indexando vaults…")
        try:
            xmem.index(quiet=True)
        except Exception as e:  # noqa: BLE001
            GLib.idle_add(self.status.set_text, f"Falha ao indexar: {e}")
            return
        self.indexed_at = time.time()
        GLib.idle_add(self.refresh_all)

    def project_row(self, p):
        """Duas linhas quando há o que dizer (sensível, parados): o nome do projeto nunca perde espaço para selo."""
        row = Gtk.ListBoxRow()
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, margin_top=6, margin_bottom=6)
        line = Gtk.Box(spacing=10)
        dot = Gtk.Label(use_markup=True)
        dot.set_markup(f'<span foreground="{self.colors[p["project"]]}">●</span>')
        line.append(dot)
        line.append(Gtk.Label(label=p["project"], xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END))
        line.append(Gtk.Label(label=str(p["n"]), css_classes=["sb-count"]))
        outer.append(line)
        if p["sens"] == "alta" or p["stale"]:
            sub = Gtk.Box(spacing=8, margin_start=22)
            if p["sens"] == "alta":
                sub.append(Gtk.Label(label="sensível", css_classes=["sb-badge"], valign=Gtk.Align.CENTER,
                                     tooltip_text="Sensibilidade alta: outros projetos só veem o título"))
            if p["stale"]:
                sub.append(Gtk.Label(label=f"{p['stale']} parados", css_classes=["sb-warn"], tooltip_text="Itens em aberto há mais de 14 dias"))
            outer.append(sub)
        row.set_child(outer)
        row.proj = p["project"]
        return row

    def refresh_all(self):
        self.c = xmem.connect()
        projs = xmem.projects_summary(self.c)
        self.colors = {p["project"]: PALETTE[i % len(PALETTE)] for i, p in enumerate(projs)}
        self.total_notes = sum(p["n"] for p in projs)
        keep = self.project
        self.plist.remove_all()
        allrow = Gtk.ListBoxRow()
        line = Gtk.Box(spacing=10)
        line.append(Gtk.Label(label="Todos os projetos", xalign=0, hexpand=True))
        line.append(Gtk.Label(label=str(self.total_notes), css_classes=["sb-count"]))
        allrow.set_child(line)
        allrow.proj = None
        self.plist.append(allrow)
        for p in projs:
            self.plist.append(self.project_row(p))
        sel = allrow
        for i in range(1, len(projs) + 1):
            r = self.plist.get_row_at_index(i)
            if keep and r.proj == keep:
                sel = r
        self.plist.select_row(sel)
        self.do_search()
        self.refresh_graph()
        self.refresh_board()
        self.update_footer()

    def on_project(self, _lb, row):
        self.project = getattr(row, "proj", None) if row else None
        self.do_search()
        self.refresh_board()
        self.graph_project_filter()

    def graph_project_filter(self):
        """Filtra o grafo pelo projeto da barra lateral sem recarregar a página (câmera e filtros ficam)."""
        js = f"window.sbSetProject&&window.sbSetProject({json.dumps(self.project)});"
        try:
            self.graph.evaluate_javascript(js, -1, None, None, None, None, None)
        except Exception:  # noqa: BLE001
            self.refresh_graph(force=True)

    def result_row(self, r, snip):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=12, margin_bottom=12, margin_start=14, margin_end=14)
        box.append(Gtk.Label(label=r["title"], xalign=0, wrap=True, lines=2, ellipsize=Pango.EllipsizeMode.END, css_classes=["sb-title"]))
        meta = Gtk.Box(spacing=8)
        dot = Gtk.Label(use_markup=True)
        dot.set_markup(f'<span foreground="{self.colors.get(r["project"], "#8087a2")}">●</span>')
        meta.append(dot)
        parts = [r["project"], r["tipo"] or r["kind"]]
        if r["data"]:
            parts.append(fmt_date(r["data"]))
        meta.append(Gtk.Label(label=" · ".join(parts), xalign=0, css_classes=["sb-meta"], ellipsize=Pango.EllipsizeMode.END))
        if r["sens"] == "alta":
            meta.append(Gtk.Label(label="Sensível", css_classes=["sb-sens"], valign=Gtk.Align.CENTER))
        box.append(meta)
        if snip:
            box.append(Gtk.Label(label=snip, xalign=0, wrap=True, lines=2, ellipsize=Pango.EllipsizeMode.END, css_classes=["sb-snip"]))
        row = Gtk.ListBoxRow(child=box)
        row.nid = r["id"]
        return row

    def do_search(self):
        q = self.entry.get_text().strip()
        self.results.remove_all()
        rows = []
        outros = self.scope == "outros"
        proj = self.project if self.scope == "projeto" else None
        if q:
            hits = xmem.hybrid(self.c, q, k=40, project=proj, exclude_project=self.project if outros else None,
                               include_inactive=self.include_inactive)
            rows = [(h["row"], xmem.snippet(h["row"]["text"], q, 140)) for h in hits]
        else:
            where, args = ("where project=?", (proj,)) if proj else ("where project!=?", (self.project,)) if outros and self.project else ("", ())
            for r in self.c.execute(f"select * from notes {where} order by data desc, id desc limit 80", args):
                rows.append((r, ""))
        for r, snip in rows:
            self.results.append(self.result_row(r, snip))
        escopo = {"projeto": f"em {self.project}" if self.project else "em todos os projetos", "todos": "em todos os projetos",
                  "outros": f"fora de {self.project}" if self.project else "em todos os projetos"}[self.scope]
        n = len(rows)
        if not rows and q:
            self.count_line.set_text(f"Nada encontrado para “{q}” {escopo}")
        else:
            self.count_line.set_text((f"{n} resultado(s) {escopo}" if q else f"{n} nota(s) recentes {escopo}"))

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

    def refresh_graph(self, force=False):
        """Monta o grafo fora da thread da interface (layout leva alguns segundos na primeira vez)."""
        threading.Thread(target=self._build_graph, args=(force,), daemon=True).start()

    def _build_graph(self, force):
        try:
            c = xmem.connect()
            g = xmem.graph_data(c, None, 0.0)
            lay = xmem.graph_layout(g)
            c.close()
        except Exception as e:  # noqa: BLE001
            GLib.idle_add(self.status.set_text, f"Grafo: {e}")
            return
        GLib.idle_add(self.apply_graph, g, lay, force)

    def apply_graph(self, g, lay, force=False):
        sig = xmem.graph_signature(g)
        if not force and sig == self.graph_sig:
            return
        self.graph_sig = sig
        nodes = []
        for n in g["nodes"]:
            x, y = lay.get(n["id"], (0.0, 0.0))
            nodes.append({"id": n["id"], "project": n["project"], "kind": n["kind"], "title": n["title"],
                          "tipo": n["tipo"], "data": n["data"], "sens": n["sens"], "inactive": n["inactive"],
                          "x": x, "y": y})
        edges = [{"src": e["src"], "dst": e["dst"], "type": e["type"], "score": e["score"], "cross": e["cross"]}
                 for e in g["edges"]]
        try:  # cartões em andamento do quadro: losangos ligados à nota de origem
            import math
            for i, t in enumerate(xmem.active_tasks(self.c)):
                oid = t["nota_id"]
                if oid is None or oid not in lay:
                    continue
                ox, oy = lay[oid]
                ang = i * 2.4
                nid = -(i + 1)
                nodes.append({"id": nid, "project": t["projeto"], "kind": "tarefa", "title": t["titulo"].replace("`", ""), "tipo": t["status"],
                              "data": "", "sens": "normal", "inactive": 0, "origin": oid, "prio": t["prioridade"],
                              "x": ox + 26 * math.cos(ang), "y": oy + 26 * math.sin(ang)})
                edges.append({"src": nid, "dst": oid, "type": "task", "score": 1.0, "cross": False})
        except Exception:  # noqa: BLE001  (o quadro nunca pode impedir o grafo)
            pass
        sig = sig + hashlib.sha1(json.dumps([[n["id"], n["tipo"]] for n in nodes if n["kind"] == "tarefa"]).encode()).hexdigest()[:6]
        data = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False).replace("<", "\\u003c")
        html_ = (GRAPH_HTML.replace("{{THEME}}", graph_theme())
                 .replace("{{DATA}}", data)
                 .replace("{{COLORS}}", json.dumps(self.colors))
                 .replace("{{SIG}}", sig[:12])
                 .replace("{{PROJECT}}", json.dumps(self.project)))
        html_ = html_.replace("<body>", '<body class="dark">' if self.dark else "<body>")
        self.graph.load_html(html_, "sb://graph/")

    def on_theme(self, style_manager, _pspec=None):
        self.dark = style_manager.get_dark()
        self.apply_css()
        self.js(self.board_page, f"window.sbSetDark&&window.sbSetDark({str(self.dark).lower()});")
        try:
            self.graph.evaluate_javascript(f"window.sbSetDark&&window.sbSetDark({str(self.dark).lower()});",
                                          -1, None, None, None, None, None)
        except Exception:  # noqa: BLE001
            pass
        if self.cur_id:
            self.open_note(self.cur_id)
        else:
            self.show_reader_empty()

    def on_graph_click(self, _ucm, value):
        try:
            nid = int(value.to_string())
        except (ValueError, AttributeError):
            return
        self.open_note(nid)
        self.stack.set_visible_child_name("notas")

    # ------------------------------------------------------------ quadro (kanban)
    def board_payload(self):
        cards = board.build(self.c, self.project)
        base = {"project": self.project, "triagem_dias": board.TRIAGE_DAYS}
        if self.project:
            slim = [{k: v for k, v in x.items() if k not in ("sens", "policy")} for x in cards]
            return dict(base, cartoes=slim)
        return dict(base, resumo=board.summary(cards), cartoes=[])

    def refresh_board(self):
        data = json.dumps(self.board_payload(), ensure_ascii=False).replace("<", "\\u003c")
        if self.board_loaded:
            self.js(self.board_page, f"window.sbBoardData&&window.sbBoardData({data});")
            return
        html_ = (board_page.BOARD_HTML.replace("{{THEME}}", graph_theme())
                 .replace("{{COLS}}", json.dumps(board.COLUMNS)).replace("{{HINT}}", json.dumps(board_page.HINTS))
                 .replace("{{COLORS}}", json.dumps(self.colors)).replace("{{DATA}}", data))
        if self.dark:
            html_ = html_.replace("<body>", '<body class="dark">', 1)
        self.board_loaded = True
        self.board_page.load_html(html_, "sb://board/")

    def js(self, view, code):
        try:
            view.evaluate_javascript(code, -1, None, None, None, None, None)
        except Exception:  # noqa: BLE001
            pass

    def board_toast(self, msg):
        self.js(self.board_page, f"window.sbToast&&window.sbToast({json.dumps(msg)});")

    def ask(self, heading, body, ok_label, callback):
        d = Adw.AlertDialog(heading=heading, body=body)
        d.add_response("cancel", "Cancelar")
        d.add_response("ok", ok_label)
        d.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        d.set_default_response("cancel")
        d.set_close_response("cancel")
        d.connect("response", lambda _d, r: callback() if r == "ok" else None)
        d.present(self)

    def board_write(self, project, changes, done_msg):
        """Grava no quadro.md do projeto (backup fora do vault). Vault sensível/versionado pede confirmação."""
        def attempt(confirmo):
            try:
                board.apply_changes(self.c, project, changes, confirmo=confirmo)
            except SystemExit as e:
                msg = str(e)
                if "confirmação explícita" in msg and not confirmo:
                    self.ask(f"Gravar o quadro de {project}?",
                             "Este vault é sensível ou versionado. O arquivo quadro.md será criado ou alterado nele; o anterior ganha backup fora do vault.",
                             "Gravar", lambda: attempt(True))
                else:
                    self.board_toast(msg)
                return
            self.refresh_board()
            self.refresh_graph()
            self.board_toast(done_msg)
        attempt(False)

    def on_board_msg(self, _ucm, value):
        try:
            m = json.loads(value.to_string())
        except (ValueError, AttributeError):
            return
        op, proj = m.get("op"), m.get("project")
        if op == "project":
            for i in range(1, 400):
                r = self.plist.get_row_at_index(i)
                if r is None:
                    break
                if getattr(r, "proj", None) == m.get("name"):
                    self.plist.select_row(r)
                    break
        elif op == "open":
            r = self.c.execute("select id from notes where project=? and rel=?", (proj, m.get("rel"))).fetchone()
            if r:
                self.open_note(r["id"])
        elif op == "move":
            card = next((k for k in board.build(self.c, proj) if k["id"] == m.get("id")), None)
            if card is None:
                self.board_toast("Cartão não encontrado; atualize o quadro.")
                return
            campos = {}
            if "bloqueado_por" in m:
                campos["bloqueado-por"] = m["bloqueado_por"] or ""
            prio = (m.get("prioridade") or "") if "prioridade" in m else None
            ch = board.change_from_card(card, m["col"], prio, None, campos)
            self.board_write(proj, [ch], f"Movido para {board.LABEL.get(m['col'], m['col'])}.")
        elif op == "discard-old":
            days, n = int(m.get("days", board.TRIAGE_DAYS)), int(m.get("n", 0))

            def go():
                cards = board.build(self.c, proj)
                ch = [board.change_from_card(k, "descartado") for k in cards if k["status"] == "triagem" and k["idade_dias"] >= days]
                self.board_write(proj, ch, f"{len(ch)} cartões descartados. As notas de origem não foram alteradas.")
            self.ask(f"Descartar {n} cartões de {proj}?",
                     f"Eles vão para a coluna Descartado do quadro (reversível). As notas de origem ficam intactas e o quadro.md anterior ganha backup.",
                     "Descartar", go)

    def on_policy(self, wv, decision, ptype):
        if ptype != WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            return False
        uri = decision.get_navigation_action().get_request().get_uri()
        if uri.startswith(("sb://reader", "sb://graph", "sb://board", "about:")):
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


def save_window_png(win, path):
    """Captura a janela inteira num PNG (usado só pelo selftest, para conferir o desenho sem tela de apoio)."""
    paintable = Gtk.WidgetPaintable.new(win)
    w, h = win.get_width(), win.get_height()
    snap = Gtk.Snapshot()
    paintable.snapshot(snap, w, h)
    node = snap.to_node()
    if node is None:  # janela ainda não pintou: o selftest não deve falhar por causa da captura
        print("captura: janela ainda sem conteúdo")
        return
    tex = win.get_native().get_renderer().render_texture(node, None)
    tex.save_to_png(path)
    print(f"captura: {path} ({w}x{h})")


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.selftest = "--selftest" in sys.argv

    def do_activate(self):
        Gtk.Window.set_default_icon_name(APP_ID)  # ícone instalado por scripts/install-tools.sh
        win = Win(self)
        win.present()
        if self.selftest:  # fumaça: abre, indexa, fecha sozinho (SB_SELFTEST_MS e SB_SELFTEST_PAGE servem para capturar a tela)
            want = os.environ.get("SB_SELFTEST_NOTE")
            if want:
                def _open():
                    r = win.c.execute("select id from notes where title like ? order by id limit 1", (f"%{want}%",)).fetchone()
                    if r:
                        win.open_note(r["id"])
                    return False
                GLib.timeout_add(3000, _open)
            want_p = os.environ.get("SB_SELFTEST_PROJECT")
            if want_p:
                def _proj():
                    for i in range(1, 400):
                        r = win.plist.get_row_at_index(i)
                        if r is None:
                            break
                        if getattr(r, "proj", None) == want_p:
                            win.plist.select_row(r)
                            break
                    return False
                GLib.timeout_add(2000, _proj)
            page = os.environ.get("SB_SELFTEST_PAGE")
            if page:
                GLib.timeout_add(2500, lambda: win.stack.set_visible_child_name(page) and False)
            js = os.environ.get("SB_SELFTEST_GRAPH_JS")
            if js:
                GLib.timeout_add(int(os.environ.get("SB_SELFTEST_JS_MS", "9000")),
                                 lambda: (win.graph.evaluate_javascript(js, -1, None, None, None, None, None), False)[1])
            bjs = os.environ.get("SB_SELFTEST_BOARD_JS")
            if bjs:
                GLib.timeout_add(int(os.environ.get("SB_SELFTEST_JS_MS", "9000")),
                                 lambda: (win.board_page.evaluate_javascript(bjs, -1, None, None, None, None, None), False)[1])
            shot = os.environ.get("SB_SELFTEST_SHOT")
            if shot:
                GLib.timeout_add(int(os.environ.get("SB_SELFTEST_SHOT_MS", "5000")), lambda: (save_window_png(win, shot), False)[1])
            GLib.timeout_add(int(os.environ.get("SB_SELFTEST_MS", "7000")), lambda: (print("selftest: janela e dados ok"), self.quit()))


if __name__ == "__main__":
    sys.exit(App().run([a for a in sys.argv[:1]]))
