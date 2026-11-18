"""Página Quadro (kanban) da interface: HTML + JS autocontidos, sem rede. Python entrega os dados (board.build) e
recebe as decisões por mensagem; quem grava `quadro.md` é scripts/board.py (com backup e confirmação)."""

BOARD_HTML = r"""<!doctype html><meta charset="utf-8"><title>Quadro</title><style>
{{THEME}}
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--fg);font:14px/1.45 Inter,Cantarell,system-ui,sans-serif}
button,select,input{font:inherit;color:inherit}
#app{display:grid;grid-template-columns:minmax(0,1fr) 0;height:100%;transition:grid-template-columns .18s ease}
#app.sel{grid-template-columns:minmax(0,1fr) 352px}
main{display:flex;flex-direction:column;min-width:0;min-height:0}
header{flex:none;padding:22px 28px 14px;border-bottom:1px solid var(--bd);display:flex;flex-direction:column;gap:14px}
.h1{display:flex;align-items:center;gap:14px}
h1{margin:0;font-size:24px;font-weight:700;letter-spacing:-.015em}
.chip{display:inline-flex;align-items:center;gap:8px;height:28px;padding:0 12px;border-radius:999px;background:var(--chip);color:var(--chip-fg);font-size:13px;font-weight:500}
.chip i{width:9px;height:9px;border-radius:50%}
.filters{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
#f{width:260px;max-width:100%;height:36px;border-radius:10px;border:1px solid var(--bd);background:var(--panel);padding:0 12px;outline:none}
#f:focus{border-color:var(--ac)}
select{height:36px;border-radius:10px;border:1px solid var(--bd);background-color:var(--panel);color:var(--fg);padding:0 10px}
#cnt{margin-left:auto;color:var(--mut);font-size:13px}
#banner{margin:14px 28px 0;padding:12px 16px;border-radius:12px;background:var(--panel);display:none;align-items:center;gap:14px;font-size:14px}
#banner.show{display:flex}
#banner b{color:var(--warn)}
.btn{height:36px;padding:0 14px;border-radius:10px;border:0;background:var(--chip);color:var(--fg);font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;white-space:nowrap}
.btn.pri{background:var(--ac);color:var(--on-ac)}
.btn:hover{filter:brightness(1.08)}
#cols{flex:1;min-height:0;display:flex;gap:14px;padding:18px 28px;overflow:auto}
.col{flex:1 0 236px;max-width:320px;display:flex;flex-direction:column;min-height:0}
.col.rail{flex:0 0 44px;max-width:44px}
.col .hd{display:flex;align-items:center;gap:8px;height:30px;flex:none}
.col .hd i{width:10px;height:10px;border-radius:3px}
.col .hd b{font-size:14px;font-weight:600}.col .hd span{font-size:13px;color:var(--mut)}
.col .hint{font-size:12px;line-height:1.4;color:var(--mut);min-height:34px;margin:2px 0 8px}
.col .body{flex:1;overflow:auto;display:flex;flex-direction:column;gap:10px;padding:2px 2px 24px;border-radius:12px}
.col.over .body{outline:2px dashed var(--ac);outline-offset:-2px;background:var(--panel)}
.col.rail .hd{writing-mode:vertical-rl;height:auto;padding:12px 0;background:var(--panel);border-radius:10px;justify-content:flex-end;cursor:pointer;width:44px;flex-direction:row}
.col.rail .hint,.col.rail .body{display:none}
.card{background:var(--chip);border:1px solid transparent;border-radius:12px;padding:12px 14px;cursor:grab;display:flex;flex-direction:column;gap:9px}
.card:hover{border-color:var(--bd)}
.card.on{border-color:var(--ac)}
.card.drag{opacity:.45}
.card .t{font-size:14px;line-height:1.4;font-weight:500;overflow-wrap:anywhere}
.card .m{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--mut)}
.pr{font-size:12px;font-weight:700;padding:1px 7px;border-radius:6px;background:var(--panel);color:var(--chip-fg)}
.pr.P0{background:var(--err);color:var(--on-ac)}.pr.P1{background:var(--warn);color:var(--on-ac)}.pr.P2{background:var(--bd);color:var(--fg)}
.warn{color:var(--warn)}
.more{border:0;background:transparent;color:var(--ac);font-weight:500;cursor:pointer;padding:6px;text-align:left}
#overview{flex:1;overflow:auto;padding:20px 28px;display:none;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;align-content:start}
.proj{background:var(--panel);border-radius:14px;padding:16px 18px;border:1px solid transparent;cursor:pointer;display:flex;flex-direction:column;gap:12px;text-align:left}
.proj:hover{border-color:var(--ac)}
.proj .n{display:flex;align-items:center;gap:10px;font-weight:600;font-size:15px}.proj .n i{width:10px;height:10px;border-radius:50%}
.proj .bar{display:flex;height:8px;border-radius:4px;overflow:hidden;background:var(--bg)}
.proj .nums{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--chip-fg)}
.proj .nums b{color:var(--fg)}
aside{background:var(--panel);border-left:1px solid var(--bd);overflow:auto;padding:0;visibility:hidden}
#app.sel aside{visibility:visible;padding:24px}
aside .tags{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
aside h3{margin:0 0 14px;font-size:18px;line-height:1.35;font-weight:700;overflow-wrap:anywhere}
.fld{display:flex;justify-content:space-between;align-items:center;gap:14px;min-height:36px;border-bottom:1px solid var(--bd);font-size:13px}
.fld>span:first-child{color:var(--mut);flex:none}
.fld>span:last-child,.fld select,.fld input{color:var(--fg);font-weight:500;text-align:right;min-width:0}
.fld select,.fld input{height:30px;border-radius:8px;border:1px solid var(--bd);background-color:var(--bg);padding:0 8px;width:170px}
.acts{display:flex;gap:10px;margin-top:20px}
.acts .btn{flex:1}
#toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:var(--panel);border:1px solid var(--bd);border-radius:12px;padding:10px 16px;font-size:13px;display:none;z-index:9;box-shadow:0 6px 20px rgba(0,0,0,.25)}
#empty{padding:40px 28px;color:var(--mut);display:none}
</style><body>
<div id="app">
<main>
  <header>
    <div class="h1"><h1 id="ttl">Quadro</h1><span class="chip" id="pj"></span><span id="cnt"></span></div>
    <div class="filters">
      <input id="f" placeholder="Filtrar cartões" spellcheck="false">
      <select id="fp"><option value="">Prioridade: todas</option><option>P0</option><option>P1</option><option>P2</option><option>P3</option></select>
      <select id="ft"><option value="">Tipo: todos</option><option value="todo">todo</option><option value="manual">manual</option><option value="criterio-feature">critério de feature</option></select>
    </div>
  </header>
  <div id="banner"><span id="bt"></span><button class="btn" id="bdisc">Descartar em lote…</button></div>
  <div id="cols"></div><div id="overview"></div><div id="empty"></div>
</main>
<aside id="drawer"></aside>
</div>
<div id="toast"></div>
<script>
const COLS={{COLS}}, HINT={{HINT}}, COLORS={{COLORS}};
let DATA={{DATA}};
const CC={triagem:'var(--mut)','a-fazer':'var(--ac)',fazendo:'var(--warn)',bloqueado:'var(--err)',revisao:'var(--kind)',feito:'var(--ok)',descartado:'var(--mut)'};
const state={sel:null,q:'',prio:'',tipo:'',open:new Set(['triagem','a-fazer','fazendo','bloqueado','revisao']),more:{}};
const $=id=>document.getElementById(id);
const send=o=>{try{window.webkit.messageHandlers.bd.postMessage(JSON.stringify(o))}catch(e){}};
const clean=t=>String(t||'').replace(/[`*]/g,'');
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
function toast(m){const t=$('toast');t.textContent=m;t.style.display='block';clearTimeout(toast.h);toast.h=setTimeout(()=>t.style.display='none',3200)}
function visible(k){
  if(state.prio&&k.prioridade!==state.prio)return false;
  if(state.tipo&&k.tipo!==state.tipo)return false;
  if(state.q&&!(k.titulo+' '+k.projeto+' '+(k.etiquetas||[]).join(' ')).toLowerCase().includes(state.q))return false;
  return true;
}
function render(){
  const cards=DATA.cartoes||[];
  const single=DATA.project;
  $('ttl').textContent='Quadro';
  const pj=$('pj');pj.innerHTML='';
  if(single){const i=el('i');i.style.background=COLORS[single]||'#8a97b2';pj.append(i,document.createTextNode(single))}
  else pj.append(document.createTextNode('Todos os projetos'));
  $('cols').style.display=single?'flex':'none';
  $('overview').style.display=single?'none':'grid';
  $('f').parentElement.style.display=single?'flex':'none';
  if(!single){renderOverview();$('banner').classList.remove('show');$('cnt').textContent=Object.keys(DATA.resumo||{}).length+' projetos';return}
  const vis=cards.filter(visible);
  const open=cards.filter(k=>k.status!=='feito'&&k.status!=='descartado').length;
  const filtering=state.q||state.prio||state.tipo;
  $('cnt').textContent=open+' abertos'+(filtering?' · '+vis.length+' no filtro':'');
  const old=cards.filter(k=>k.status==='triagem'&&k.idade_dias>=DATA.triagem_dias);
  const b=$('banner');
  if(old.length){b.classList.add('show');$('bt').innerHTML='<b>'+old.length+'</b> '+(old.length===1?'cartão em Triagem tem':'cartões em Triagem têm')+' mais de '+DATA.triagem_dias+' dias. A maioria costuma ser caixa esquecida em devtrack antigo.';
    $('bdisc').onclick=()=>send({op:'discard-old',project:single,days:DATA.triagem_dias,n:old.length})}
  else b.classList.remove('show');
  const root=$('cols');root.innerHTML='';
  for(const [key,label] of COLS){
    const list=vis.filter(k=>k.status===key);
    const all=cards.filter(k=>k.status===key).length;
    const col=el('section','col'+(state.open.has(key)?'':' rail'));col.dataset.col=key;
    const hd=el('div','hd');const sw=el('i');sw.style.background=CC[key];hd.append(sw,el('b',null,label),el('span',null,String(all)));
    hd.onclick=()=>{if(!state.open.has(key)){state.open.add(key)}else if(key==='feito'||key==='descartado'){state.open.delete(key)}render()};
    col.append(hd,el('div','hint',HINT[key]||''));
    const body=el('div','body');
    const cap=state.more[key]||40;
    for(const k of list.slice(0,cap))body.appendChild(cardEl(k));
    if(list.length>cap){const m=el('button','more','Mostrar mais '+Math.min(40,list.length-cap)+' de '+(list.length-cap));m.onclick=()=>{state.more[key]=cap+40;render()};body.appendChild(m)}
    col.append(body);
    col.addEventListener('dragover',ev=>{ev.preventDefault();col.classList.add('over')});
    col.addEventListener('dragleave',()=>col.classList.remove('over'));
    col.addEventListener('drop',ev=>{ev.preventDefault();col.classList.remove('over');const id=ev.dataTransfer.getData('text/plain');const k=cards.find(x=>x.id===id);
      if(k&&k.status!==key){state.open.add(key);send({op:'move',project:k.projeto,id:k.id,col:key})}});
    root.appendChild(col);
  }
  renderDrawer();
}
function cardEl(k){
  const c=el('div','card'+(k.id===state.sel?' on':''));c.draggable=true;c.dataset.id=k.id;
  c.append(el('div','t',clean(k.titulo)));
  const m=el('div','m');
  if(k.prioridade)m.append(el('span','pr '+k.prioridade,k.prioridade));
  if(k.parado)m.append(el('span','warn','parado há '+k.idade_dias+' d'));
  else if(k.idade_dias>0&&k.status!=='feito')m.append(el('span',null,k.idade_dias+' d'));
  if(k.modo==='manual')m.append(el('span',null,'manual'));
  if(k.orfao)m.append(el('span','warn','órfão'));
  if(k.bloqueado_por&&k.bloqueado_por.length)m.append(el('span','warn','bloqueado: '+k.bloqueado_por[0]));
  (k.etiquetas||[]).slice(0,2).forEach(t=>m.append(el('span',null,'#'+t)));
  c.append(m);
  c.onclick=()=>{state.sel=k.id;$('app').classList.add('sel');render()};
  c.addEventListener('dragstart',ev=>{ev.dataTransfer.setData('text/plain',k.id);ev.dataTransfer.effectAllowed='move';c.classList.add('drag')});
  c.addEventListener('dragend',()=>c.classList.remove('drag'));
  return c;
}
function renderDrawer(){
  const d=$('drawer');d.innerHTML='';
  const k=(DATA.cartoes||[]).find(x=>x.id===state.sel);
  if(!k){$('app').classList.remove('sel');return}
  const tags=el('div','tags');
  tags.append(el('span','chip',COLS.find(c=>c[0]===k.status)[1]),el('span','chip',k.tipo));
  if(k.orfao)tags.append(el('span','chip warn','órfão'));
  d.append(tags,el('h3',null,clean(k.titulo)));
  const row=(a,b)=>{const r=el('div','fld');r.append(el('span',null,a));if(typeof b==='string'||b==null){r.append(el('span',null,b||'—'))}else r.append(b);d.append(r)};
  const sc=el('select');for(const [key,label] of COLS){const o=el('option',null,label);o.value=key;if(key===k.status)o.selected=true;sc.append(o)}
  sc.onchange=()=>send({op:'move',project:k.projeto,id:k.id,col:sc.value});row('Status',sc);
  const sp=el('select');for(const p of ['','P0','P1','P2','P3']){const o=el('option',null,p||'sem prioridade');o.value=p;if(p===k.prioridade)o.selected=true;sp.append(o)}
  sp.onchange=()=>send({op:'move',project:k.projeto,id:k.id,col:k.status,prioridade:sp.value||null,keep:true});row('Prioridade',sp);
  row('Projeto',k.projeto);
  row('Origem',k.origem&&k.origem.nota?(k.origem.nota.replace(/\.md$/,'')+(k.origem.linha?', linha '+k.origem.linha:'')):'cartão manual');
  row('Criado',k.criado);row('Atualizado',k.atualizado);
  row('Parado há',k.parado?k.idade_dias+' dias':(k.status==='feito'?'concluído':'não está parado'));
  const bi=el('input');bi.value=(k.bloqueado_por||[]).join(', ');bi.placeholder='quem ou o quê';
  bi.onchange=()=>send({op:'move',project:k.projeto,id:k.id,col:k.status,bloqueado_por:bi.value,keep:true});row('Bloqueado por',bi);
  row('Relacionadas',(k.relacionadas||[]).join(', '));
  row('Etiquetas',(k.etiquetas||[]).map(t=>'#'+t).join(' '));
  row('Modo',k.modo==='manual'?'manual':'derivado do checkbox');
  row('Fonte do status',k.status_origem==='quadro'?'decisão registrada':'automático');
  row('Responsável',k.responsavel);row('Prazo',k.prazo);
  const acts=el('div','acts');
  const open=el('button','btn pri','Abrir nota');open.onclick=()=>send({op:'open',project:k.projeto,rel:k.origem&&k.origem.nota});
  if(!(k.origem&&k.origem.nota))open.disabled=true;
  const disc=el('button','btn',k.status==='descartado'?'Restaurar':'Descartar');
  disc.onclick=()=>send({op:'move',project:k.projeto,id:k.id,col:k.status==='descartado'?'a-fazer':'descartado'});
  acts.append(open,disc);d.append(acts);
  const close=el('button','btn','Fechar');close.style.marginTop='10px';close.style.width='100%';close.onclick=()=>{state.sel=null;render()};d.append(close);
}
function renderOverview(){
  const root=$('overview');root.innerHTML='';
  const names=Object.keys(DATA.resumo||{});
  if(!names.length){root.append(el('div','',''));return}
  for(const p of names){
    const v=DATA.resumo[p];const total=COLS.reduce((s,[k])=>s+(k==='feito'||k==='descartado'?0:v[k]),0);
    const c=el('button','proj');
    const n=el('div','n');const i=el('i');i.style.background=COLORS[p]||'#8a97b2';n.append(i,el('span',null,p));
    const bar=el('div','bar');
    for(const [k] of COLS){if(k==='feito'||k==='descartado'||!v[k])continue;const s=el('span');s.style.cssText='flex:'+v[k]+';background:'+CC[k];bar.append(s)}
    const nums=el('div','nums');
    for(const [k,l] of COLS){if(!v[k])continue;const b=el('span');b.innerHTML=l+' <b>'+v[k]+'</b>';nums.append(b)}
    c.append(n,bar,nums);c.title=total+' abertos';
    c.onclick=()=>send({op:'project',name:p});
    root.append(c);
  }
}
$('f').oninput=e=>{state.q=e.target.value.trim().toLowerCase();render()};
$('fp').onchange=e=>{state.prio=e.target.value;render()};
$('ft').onchange=e=>{state.tipo=e.target.value;render()};
window.sbBoardData=d=>{DATA=d;render()};
window.sbToast=toast;
window.sbSetDark=on=>document.body.classList.toggle('dark',!!on);
window.addEventListener('keydown',ev=>{if(ev.key==='Escape'){state.sel=null;render()}});
render();
</script>"""

HINTS = {
    "triagem": "Antigos ou sem dono. Decida: voltar, descartar ou manter.",
    "a-fazer": "Decidido que entra, ainda sem começar.",
    "fazendo": "No máximo 3 por vez, para não espalhar.",
    "bloqueado": "Depende de alguém ou de outro cartão.",
    "revisao": "Pronto, esperando conferência.",
    "feito": "Concluídos (a origem foi marcada).",
    "descartado": "Fora do escopo. A nota de origem fica intacta.",
}
