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
#vseg{display:flex;padding:3px;border-radius:10px;background:var(--panel);border:1px solid var(--bd);margin-left:auto}
#vseg button{border:0;background:transparent;border-radius:8px;padding:5px 12px;font-size:13px;font-weight:500;color:var(--mut);cursor:pointer}
#vseg button.on{background:var(--chip);color:var(--fg)}
#list{flex:1;overflow:auto;padding:14px 28px;display:none}
#list table{width:100%;border-collapse:collapse;font-size:14px}
#list th{text-align:left;font-size:12px;font-weight:600;color:var(--mut);padding:8px 10px;border-bottom:1px solid var(--bd)}
#list td{padding:10px;border-bottom:1px solid var(--bd);vertical-align:top}
#list tr.row{cursor:pointer}#list tr.row:hover td{background:var(--panel)}
.none{font-size:12px;color:var(--mut);padding:8px 4px}
.form label{display:block;font-size:12px;font-weight:600;color:var(--mut);margin:14px 0 6px}
.form input,.form select{width:100%;height:38px;border-radius:10px;border:1px solid var(--bd);background-color:var(--bg);color:var(--fg);padding:0 12px}
#toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:var(--panel);border:1px solid var(--bd);border-radius:12px;padding:10px 16px;font-size:13px;display:none;z-index:9;box-shadow:0 6px 20px rgba(0,0,0,.25)}
#empty{padding:40px 28px;color:var(--mut);display:none}
#weeks{flex:none;display:flex;align-items:center;gap:8px;padding:12px 28px 0;overflow:auto}
.wk{flex:none;border:1px solid var(--bd);background:var(--panel);border-radius:10px;padding:6px 12px;cursor:pointer;display:flex;flex-direction:column;align-items:flex-start;min-width:112px;text-align:left}
.wk b{font-size:13px}.wk span{font-size:11px;color:var(--mut)}
.wk.on{border-color:var(--ac);background:var(--chip)}
.wk.now b::after{content:' · hoje';color:var(--ac);font-weight:500}
.wk.over{outline:2px dashed var(--ac)}
#sprint{flex:none;display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:10px 28px 0}
.fl{display:inline-flex;align-items:center;height:22px;padding:0 9px;border-radius:999px;font-size:12px;font-weight:600;background:var(--panel);color:var(--chip-fg);white-space:nowrap}
.fl.atrasado{background:var(--err);color:var(--on-ac)}
.fl.hoje{background:var(--warn);color:var(--on-ac)}
.fl.chegando{background:var(--warn);color:var(--on-ac);opacity:.85}
.fl.no-prazo{background:var(--ok);color:var(--on-ac)}
.fl.cheia{background:var(--warn);color:var(--on-ac)}
#cal,#agenda{flex:1;min-height:0;display:none;gap:14px;padding:18px 28px;overflow:auto}
</style><body>
<div id="app">
<main>
  <header>
    <div class="h1"><h1 id="ttl">Quadro</h1><span class="chip" id="pj"></span><span id="cnt"></span>
      <div id="vseg"><button id="vc" class="on">Calendário</button><button id="va">Agenda</button><button id="vq">Quadro</button><button id="vl">Lista</button><button id="vo">Projetos</button></div><button class="btn pri" id="newb" title="Atalho: n">Novo cartão</button></div>
    <div class="filters">
      <input id="f" placeholder="Filtrar cartões" spellcheck="false">
      <select id="fp"><option value="">Prioridade: todas</option><option>P0</option><option>P1</option><option>P2</option><option>P3</option></select>
      <select id="fe"><option value="">Etiqueta: todas</option></select>
      <select id="ft"><option value="">Tipo: todos</option><option value="todo">todo</option><option value="manual">manual</option><option value="criterio-feature">critério de feature</option></select>
      <select id="fs"><option value="">Situação: todas</option><option value="atrasado">atrasado</option><option value="hoje">vence hoje</option><option value="chegando">chegando</option><option value="no-prazo">no prazo</option><option value="sem-prazo">sem prazo</option></select>
      <select id="fj"><option value="">Projeto: todos</option></select>
    </div>
  </header>
  <div id="weeks"></div><div id="sprint"></div>
  <div id="banner"><span id="bt"></span><button class="btn" id="bdisc">Descartar em lote…</button></div>
  <div id="cal"></div><div id="agenda"></div><div id="cols"></div><div id="list"></div><div id="overview"></div><div id="empty"></div>
