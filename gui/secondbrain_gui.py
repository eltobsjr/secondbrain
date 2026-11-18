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
PALETTE = ["#8aadf4", "#a6da95", "#f5a97f", "#c6a0f6", "#eed49f", "#8bd5ca", "#ed8796", "#f5bde6", "#91d7e3", "#b7bdf8", "#f0c6c6", "#7dc4e4",
           "#e8c07a", "#8fc4a0", "#c99ad9", "#7fb3d5", "#d99a9a", "#a8c98a"]


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


GRAPH_HTML = r"""<!doctype html><meta charset="utf-8"><title>Grafo</title><style>
:root{--bg:#fbfbfd;--fg:#2e3440;--mut:#6b7385;--card:rgba(252,252,254,.92);--bd:#dfe3ec;--ac:#4a6fd8;--halo:#fbfbfd}
body.dark{--bg:#1e2030;--fg:#cad3f5;--mut:#9aa1bd;--card:rgba(36,39,58,.94);--bd:#363a4f;--ac:#8aadf4;--halo:#1e2030}
*{box-sizing:border-box}html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--fg);font:13px/1.4 system-ui,sans-serif}
canvas{display:block;width:100%;height:100%;cursor:grab}canvas.drag{cursor:grabbing}
.panel{position:absolute;background:var(--card);border:1px solid var(--bd);border-radius:14px;box-shadow:0 8px 24px rgba(0,0,0,.07);backdrop-filter:blur(10px)}
#top{top:12px;left:12px;right:12px;display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:6px}
#top input{border:1px solid var(--bd);background:transparent;color:var(--fg);border-radius:9px;padding:5px 9px;font:inherit;width:190px;outline:none}
#top input:focus{border-color:var(--ac)}
#top .sep{width:1px;height:22px;background:var(--bd);margin:0 2px}
#top select{max-width:150px;padding:5px 6px}
.btn{border:1px solid var(--bd);background:transparent;color:var(--fg);border-radius:9px;padding:5px 9px;font:inherit;cursor:pointer;white-space:nowrap}
.btn:hover{border-color:var(--ac);color:var(--ac)}
.btn.on{background:var(--ac);border-color:var(--ac);color:#fff}
.btn.icon{padding:5px 8px}
#stats{padding:0 4px;color:var(--mut);font-size:12px;white-space:nowrap}
#left{left:12px;top:60px;width:200px;padding:9px;max-height:calc(100% - 190px);display:flex;flex-direction:column;gap:6px}
#left h4,#bottom h4{margin:0;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);font-weight:600}
#plist{overflow:auto;display:flex;flex-direction:column;gap:1px;margin:0 -4px}
.prj{display:flex;align-items:center;gap:7px;border:0;background:transparent;color:var(--fg);font:inherit;text-align:left;padding:3px 5px;border-radius:7px;cursor:pointer;opacity:1}
.prj:hover{background:rgba(127,127,127,.10)}
.prj.off{opacity:.32}
.prj .dot{width:9px;height:9px;border-radius:50%;flex:none}
.prj .n{margin-left:auto;color:var(--mut);font-size:11px}
.row2{display:flex;gap:6px}.row2 .btn{flex:1;padding:3px 6px;font-size:12px}
#bottom{left:12px;bottom:12px;padding:8px 10px;display:flex;flex-direction:column;gap:6px;max-width:min(560px,calc(100% - 360px))}
.chips{display:flex;gap:5px;flex-wrap:wrap}
.chip{border:1px solid var(--bd);border-radius:999px;padding:2px 9px;font-size:12px;cursor:pointer;color:var(--fg);background:transparent}
.chip.off{opacity:.4}
.chip .n{color:var(--mut);font-size:11px;margin-left:3px}
.leg{display:flex;gap:12px;flex-wrap:wrap;color:var(--mut);font-size:11px;align-items:center}
.leg i{display:inline-block;width:16px;height:0;border-top:2px solid;margin-right:4px;vertical-align:middle}
#right{right:12px;top:60px;width:308px;max-height:calc(100% - 72px);padding:12px;display:none;flex-direction:column;gap:8px;overflow:auto}
#right.on{display:flex}
#right h3{margin:0;font-size:15px;line-height:1.3}
#right .meta{color:var(--mut);font-size:12px}
#right .meta b{color:var(--fg);font-weight:500}
#right .side{margin-top:4px;border-top:1px solid var(--bd);padding-top:8px}
#right .side h5{margin:0 0 5px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
.nb{display:block;width:100%;text-align:left;border:0;background:transparent;color:var(--fg);font:inherit;padding:3px 4px;border-radius:6px;cursor:pointer;line-height:1.25}
.nb:hover{background:rgba(127,127,127,.10)}
.nb small{color:var(--mut);font-size:11px}
#open{margin-top:auto;width:100%;padding:7px;font-weight:500}
#tip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--bd);border-radius:9px;padding:5px 9px;display:none;max-width:330px;font-size:12px;box-shadow:0 4px 14px rgba(0,0,0,.12);z-index:5}
#tip b{font-weight:600}#tip span{color:var(--mut)}
#empty{position:absolute;inset:0;display:none;align-items:center;justify-content:center;color:var(--mut);font-size:14px;pointer-events:none}
</style><body>
<canvas id="c"></canvas><div id="empty">Nenhuma nota com os filtros atuais</div>
<div id="top" class="panel">
  <input id="q" placeholder="Buscar nota ou projeto…" spellcheck="false">
  <span class="sep"></span>
  <button class="btn icon" id="fit" title="Ajustar à tela (F)">⤢</button>
  <button class="btn" id="cross" title="Mostrar só relações entre projetos diferentes">Entre projetos</button>
  <button class="btn" id="iso" title="Mostrar notas sem nenhuma relação visível">Isoladas</button>
  <button class="btn" id="local" title="Só a vizinhança da nota selecionada (clique alterna 1 salto / 2 saltos)">Local</button>
  <select id="tipo" class="btn" title="Filtrar por tipo de nota"></select>
  <span class="sep"></span>
  <label style="color:var(--mut);display:flex;gap:6px;align-items:center" title="Semelhança mínima das arestas automáticas">
    <input id="min" type="range" min="0.16" max="0.75" step="0.02" value="0.30" style="width:86px"> <span id="sv">0.30</span>
  </label>
  <span id="stats"></span>
</div>
<div id="left" class="panel"><h4>Projetos</h4><div id="plist"></div>
  <div class="row2"><button class="btn" id="allp">Todos</button><button class="btn" id="nonep">Nenhum</button></div></div>
<div id="bottom" class="panel">
  <h4>Camadas</h4><div class="chips" id="groups"></div>
  <div class="leg"><span><i style="border-color:#8a97b2"></i>link</span><span><i style="border-color:#8a97b2;opacity:.45"></i>semelhança</span><span><i style="border-color:#4a6fd8"></i>entre projetos</span><span>duplo clique abre a nota</span></div>
</div>
<div id="right" class="panel"><h3 id="rt"></h3><div class="meta" id="rm"></div><div class="chips" id="rc"></div>
  <div class="side" id="rs" style="display:none"><h5>Relacionadas</h5><div id="rn"></div></div>
  <button class="btn on" id="open">Abrir nota</button></div>
<div id="tip"></div>
<script>
const DATA={{DATA}}, COLORS={{COLORS}}, SIG="{{SIG}}", START_PROJECT={{PROJECT}};
const KG={decisao:'k',feature:'k',rfc:'k',nota:'k',analise:'k',padrao:'k',aprendizado:'k',postmortem:'k',release:'k','visao-geral':'k',
          memory:'m',devtrack:'r',commit:'r',estado:'r',prioridade:'r','claude-md':'r',checklist:'r',projeto:'r'};
const GROUP_LABEL={k:'Conhecimento',m:'Memória',r:'Registro'};
const cv=document.getElementById('c'),ctx=cv.getContext('2d'),tip=document.getElementById('tip');
const N=DATA.nodes.map(n=>Object.assign({},n));
const byId=new Map(N.map(n=>[n.id,n]));
const ADJ=new Map(N.map(n=>[n.id,[]]));
for(const e of DATA.edges){ if(!byId.has(e.src)||!byId.has(e.dst)) continue;
  ADJ.get(e.src).push({e,other:e.dst}); ADJ.get(e.dst).push({e,other:e.src}); }
const projects=[...new Set(N.map(n=>n.project))].sort((a,b)=>a.localeCompare(b));
const projCount={}; N.forEach(n=>{projCount[n.project]=(projCount[n.project]||0)+1});
const state={projects:new Set(projects),groups:new Set(['k','m']),min:0.30,cross:false,isolated:false,q:'',tipo:'',local:0,sel:null,hover:null};
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
  if(dirty){draw();dirty=false}}

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
    shown=state.isolated||q||state.tipo?nodes:nodes.filter(n=>deg.get(n.id));
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
    ctx.beginPath();ctx.arc(sx(n.x),sy(n.y),r,0,6.2832);ctx.fillStyle=COLORS[n.project]||'#8a97b2';ctx.fill();
    if(n.sens==='alta'){ctx.strokeStyle=rgb('#d98a1c',.9);ctx.lineWidth=1.4;ctx.stroke()}
    if(n.inactive){ctx.setLineDash([2,2]);ctx.strokeStyle=bg;ctx.lineWidth=1.2;ctx.stroke();ctx.setLineDash([])}
    if(n.id===sel||n.id===hover){ctx.strokeStyle=getComputedStyle(document.body).color;ctx.lineWidth=2;ctx.beginPath();ctx.arc(sx(n.x),sy(n.y),r+2.5,0,6.2832);ctx.stroke()}
    if(focus&&near.has(n.id)&&n.id!==focus&&n.id!==sel)labels.push(n);
    if(cam.k>=1.8)labels.push(n);
  }
  ctx.globalAlpha=1;
  if(sel){/* rótulo sempre para a selecionada */}
  if(!focus)labels=labels.concat(topHubs());
  if(sel&&byId.has(sel)&&vis.deg.has(sel))labels.push(byId.get(sel));
  if(hover&&byId.has(hover)&&vis.deg.has(hover))labels.push(byId.get(hover));
  drawLabels(labels);
  ctx.font='11px system-ui';ctx.fillStyle=getComputedStyle(document.body).getPropertyValue('--mut');
  ctx.fillText(cam.k<0.3?'Role para aproximar e ver os nomes':'',W-190,H-14);
}
let hubs=null;
function topHubs(){
  if(hubs)return hubs;
  hubs=vis.nodes.slice().sort((a,b)=>(vis.deg.get(b.id)||0)-(vis.deg.get(a.id)||0)).slice(0,22);
  return hubs;
}
function pill(x,y,text,color){
  ctx.font='600 10px system-ui';ctx.textBaseline='middle';
  const w=ctx.measureText(text).width+12,h=17;
  const bg=getComputedStyle(document.body).getPropertyValue('--card').trim()||'rgba(255,255,255,.9)';
  ctx.beginPath();
  if(ctx.roundRect)ctx.roundRect(x-w/2,y-h/2,w,h,8);else ctx.rect(x-w/2,y-h/2,w,h);
  ctx.globalAlpha=.92;ctx.fillStyle=bg;ctx.fill();ctx.globalAlpha=1;
  ctx.strokeStyle=rgb(color,.45);ctx.lineWidth=1;ctx.stroke();
  ctx.textAlign='center';ctx.fillStyle=color;ctx.fillText(text,x,y);
  ctx.textAlign='left';ctx.textBaseline='alphabetic';
  return w;
}
function drawProjectLabels(){
  const placed=[];
  for(const [p,s] of vis.projects){
    if(s.n<3||state.q.trim())continue;
    const name=p.toUpperCase(),x=sx(s.cx),y=sy(s.miny)-16;
    ctx.font='600 10px system-ui';const w=ctx.measureText(name).width+12;
    if(placed.some(r=>Math.abs(x-r[0])<(w+r[1])/2+4&&Math.abs(y-r[2])<20))continue;
    placed.push([x,w,y]);
    pill(x,y,name,COLORS[p]||'#8a97b2');
  }
}
function drawEdges(edges,focus,near){
  const b={at:[],am:[],ct:[],cm:[]};
  for(const e of edges){
    const incident=focus&&(e.src===focus||e.dst===focus);
    if(incident)continue;
    (e.cross?(e.type==='related_to'?b.ct:b.cm):(e.type==='related_to'?b.at:b.am)).push(e);
  }
  const stroke=(arr,color,alpha,width)=>{if(!arr.length)return;ctx.beginPath();
    for(const e of arr){const a=byId.get(e.src),c=byId.get(e.dst);if(!a||!c)continue;ctx.moveTo(sx(a.x),sy(a.y));ctx.lineTo(sx(c.x),sy(c.y))}
    ctx.strokeStyle=color;ctx.globalAlpha=alpha;ctx.lineWidth=width;ctx.stroke();ctx.globalAlpha=1};
  const mut=getComputedStyle(document.body).getPropertyValue('--mut').trim(),ac=getComputedStyle(document.body).getPropertyValue('--ac').trim();
  const faded=(focus&&!near.has(-1))?0.55:1;
  stroke(b.at,mut,0.26*faded,0.9);stroke(b.am,mut,0.50*faded,1.15);
  stroke(b.ct,ac,0.17*faded,0.85);stroke(b.cm,ac,0.55*faded,1.3);
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
  ctx.font='11px system-ui';ctx.textAlign='left';ctx.textBaseline='middle';
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
  if(id!==state.hover){state.hover=id;schedule()}
  if(n){tip.style.display='block';tip.style.left=(mx+16)+'px';tip.style.top=(my+16)+'px';
    tip.innerHTML='<b>'+escapeHtml(n.title)+'</b><br><span>'+escapeHtml(n.project)+' · '+escapeHtml(n.tipo||n.kind)+(n.data?' · '+escapeHtml(n.data):'')+'</span>'}
  else tip.style.display='none';
});
cv.addEventListener('pointerup',ev=>{
  cv.classList.remove('drag');
  if(dragN&&!moved)select(dragN.id);
  else if(!dragN&&!moved)select(null);
  dragN=null;pan=null;down=null;saveCam();schedule();
});
cv.addEventListener('pointerleave',()=>{tip.style.display='none';if(state.hover){state.hover=null;schedule()}});
cv.addEventListener('dblclick',ev=>{const r=cv.getBoundingClientRect();const n=pick(ev.clientX-r.left,ev.clientY-r.top);if(n)openNote(n.id)});
cv.addEventListener('wheel',ev=>{
  ev.preventDefault();
  const r=cv.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;
  const w={x:wx(mx),y:wy(my)};
  const k=Math.max(0.12,Math.min(5,cam.k*Math.pow(1.0015,-ev.deltaY)));
  cam.k=k;cam.x=(mx-W/2)/k-w.x;cam.y=(my-H/2)/k-w.y;saveCam();schedule();
},{passive:false});
function escapeHtml(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}

/* ---------- seleção e painel ---------- */
function select(id){
  state.sel=id||null;
  const p=document.getElementById('right');
  if(!id){p.classList.remove('on');if(state.local)build();schedule();return}
  const n=byId.get(id);if(!n)return;
  document.getElementById('rt').textContent=n.title;
  document.getElementById('rm').innerHTML='<b>'+escapeHtml(n.project)+'</b> · '+escapeHtml(n.tipo||n.kind)+(n.data?' · '+escapeHtml(n.data):'');
  const rc=document.getElementById('rc');rc.innerHTML='';
  const chip=(t)=>{const s=document.createElement('span');s.className='chip';s.textContent=t;rc.appendChild(s)};
  if(n.sens==='alta')chip('🔒 sensibilidade alta');
  if(n.inactive)chip('substituída');
  if(n.kind)chip(n.kind);
  const rel=(ADJ.get(id)||[]).slice().sort((a,b)=>b.e.score-a.e.score);
  const box=document.getElementById('rn');box.innerHTML='';
  document.getElementById('rs').style.display=rel.length?'block':'none';
  for(const a of rel.slice(0,12)){
    const o=byId.get(a.other);if(!o)continue;
    const b=document.createElement('button');b.className='nb';
    b.textContent=o.title;const sm=document.createElement('small');
    sm.textContent='  '+o.project+' · '+(a.e.type==='related_to'?('semelhança '+a.e.score.toFixed(2)):a.e.type);b.appendChild(sm);
    b.onclick=()=>{select(o.id);flyTo(o.x,o.y,Math.max(cam.k,1.1))};
    box.appendChild(b);
  }
  document.getElementById('open').onclick=()=>openNote(id);
  p.classList.add('on');
  if(state.local)build();
  schedule();
}
function openNote(id){try{window.webkit.messageHandlers.sb.postMessage(String(id))}catch(e){}}
function flyTo(x,y,k,ms=280){
  tween={x0:cam.x,y0:cam.y,k0:cam.k,x:-x,y:-y,k:k||cam.k,t0:performance.now(),ms};
  schedule();
}

/* ---------- câmera ---------- */
function fit(animate){
  if(!vis.nodes.length)return;
  let minx=1e9,maxx=-1e9,miny=1e9,maxy=-1e9;
  for(const n of vis.nodes){minx=Math.min(minx,n.x);maxx=Math.max(maxx,n.x);miny=Math.min(miny,n.y);maxy=Math.max(maxy,n.y)}
  const bw=Math.max(80,maxx-minx),bh=Math.max(80,maxy-miny);
  const padL=document.getElementById('left').offsetWidth+70;
  const padR=document.getElementById('right').classList.contains('on')?318:36;
  const padTop=70,padBot=110;
  const k=Math.max(0.12,Math.min(2.4,Math.min((W-padL-padR)/bw,(H-padTop-padBot)/bh)));
  const cx=(minx+maxx)/2,cy=(miny+maxy)/2;
  const tx=(padL+(W-padL-padR)/2-W/2)/k-cx,ty=(padTop+(H-padTop-padBot)/2-H/2)/k-cy;
  if(animate!==false){tween={x0:cam.x,y0:cam.y,k0:cam.k,x:tx,y:ty,k,t0:performance.now(),ms:300};schedule()}
  else{cam.x=tx;cam.y=ty;cam.k=k;schedule()}
  saveCam();
}
function saveCam(){try{localStorage.setItem('sb.cam.'+SIG,JSON.stringify(cam))}catch(e){}}
function loadCam(){try{const c=JSON.parse(localStorage.getItem('sb.cam.'+SIG)||'null');if(c&&isFinite(c.x)&&isFinite(c.y)&&c.k>0){cam.x=c.x;cam.y=c.y;cam.k=c.k;return true}}catch(e){}return false}

/* ---------- controles ---------- */
function buildPanels(){
  const pl=document.getElementById('plist');pl.innerHTML='';
  for(const p of projects){
    const b=document.createElement('button');b.className='prj'+(state.projects.has(p)?'':' off');
    const d=document.createElement('span');d.className='dot';d.style.background=COLORS[p]||'#8a97b2';
    const t=document.createElement('span');t.textContent=p;
    const n=document.createElement('span');n.className='n';n.textContent=projCount[p];
    b.append(d,t,n);
    b.onclick=()=>{state.projects.has(p)?state.projects.delete(p):state.projects.add(p);buildPanels();build()};
    b.ondblclick=()=>{state.projects=new Set([p]);buildPanels();build();fit()};
    pl.appendChild(b);
  }
  const gc=document.getElementById('groups');gc.innerHTML='';
  for(const g of ['k','m','r']){
    let n=0;for(const x of N){if((KG[x.kind]||'r')===g&&state.projects.has(x.project))n++}
    const b=document.createElement('button');b.className='chip'+(state.groups.has(g)?'':' off');
    b.textContent=GROUP_LABEL[g];const s=document.createElement('span');s.className='n';s.textContent=n;b.appendChild(s);
    b.onclick=()=>{state.groups.has(g)?state.groups.delete(g):state.groups.add(g);buildPanels();build()};
    gc.appendChild(b);
  }
}
document.getElementById('fit').onclick=()=>fit();
document.getElementById('allp').onclick=()=>{state.projects=new Set(projects);buildPanels();build()};
document.getElementById('nonep').onclick=()=>{state.projects=new Set();buildPanels();build()};
document.getElementById('cross').onclick=ev=>{state.cross=!state.cross;ev.currentTarget.classList.toggle('on',state.cross);build()};
document.getElementById('iso').onclick=ev=>{state.isolated=!state.isolated;ev.currentTarget.classList.toggle('on',state.isolated);build()};
document.getElementById('min').oninput=ev=>{state.min=+ev.target.value;document.getElementById('sv').textContent=state.min.toFixed(2);build()};
function buildTipos(){
  const sel=document.getElementById('tipo'),count={};
  for(const n of N){if(n.tipo)count[n.tipo]=(count[n.tipo]||0)+1}
  sel.innerHTML='';
  const zero=document.createElement('option');zero.value='';zero.textContent='Tipo: todos';sel.appendChild(zero);
  for(const t of Object.keys(count).sort((a,b)=>count[b]-count[a]||a.localeCompare(b))){
    const o=document.createElement('option');o.value=t;o.textContent=t+' ('+count[t]+')';sel.appendChild(o);
  }
  sel.value=state.tipo;
}
document.getElementById('tipo').onchange=ev=>{state.tipo=ev.target.value;build();
  clearTimeout(qtimer);qtimer=setTimeout(()=>fit(),200)};
document.getElementById('local').onclick=ev=>{
  state.local=state.local===0?1:(state.local===1?2:0);
  const b=ev.currentTarget;
  b.classList.toggle('on',state.local>0);
  b.textContent=state.local===0?'Local':('Local '+state.local+' salto'+(state.local>1?'s':''));
  b.title=state.local?(state.local===1?'Vizinhos diretos da nota selecionada':'Até 2 saltos da nota selecionada'):'Só a vizinhança da nota selecionada (clique alterna 1 salto / 2 saltos)';
  build();if(state.local)fit();
};
let qtimer=0;
document.getElementById('q').oninput=ev=>{state.q=ev.target.value;build();
  clearTimeout(qtimer);qtimer=setTimeout(()=>{if(state.q.trim().length>=2)fit()},200)};
document.getElementById('q').onkeydown=ev=>{if(ev.key==='Enter'){const n=vis.nodes[0];if(n){select(n.id);flyTo(n.x,n.y,Math.max(cam.k,1.2))}}};
window.addEventListener('keydown',ev=>{
  if(ev.target.tagName==='INPUT')return;
  if(ev.key==='f'||ev.key==='F')fit();
  else if(ev.key==='Escape'){select(null);document.getElementById('q').blur()}
  else if(ev.key==='+'||ev.key==='=')zoomBy(1.2);
  else if(ev.key==='-')zoomBy(1/1.2);
  else if(ev.key==='0'){cam.k=1;cam.x=0;cam.y=0;schedule()}
});
function zoomBy(f){cam.k=Math.max(0.12,Math.min(5,cam.k*f));schedule();saveCam()}
function resize(){W=cv.clientWidth;H=cv.clientHeight;dpr=window.devicePixelRatio||1;cv.width=W*dpr;cv.height=H*dpr;schedule()}
new ResizeObserver(resize).observe(cv);
window.sbSetDark=on=>{document.body.classList.toggle('dark',!!on);schedule()};
window.sbSetProject=p=>{state.projects=p?new Set([p]):new Set(projects);buildPanels();build();fit();schedule()};
window.sbRedraw=build;
window.sbSelect=id=>select(id);
if(START_PROJECT&&projects.includes(START_PROJECT))state.projects=new Set([START_PROJECT]);
buildTipos();buildPanels();resize();build();
if(START_PROJECT||!loadCam())fit(false);else schedule();
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
        self.graph_sig = None
        Adw.StyleManager.get_default().connect("notify::dark", self.on_theme)
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
        self.refresh_graph()
        self.fill_todos()
        self.status.set_text(f"{self.c.execute('select count(*) from notes').fetchone()[0]} notas · {len(projs)} projetos · índice {xmem.DB_PATH}")

    def on_project(self, _lb, row):
        self.project = getattr(row, "proj", None) if row else None
        self.do_search()
        self.fill_todos()
        self.graph_project_filter()

    def graph_project_filter(self):
        """Filtra o grafo pelo projeto da barra lateral sem recarregar a página (câmera e filtros ficam)."""
        js = f"window.sbSetProject&&window.sbSetProject({json.dumps(self.project)});"
        try:
            self.graph.evaluate_javascript(js, -1, None, None, None, None, None)
        except Exception:  # noqa: BLE001
            self.refresh_graph(force=True)

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
        data = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False).replace("<", "\\u003c")
        html_ = (GRAPH_HTML.replace("{{DATA}}", data)
                 .replace("{{COLORS}}", json.dumps(self.colors))
                 .replace("{{SIG}}", sig[:12])
                 .replace("{{PROJECT}}", json.dumps(self.project)))
        html_ = html_.replace("<body>", '<body class="dark">' if self.dark else "<body>")
        self.graph.load_html(html_, "sb://graph/")

    def on_theme(self, style_manager, _pspec=None):
        self.dark = style_manager.get_dark()
        try:
            self.graph.evaluate_javascript(f"window.sbSetDark&&window.sbSetDark({str(self.dark).lower()});",
                                          -1, None, None, None, None, None)
        except Exception:  # noqa: BLE001
            pass
        if self.cur_id:
            self.open_note(self.cur_id)

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
