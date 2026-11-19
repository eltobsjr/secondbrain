"""Página Insights: retrato do que está vivo e do que está parado, a partir de xmem.insights_data (somente leitura)."""

INSIGHTS_HTML = r"""<!doctype html><meta charset="utf-8"><title>Insights</title><style>
{{THEME}}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:14px/1.5 Inter,Cantarell,system-ui,sans-serif}
body{overflow:auto;padding:28px}
.wrap{max-width:1040px;margin:0 auto}
h1{margin:0 0 4px;font-size:24px;font-weight:700;letter-spacing:-.015em}
.sub{color:var(--mut);margin:0 0 24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:16px}
.card{background:var(--panel);border-radius:14px;padding:20px 22px}
.card h2{margin:0 0 4px;font-size:16px;font-weight:600}
.card .why{margin:0 0 14px;font-size:13px;color:var(--mut)}
.row{display:flex;align-items:center;gap:12px;padding:7px 0;border-bottom:1px solid var(--bd)}
.row:last-child{border-bottom:0}
.row .n{width:150px;flex:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:500}
.bar{flex:1;display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--bg)}
.bar span{display:block;height:100%}
.row .v{width:44px;text-align:right;color:var(--chip-fg);font-size:13px;flex:none}
.tag{font-size:12px;color:var(--mut)}
.ok{color:var(--ok);font-size:13px}
.big{font-size:30px;font-weight:700;letter-spacing:-.02em}
.warn{color:var(--warn)}.err{color:var(--err)}
.leg{display:flex;gap:14px;flex-wrap:wrap;margin:0 0 12px;font-size:12px;color:var(--chip-fg)}
.leg i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.item{padding:7px 0;border-bottom:1px solid var(--bd);font-size:13px}.item:last-child{border-bottom:0}
</style><body><div class="wrap" id="root"></div>
<script>
const D={{DATA}}, COLORS={{COLORS}};
const KC={decisao:'var(--ac)',devtrack:'var(--mut)',feature:'var(--ok)',rfc:'var(--kind)',postmortem:'var(--err)',analise:'var(--warn)',release:'var(--chip-fg)'};
const KL={decisao:'decisões',devtrack:'devtracks',feature:'features',rfc:'RFCs',postmortem:'postmortems',analise:'análises',release:'releases'};
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
function card(title,why){const c=el('div','card');c.append(el('h2',null,title),el('p','why',why));return c}
const root=document.getElementById('root');
root.append(el('h1',null,'Insights'),el('p','sub','Desde '+D.desde+' · itens parados = em aberto há mais de '+D.dias_parado+' dias'));
const g=el('div','grid');root.append(g);
// atividade
{const c=card('Atividade por projeto','Notas de trabalho criadas no período: onde o esforço está indo.');
 const max=Math.max(1,...D.atividade.map(r=>r.total));
 const used=[...new Set(D.atividade.flatMap(r=>Object.keys(r.tipos)))];
 const leg=el('div','leg');for(const k of used){const s=el('span');const i=el('i');i.style.background=KC[k]||'var(--mut)';s.append(i,document.createTextNode(KL[k]||k));leg.append(s)}c.append(leg);
 if(!D.atividade.length)c.append(el('div','ok','Nenhuma atividade no período.'));
 for(const r of D.atividade.slice(0,12)){const row=el('div','row');row.append(el('span','n',r.projeto));
  const bar=el('div','bar');bar.style.maxWidth=(r.total/max*100)+'%';for(const [k,n] of Object.entries(r.tipos)){const s=el('span');s.style.flex=n;s.style.background=KC[k]||'var(--mut)';bar.append(s)}
  const w=el('div');w.style.flex='1';w.append(bar);row.append(w,el('span','v',String(r.total)));c.append(row)}
 g.append(c)}
// prazos
{const P=D.prazos||{atrasados:0,hoje:0,chegando:0,sem_prazo:0,por_projeto:{},lista:[]};
 const c=card('Prazos','Só tarefa com prazo atrasa. Dentro do prazo não é atrasada; "chegando" usa a janela de alerta do projeto (3 dias por padrão).');
 const line=el('div','leg');
 for(const [k,l,cls] of [['atrasados','atrasados','err'],['hoje','vencem hoje','warn'],['chegando','chegando','warn'],['sem_prazo','sem prazo','tag']]){const s=el('span',cls);s.textContent=P[k]+' '+l;line.append(s)}
 c.append(line);
 if(!P.lista.length)c.append(el('div','ok','Nada atrasado, vencendo hoje ou chegando.'));
 for(const r of P.lista)c.append(el('div','item',r.projeto+' · '+r.titulo+' · '+r.texto+(r.prazo?' ('+r.prazo+')':'')));
 g.append(c)}
// parados
{const c=card('Itens em aberto parados','Caixas "- [ ]" abertas há muito tempo, já sem pergunta, frase de estado, repetido e sem-sinal (ocultos: '+(D.total_ocultos||0)+'). O que tem prazo não entra: quem avisa é a flag.');
 c.append(el('div','big warn',String(D.total_parados)));
 const ent=Object.entries(D.parados_por_projeto);const max=Math.max(1,...ent.map(e=>e[1]));
 if(!ent.length)c.append(el('div','ok','Nada parado. Tudo em dia.'));
 for(const [p,n] of ent.slice(0,10)){const row=el('div','row');row.append(el('span','n',p));
  const bar=el('div','bar');const s=el('span');s.style.width=(n/max*100)+'%';s.style.background=COLORS[p]||'var(--warn)';bar.append(s);const w=el('div');w.style.flex='1';w.append(bar);row.append(w,el('span','v',String(n)));c.append(row)}
 g.append(c)}
// quietos
{const c=card('Projetos sem devtrack há mais de 30 dias','Candidatos a um /devtrack ou a ficarem de fora do dia a dia.');
 if(!D.projetos_sem_devtrack.length)c.append(el('div','ok','Todos os projetos têm devtrack recente.'));
 for(const r of D.projetos_sem_devtrack){const row=el('div','row');row.append(el('span','n',r.projeto),el('span','tag','último devtrack em '+r.ultimo));c.append(row)}
 g.append(c)}
// quadro
{const q=D.quadro;const c=card('Saúde do quadro','Cartões órfãos (origem sumiu) e cartões em Fazendo ou Bloqueado há tempo demais.');
 if(!q.orfaos.length&&!q.parados.length)c.append(el('div','ok','Nenhum cartão órfão ou esquecido em andamento.'));
 for(const [t,l,cls] of [['orfaos','Órfãos','err'],['parados','Em andamento há muito tempo','warn']]){
  if(!q[t].length)continue;const h=el('div','tag '+cls,l+' ('+q[t].length+')');h.style.margin='8px 0 4px';c.append(h);
  for(const k of q[t].slice(0,8))c.append(el('div','item',k.projeto+' · '+k.status+' · '+k.titulo))}
 g.append(c)}
// contradições
{const c=card('Contradições declaradas','Notas ativas que se contradizem e ainda não foram resolvidas.');
 if(!D.contradicoes.length)c.append(el('div','ok','Nenhuma contradição declarada.'));
 for(const r of D.contradicoes.slice(0,10))c.append(el('div','item',r.de+'  contradiz  '+r.para));
 g.append(c)}
window.sbSetDark=on=>document.body.classList.toggle('dark',!!on);
</script>"""