</main>
<aside id="drawer"></aside>
</div>
<div id="toast"></div>
<script>
const COLS={{COLS}}, HINT={{HINT}}, COLORS={{COLORS}};
let DATA={{DATA}};
const CC={triagem:'var(--mut)','a-fazer':'var(--ac)',fazendo:'var(--warn)',bloqueado:'var(--err)',revisao:'var(--kind)',feito:'var(--ok)',descartado:'var(--mut)'};
const state={sel:null,q:'',prio:'',tipo:'',tag:'',sit:'',proj:'',sem:null,pj:null,view:'calendario',newForm:false,open:new Set(['triagem','a-fazer','fazendo','bloqueado','revisao']),more:{}};
const $=id=>document.getElementById(id);
const send=o=>{try{window.webkit.messageHandlers.bd.postMessage(JSON.stringify(o))}catch(e){}};
const clean=t=>String(t||'').replace(/[`*]/g,'');
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
function toast(m){const t=$('toast');t.textContent=m;t.style.display='block';clearTimeout(toast.h);toast.h=setTimeout(()=>t.style.display='none',3200)}
function visible(k){
  if(state.prio&&k.prioridade!==state.prio)return false;
  if(state.tipo&&k.tipo!==state.tipo)return false;
  if(state.tag&&!(k.etiquetas||[]).includes(state.tag))return false;
  if(state.sit&&k.flag!==state.sit)return false;
  if(state.proj&&k.projeto!==state.proj)return false;
  if(state.q&&!(k.titulo+' '+k.projeto+' '+(k.etiquetas||[]).join(' ')).toLowerCase().includes(state.q))return false;
  return true;
}
const closed=k=>k.status==='feito'||k.status==='descartado';
const byPrazo=(a,b)=>{const x=a.prazo||'9999',y=b.prazo||'9999';return x<y?-1:x>y?1:(a.prioridade||'P9').localeCompare(b.prioridade||'P9')};
const VIEWS_SINGLE=['calendario','agenda','quadro','lista'], VIEWS_GLOBAL=['calendario','agenda','projetos'];
function ensureWeek(){
  if(state.pj!==(DATA.project||'')){state.pj=DATA.project||'';state.sem=null;state.proj='';$('fj').value=''}
  const ws=DATA.semanas||[];
  if(!state.sem||(state.sem!=='backlog'&&!ws.includes(state.sem)))state.sem=DATA.ultima_semana||DATA.semana_hoje;
}
function render(){
  const cards=DATA.cartoes||[];
  const single=DATA.project;
  const allowed=single?VIEWS_SINGLE:VIEWS_GLOBAL;
  if(!allowed.includes(state.view))state.view='calendario';
  ensureWeek();
  const v=state.view;
  $('ttl').textContent='Quadro';
  const pj=$('pj');pj.innerHTML='';
  if(single){const i=el('i');i.style.background=COLORS[single]||'#8a97b2';pj.append(i,document.createTextNode(single))}
  else pj.append(document.createTextNode('Todos os projetos'));
  $('cols').style.display=v==='quadro'?'flex':'none';
  $('list').style.display=v==='lista'?'block':'none';
  $('overview').style.display=v==='projetos'?'grid':'none';
  $('cal').style.display=v==='calendario'?'flex':'none';
  $('agenda').style.display=v==='agenda'?'flex':'none';
  $('weeks').style.display=v==='calendario'?'flex':'none';
  $('sprint').style.display=v==='calendario'?'flex':'none';
  $('newb').style.display=single?'inline-flex':'none';
  for(const [id,name] of [['vc','calendario'],['va','agenda'],['vq','quadro'],['vl','lista'],['vo','projetos']]){
    const b=$(id);b.style.display=allowed.includes(name)?'':'none';b.classList.toggle('on',v===name)}
  $('f').parentElement.style.display=v==='projetos'?'none':'flex';
  const fj=$('fj');fj.style.display=single?'none':'';
  const pjs=DATA.projetos||[];
  if(fj.options.length!==pjs.length+1){fj.innerHTML='<option value="">Projeto: todos</option>';for(const p of pjs){const o=el('option',null,p);o.value=p;fj.append(o)}fj.value=state.proj}
  const tags=[...new Set(cards.flatMap(k=>k.etiquetas||[]))].sort();
  const fe=$('fe');if(fe.options.length!==tags.length+1){fe.innerHTML='<option value="">Etiqueta: todas</option>';for(const t of tags){const o=el('option',null,'#'+t);o.value=t;fe.append(o)}fe.value=state.tag}
  const vis=cards.filter(visible);
  const open=cards.filter(k=>!closed(k)).length;
  const filtering=state.q||state.prio||state.tipo||state.tag||state.sit||state.proj;
  $('cnt').textContent=open+' abertos'+(filtering?' · '+vis.length+' no filtro':'');
  const b=$('banner');
  const old=single&&v==='quadro'?cards.filter(k=>k.status==='triagem'&&k.idade_dias>=DATA.triagem_dias):[];
  if(old.length){b.classList.add('show');$('bt').innerHTML='<b>'+old.length+'</b> '+(old.length===1?'cartão em Triagem tem':'cartões em Triagem têm')+' mais de '+DATA.triagem_dias+' dias. A maioria costuma ser caixa esquecida em devtrack antigo.';
    $('bdisc').onclick=()=>send({op:'discard-old',project:single,days:DATA.triagem_dias,n:old.length})}
  else b.classList.remove('show');
  if(v==='projetos'){renderOverview();$('cnt').textContent=Object.keys(DATA.resumo||{}).length+' projetos';renderDrawer();return}
  if(v==='calendario'){renderWeeks(cards);renderSprint(cards);renderCal(vis);renderDrawer();return}
  if(v==='agenda'){renderAgenda(vis);renderDrawer();return}
  if(v==='lista'){renderList(vis);renderDrawer();return}
  renderQuadro(vis,cards);
  renderDrawer();
}
function dropPlan(ev,w){
  const id=ev.dataTransfer.getData('text/plain');const k=(DATA.cartoes||[]).find(x=>x.id===id);
  if(!k||closed(k))return;send({op:'plan',project:k.projeto,id:k.id,semana:w});
}
function weekChip(w,cards){
  const ab=cards.filter(k=>!closed(k)&&k.semana_ef===w&&visible(k)).length;
  const fe=cards.filter(k=>k.status==='feito'&&k.feito_semana===w&&visible(k)).length;
  const b=el('button','wk'+(w===state.sem?' on':'')+(w===DATA.semana_hoje?' now':''));
  b.append(el('b',null,w.slice(5)),el('span',null,(DATA.rotulos||{})[w]||''),el('span',null,ab+' abertas · '+fe+' feitas'));
  b.onclick=()=>{state.sem=w;render()};
  b.addEventListener('dragover',ev=>{ev.preventDefault();b.classList.add('over')});
  b.addEventListener('dragleave',()=>b.classList.remove('over'));
  b.addEventListener('drop',ev=>{ev.preventDefault();b.classList.remove('over');dropPlan(ev,w)});
  return b;
}
function renderWeeks(cards){
  const root=$('weeks');root.innerHTML='';
  const ws=DATA.semanas||[];const i=Math.max(0,ws.indexOf(state.sem));
  const prev=el('button','btn','‹');prev.title='Semana anterior';prev.onclick=()=>{const j=state.sem==='backlog'?ws.length-1:i-1;if(j>=0){state.sem=ws[j];render()}};
  const next=el('button','btn','›');next.title='Próxima semana';next.onclick=()=>{if(state.sem!=='backlog'&&i<ws.length-1){state.sem=ws[i+1];render()}};
  const bl=el('button','wk'+(state.sem==='backlog'?' on':''));
  bl.append(el('b',null,'Backlog'),el('span',null,'sem semana'),el('span',null,cards.filter(k=>!closed(k)&&k.backlog&&visible(k)).length+' abertas'));
  bl.onclick=()=>{state.sem='backlog';render()};
  bl.addEventListener('dragover',ev=>{ev.preventDefault();bl.classList.add('over')});
  bl.addEventListener('dragleave',()=>bl.classList.remove('over'));
  bl.addEventListener('drop',ev=>{ev.preventDefault();bl.classList.remove('over');dropPlan(ev,'backlog')});
  root.append(bl,prev);
  const lo=Math.max(0,Math.min(i-3,ws.length-7)),hi=Math.min(ws.length,lo+7);
  for(const w of ws.slice(lo,hi))root.append(weekChip(w,cards));
  root.append(next);
  const hb=el('button','btn','Hoje');hb.onclick=()=>{state.sem=DATA.semana_hoje;render()};
  const ub=el('button','btn','Última com registro');ub.onclick=()=>{state.sem=DATA.ultima_semana||DATA.semana_hoje;render()};
  const sel=el('select');for(const w of [...ws].reverse()){const o=el('option',null,w+' · '+((DATA.rotulos||{})[w]||''));o.value=w;sel.append(o)}
  if(state.sem!=='backlog')sel.value=state.sem;sel.onchange=()=>{state.sem=sel.value;render()};
  root.append(hb,ub,sel);
}
function renderSprint(cards){
  const w=state.sem;const root=$('sprint');root.innerHTML='';
  const chip=(t,c)=>root.append(el('span','fl'+(c?' '+c:''),t));
  if(w==='backlog'){chip('Backlog: itens sem semana (documento vivo ou movidos para cá)');return}
  const ab=cards.filter(k=>!closed(k)&&k.semana_ef===w),fe=cards.filter(k=>k.status==='feito'&&k.feito_semana===w);
  const plan=ab.filter(k=>k.planejado).length,cap=DATA.capacidade||0;
  chip('Semana '+w+' · '+((DATA.rotulos||{})[w]||'')+(w===DATA.ultima_semana?' · última com registro':''));
  chip('Planejados '+plan+(cap?'/'+cap:'')+(cap&&plan>cap?' · semana cheia':''),cap&&plan>cap?'cheia':'');
  chip('Surgiram '+cards.filter(k=>k.surgiu===w).length);
  chip('Feitos '+fe.length);
  const at=ab.filter(k=>k.flag==='atrasado').length,ch=ab.filter(k=>k.flag==='hoje'||k.flag==='chegando').length;
  if(at)chip('Atrasados '+at,'atrasado');
  if(ch)chip('Chegando '+ch,'chegando');
}
function colEl(label,list,hint,dropCol,color){
  const col=el('section','col');
  const hd=el('div','hd');const sw=el('i');sw.style.background=color;hd.append(sw,el('b',null,label),el('span',null,String(list.length)));
  col.append(hd,el('div','hint',hint||''));
  const body=el('div','body');
  if(!list.length)body.appendChild(el('div','none','Nada aqui'));
  const cap=state.more[label]||40;
  for(const k of list.slice(0,cap))body.appendChild(cardEl(k));
  if(list.length>cap){const m=el('button','more','Mostrar mais '+Math.min(40,list.length-cap)+' de '+(list.length-cap));m.onclick=()=>{state.more[label]=cap+40;render()};body.appendChild(m)}
  col.append(body);
  if(dropCol){
    col.addEventListener('dragover',ev=>{ev.preventDefault();col.classList.add('over')});
    col.addEventListener('dragleave',()=>col.classList.remove('over'));
    col.addEventListener('drop',ev=>{ev.preventDefault();col.classList.remove('over');const id=ev.dataTransfer.getData('text/plain');const k=(DATA.cartoes||[]).find(x=>x.id===id);
      if(!k||k.status===dropCol)return;send({op:'move',project:k.projeto,id:k.id,col:dropCol})});
  }
  return col;
}
function renderCal(vis){
  const root=$('cal');root.innerHTML='';const w=state.sem;
  const open=vis.filter(k=>!closed(k)&&(w==='backlog'?k.backlog:k.semana_ef===w));
  const done=w==='backlog'?[]:vis.filter(k=>k.status==='feito'&&k.feito_semana===w);
  const pick=sts=>open.filter(k=>sts.includes(k.status)).sort(byPrazo);
  root.append(colEl('Abertas',pick(['triagem','a-fazer']),'Ainda não começaram. Arraste um cartão para outra semana acima para planejá-lo.','a-fazer','var(--ac)'),
              colEl('Em andamento',pick(['fazendo','revisao','bloqueado']),'Fazendo, em revisão ou bloqueadas.','fazendo','var(--warn)'),
              colEl('Feitas nesta semana',done.sort(byPrazo),'A semana vem da data de conclusão, não de quando surgiu.','feito','var(--ok)'));
}
function renderAgenda(vis){
  const root=$('agenda');root.innerHTML='';
  const open=vis.filter(k=>!closed(k));
  const color={atrasadas:'var(--err)',hoje:'var(--warn)','esta-semana':'var(--ac)','proxima-semana':'var(--kind)',adiante:'var(--mut)','sem-prazo':'var(--mut)'};
  const hint={atrasadas:'Prazo vencido e ainda aberto.',hoje:'Vencem hoje.','esta-semana':'Prazo até o domingo.','proxima-semana':'Prazo na semana que vem.',adiante:'Depois da semana que vem.','sem-prazo':'Defina um prazo no detalhe do cartão.'};
  for(const [j,label] of DATA.janelas||[])root.append(colEl(label,open.filter(k=>k.janela===j).sort(byPrazo),hint[j],null,color[j]));
}
function renderQuadro(vis,cards){
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
    if(!list.length)body.appendChild(el('div','none',all?'Nenhum cartão neste filtro':'Nenhum cartão'));
    for(const k of list.slice(0,cap))body.appendChild(cardEl(k));
    if(list.length>cap){const m=el('button','more','Mostrar mais '+Math.min(40,list.length-cap)+' de '+(list.length-cap));m.onclick=()=>{state.more[key]=cap+40;render()};body.appendChild(m)}
    col.append(body);
    col.addEventListener('dragover',ev=>{ev.preventDefault();col.classList.add('over')});
    col.addEventListener('dragleave',()=>col.classList.remove('over'));
    col.addEventListener('drop',ev=>{ev.preventDefault();col.classList.remove('over');const id=ev.dataTransfer.getData('text/plain');const k=cards.find(x=>x.id===id);
      if(!k)return;
      const over=ev.target.closest?ev.target.closest('.card'):null;
      const ids=[...col.querySelectorAll('.card')].map(c=>c.dataset.id).filter(x=>x!==id);
      const at=over&&over.dataset.id!==id?ids.indexOf(over.dataset.id):ids.length;
      ids.splice(at<0?ids.length:at,0,id);
      if(k.status===key&&ids.join()===[...col.querySelectorAll('.card')].map(c=>c.dataset.id).join())return;
      state.open.add(key);send({op:'move',project:k.projeto,id:k.id,col:key,order:ids})});
    root.appendChild(col);
  }
}
function cardEl(k){
  const c=el('div','card'+(k.id===state.sel?' on':''));c.draggable=true;c.dataset.id=k.id;
  c.append(el('div','t',clean(k.titulo)));
  const m=el('div','m');
  if(!DATA.project)m.append(el('span',null,k.projeto));
  if(k.prioridade)m.append(el('span','pr '+k.prioridade,k.prioridade));
  if(k.flag&&k.flag!=='sem-prazo'&&!closed(k))m.append(el('span','fl '+k.flag,k.flag_texto));
  if(k.status==='feito'&&k.feito_em)m.append(el('span',null,'feito em '+k.feito_em.slice(5).split('-').reverse().join('/')));
  if(k.parado)m.append(el('span','warn','parado há '+k.idade_dias+' d'));
  else if(k.idade_dias>0&&k.status!=='feito')m.append(el('span',null,k.idade_dias+' d'));
  if(k.modo==='manual')m.append(el('span',null,'manual'));
  if(k.orfao)m.append(el('span','warn','órfão'));
  if(k.bloqueado_por&&k.bloqueado_por.length)m.append(el('span','warn','bloqueado: '+k.bloqueado_por[0]));
  (k.etiquetas||[]).slice(0,2).forEach(t=>m.append(el('span',null,'#'+t)));
  c.append(m);
  c.onclick=()=>{state.sel=k.id;state.newForm=false;$('app').classList.add('sel');render()};
  c.addEventListener('dragstart',ev=>{ev.dataTransfer.setData('text/plain',k.id);ev.dataTransfer.effectAllowed='move';c.classList.add('drag')});
  c.addEventListener('dragend',()=>c.classList.remove('drag'));
  return c;
}
function renderList(vis){
  const root=$('list');root.innerHTML='';
  if(!vis.length){root.append(el('div','none','Nenhum cartão neste filtro'));return}
  const t=el('table');const hd=el('tr');for(const h of ['Prio','Cartão','Status','Parado há'])hd.append(el('th',null,h));t.append(hd);
  for(const k of vis.filter(x=>state.q||state.prio||state.tag||state.tipo||(x.status!=='feito'&&x.status!=='descartado'))){
    const r=el('tr','row');r.append(el('td',null,k.prioridade||'—'),el('td',null,clean(k.titulo)),el('td',null,COLS.find(c=>c[0]===k.status)[1]),el('td',null,k.parado?k.idade_dias+' d':''));
    r.onclick=()=>{state.sel=k.id;state.newForm=false;$('app').classList.add('sel');render()};t.append(r)}
  root.append(t);
}
function showNew(){state.newForm=true;state.sel=null;$('app').classList.add('sel');renderDrawer()}
function renderDrawer(){
  const d=$('drawer');d.innerHTML='';
  if(state.newForm){
    d.append(el('h3',null,'Novo cartão'));const f=el('div','form');
    const ti=el('input');ti.placeholder='O que precisa ser feito?';
    const sc=el('select');for(const [key,label] of COLS){if(key==='descartado')continue;const o=el('option',null,label);o.value=key;if(key==='a-fazer')o.selected=true;sc.append(o)}
    const sp=el('select');for(const p of ['','P0','P1','P2','P3']){const o=el('option',null,p||'sem prioridade');o.value=p;sp.append(o)}
    const lab=(t,x)=>{f.append(el('label',null,t),x)};lab('Título',ti);lab('Coluna',sc);lab('Prioridade',sp);d.append(f);
    const go=()=>{const t=ti.value.trim();if(!t){ti.focus();return}send({op:'add',project:DATA.project,titulo:t,col:sc.value,prioridade:sp.value||null});state.newForm=false;state.sel=null;$('app').classList.remove('sel')};
    ti.onkeydown=e=>{if(e.key==='Enter')go()};
    const acts=el('div','acts');const ok=el('button','btn pri','Criar');ok.onclick=go;const no=el('button','btn','Cancelar');no.onclick=()=>{state.newForm=false;$('app').classList.remove('sel');d.innerHTML=''};acts.append(ok,no);d.append(acts);
    setTimeout(()=>ti.focus(),30);return}
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
  row('Situação',k.flag_texto||'—');
  const pz=el('input');pz.type='date';pz.value=k.prazo||'';pz.onchange=()=>send({op:'prazo',project:k.projeto,id:k.id,prazo:pz.value});row('Prazo',pz);
  const ss=el('select');for(const w of ['backlog',...(DATA.semanas||[])]){const o=el('option',null,w==='backlog'?'Backlog':w+' ('+((DATA.rotulos||{})[w]||'')+')');o.value=w;if(w===(k.backlog?'backlog':k.semana_ef))o.selected=true;ss.append(o)}
  ss.disabled=closed(k);ss.onchange=()=>send({op:'plan',project:k.projeto,id:k.id,semana:ss.value});row('Semana',ss);
  row('Surgiu em',k.surgiu||'documento vivo (sem semana)');row('Concluído em',k.feito_em||'—');
  row('Responsável',k.responsavel);
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
$('fe').onchange=e=>{state.tag=e.target.value;render()};
$('vc').onclick=()=>{state.view='calendario';render()};$('va').onclick=()=>{state.view='agenda';render()};$('vq').onclick=()=>{state.view='quadro';render()};$('vl').onclick=()=>{state.view='lista';render()};$('vo').onclick=()=>{state.view='projetos';render()};
$('fs').onchange=e=>{state.sit=e.target.value;render()};
$('fj').onchange=e=>{state.proj=e.target.value;render()};
$('newb').onclick=showNew;
window.sbBoardData=d=>{DATA=d;render()};
window.sbToast=toast;
window.sbSetDark=on=>document.body.classList.toggle('dark',!!on);
window.addEventListener('keydown',ev=>{
  const typing=/^(INPUT|SELECT|TEXTAREA)$/.test((ev.target||{}).tagName||'');
  if(ev.key==='Escape'){state.sel=null;state.newForm=false;$('app').classList.remove('sel');render();return}
  if(typing||ev.ctrlKey||ev.metaKey||ev.altKey)return;
  if(ev.key==='n'&&DATA.project){ev.preventDefault();showNew()}
  else if(ev.key==='/'){ev.preventDefault();$('f').focus()}
  else if(ev.key==='l'&&DATA.project){state.view=state.view==='quadro'?'lista':'quadro';render()}
  else if(ev.key==='c'){state.view='calendario';render()}
  else if(ev.key==='a'){state.view='agenda';render()}
});
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
