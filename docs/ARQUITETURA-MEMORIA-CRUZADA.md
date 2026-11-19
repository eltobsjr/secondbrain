---
tipo: arquitetura
status: ativo
data: 2026-11-16
versao: 0.7.0
---

# Arquitetura da memória cruzada do SecondBrain

> Documento para humanos **e** para a IA. Tudo aqui foi verificado em código ou executado nos seus dados; o que é limite ou suposição está marcado.

## 1. Objetivo

Cada projeto tem o seu vault. O objetivo é um **cérebro único e navegável**: achar o que já foi resolvido em outro projeto, consolidar padrões repetidos e enxergar tudo numa interface nativa, sem trocar a fonte da verdade (arquivos Markdown) por um banco.

## 2. Princípios (herdados da análise do Memora e das suas regras)

| Princípio | Como aparece aqui |
|---|---|
| Arquivo é a fonte da verdade; índice é cache | `xmem.db` é derivado e reconstruível (`xmem.py index --full`) |
| Recuperar só o que está ativo | nota substituída some da busca por padrão (`--all` mostra) |
| Nunca apagar conhecimento | substituir muda só `status` e cria aresta `supersedes`; a nota antiga fica |
| Substituir é perigoso: exigir prova | regra dos **3 "sim"**; na dúvida, "relacionado" |
| Falhar fechado | vault sensível começa como "só título" para outros projetos; versão do esquema diferente reconstrói o índice |
| Conteúdo armazenado é dado, não instrução | skills mandam ignorar ordens escritas dentro de notas |
| Economia de contexto | resultados em trechos curtos; hook com teto de 1.500 caracteres; nada é lido inteiro sem necessidade |
| Nunca inferir tipo sozinho | tipo vem do papel da pasta ou do frontmatter explícito (o Memora já rotulou 130 memórias erradas por inferência) |

## 3. Componentes

```
vaults (.md)  ─┐
memória Claude ├─►  xmem.py index  ─►  ~/.local/share/secondbrain/xmem.db (SQLite + FTS5, derivado)
CLAUDE.md     ─┘                          │
                                          ├─► skills do Claude: /recall /patterns /learn /decision /audit /context
                                          ├─► hook de início de sessão (opt-in, ≤1500 caracteres)
                                          └─► interface nativa (GTK4 + libadwaita + WebKitGTK)
~/GlobalSecondBrain/  (cartões de projeto, padroes/, licoes/, INDEX.md)  ◄── /patterns, global-init
~/backups-… / HD externo  ◄── backup.sh (inclui o vault global)
```

Ferramentas em `~/.local/share/secondbrain/bin` (variável `$SB`), copiadas por `scripts/install-tools.sh`.

## 4. Modelo de dados do índice (`scripts/xmem.py`)

- **notes**: projeto, vault, caminho, `kind` (papel da pasta), `tipo`, data, `status`, sensibilidade, política de exposição (`policy`), `inactive`.
- **chunks**: cada seção `##`/`###` vira um trecho buscável (seção longa é quebrada em parágrafos); a nota é achada pelo melhor trecho. O `description` do frontmatter entra no texto (nas memórias do Claude ele é o resumo principal).
- **post/idf**: vetores TF-IDF esparsos (80 termos por trecho) e índice invertido; o radical de 5 letras (`~autent`) casa flexões.
- **edges**: `links_to` (wikilink), arestas tipadas declaradas no frontmatter, e `related_to` automáticas (os 10 vizinhos mais próximos de cada nota, piso de 0,16 e corte em 0,44× o melhor vizinho; par canônico `a<b`, sem duplicar link nem aresta declarada, só entre notas de conhecimento).
- **todos**: `- [ ]` e `- [x]` de devtrack, estado, prioridade, features. Item é "em aberto" se sua ocorrência **mais recente** está desmarcada.

### Relações no frontmatter (opcionais)

`substitui`, `contradiz`, `estende`, `implementa`, `referencia`, `relacionado` e `origem`. Valores: `"[[wikilink]]"` (mesmo vault) ou `projeto:caminho-sem-.md` (entre vaults). Decisão com `status: substituída por NNN` também gera a aresta.

## 5. Busca

1. **Perna semântica:** cosseno TF-IDF contra todos os trechos (via SQL sobre o índice invertido).
2. **Perna por palavra:** FTS5/BM25, sem acento.
3. **Fusão RRF** (k=60; pesos 0,6 semântico / 0,4 palavra; pequeno bônus pelo cosseno) — mesmo desenho do Memora (`hybrid_search_scored`).
4. **Ajustes meus, medidos:** cobertura ponderada pela raridade dos termos; siglas e identificadores (`RLS`, `parseDate`, `--verbose`) pesam 1,6×; bônus de tipo (padrão, decisão, memória) proporcional à relevância; só o que está ativo.

### Qualidade medida (`tests/eval_xmem.py`, consultas reais com resposta verificada à mão)

| Conjunto | top 3 | MRR |
|---|---|---|
| Ajuste (8 perguntas usadas para calibrar) | 8/8 | 1,000 |
| **Reservado (6 perguntas que não influenciaram o ajuste)** | **6/6** | **0,833** |

O número de referência é o do conjunto reservado. Antes dos ajustes, o conjunto de ajuste dava MRR 0,729.

### Limite honesto

É busca **lexical** (TF-IDF + radicais). **Não entende sinônimos** como um modelo de embeddings (o Memora usa embeddings densos por padrão). Compensação: siglas e termos técnicos, que dominam suas notas, funcionam bem. Embeddings locais ficam como extensão futura (ponto de troca: `tokens`/`rebuild_vectors`).

## 6. Fluxos que a IA usa

| Situação | Comando | O que entrega |
|---|---|---|
| Travou num problema | `xmem.py recall "<problema>"` | notas de **outros** projetos, com trecho e aviso de aplicação |
| Começar sessão | hook / `hook-context` | estado, notas relevantes, itens parados (≤1500 caracteres) |
| Entender um tema | `digest "<tema>"` | notas ativas + linhagem + relacionadas (até 3 saltos) + itens abertos |
| Gravar aprendizado/decisão | `absorb-check "<texto>"` | candidatas parecidas, classe provável, aviso de segredo, regra dos 3 "sim" |
| Consolidar | `patterns` | grupos de ≥2 projetos que se parecem → `padroes/` do vault global |
| Higiene | `dups`, `insights` | duplicatas, parados >14 dias, projetos sem devtrack >30 dias, contradições |

### Limiares do `absorb-check`

| Faixa (cosseno) | Classe | Origem |
|---|---|---|
| ≥ 0,80 | duplicata provável | Memora usa 0,85 com embeddings; recalibrado para TF-IDF |
| 0,50–0,80 (mesmo projeto) | candidata a substituir/consolidar → exige os 3 "sim" | Memora: piso 0,55 + verificação |
| 0,25–0,50 | relacionada | Memora: 0,35 |

Medido: uma **paráfrase** de decisão existente deu 0,67 (cai em "candidata"); um aspecto relacionado deu 0,26–0,29; texto sem relação deu nada. Com TF-IDF a paráfrase não atinge o patamar de duplicata automática, então vai para a verificação do Claude, como no Memora.

## 7. Privacidade

`crossmem` por vault: `completo` | `titulos` | `nenhum`. Sem a chave, `sensibilidade: alta` → `titulos`. A restrição vale **só quando há outro projeto em foco** (o diretório atual está dentro de outro projeto). Interface e busca solta veem tudo, porque não há projeto de destino para vazar. O motivo: o risco é o Claude copiar texto de um projeto para arquivo público ou versionado de outro.

Segredos: os 10 padrões do Memora mais `sk-…` são checados no `absorb-check` e no `/audit`. Nada é gravado na rede em nenhum componente.

## 8. Interface (`gui/secondbrain_gui.py`)

GTK4 + libadwaita + WebKitGTK 6 (já instalados). Barra de projetos (🔒, itens parados), busca híbrida, alternância "Outros projetos" (recall) e "Substituídas", leitor de nota (Markdown com HTML cru **escapado**, JavaScript desligado, imagens remotas bloqueadas, links `[[...]]` navegáveis), painéis de linhagem/relacionadas/citada por, **grafo** e **pendências**. Somente leitura sobre os vaults. Atalho: `~/.local/share/applications/io.github.eltobsjr.SecondBrain.desktop`.

### Grafo

O mapa é **calculado em Python e cacheado**, não simulado no navegador — por isso não treme:

1. `graph_layout` monta cada projeto como uma ilha: repulsão em grade, mola nas arestas e gravidade no centro, posições iniciais determinísticas (espiral áurea) e nenhum sorteio.
2. As ilhas são empacotadas como um arquipélago: espiral inicial, atração entre projetos que têm arestas entre si e folga mínima de 70 px entre cascos.
3. O resultado vai para `~/.local/share/secondbrain/graph_layout.json`, atrelado a um hash do conteúdo do grafo (`graph_signature`: ids, projetos, tipos e arestas). Reindexar sem mudar nada mantém o mapa; mudar notas recalcula, e a interface só recarrega a página quando o hash muda (`--recompute` força).
4. A página desenha um canvas estático com casco por projeto, rótulos em pílula, graus por nota, painel de relacionadas (clique seleciona, duplo clique abre a nota), busca, filtros por projeto/camada/tipo/similaridade, modo "entre projetos", modo **Local** (vizinhança de 1 ou 2 saltos da nota selecionada), zoom no cursor e "ajustar à tela". A câmera e os filtros ficam salvos em `localStorage` por assinatura do grafo.

A física de 16 ms/tick que existia antes (≈ 11 s para assentar e nós ainda se mexendo) foi removida: o navegador só desenha, então pan e zoom rodam a 60 fps mesmo com ~900 notas.

## 8b. Quadro kanban (decisão 009, `scripts/board.py`)

Cartões **derivados** das caixas `- [ ]` (um por projeto + texto normalizado, vale a ocorrência mais recente) e decisões em `{vault}/quadro.md`, criado só quando alguém mexe, no formato do Obsidian Kanban (`## Coluna`, `- [ ] texto #P1 #etiqueta ^id`, campos `chave:: valor`).

| Coluna inicial | Regra |
|---|---|
| Triagem | aberto há mais de 60 dias (só os que passam pelas regras da 8d) |
| A fazer | aberto recente |
| Feito | `[x]` na ocorrência mais recente; mover o cartão grava a caixa na nota de origem (8f) |

Colunas: `triagem, a-fazer, fazendo, bloqueado, revisao, feito, descartado`. Campos do cartão (`board show --json`, `schema` 1): `id, titulo, status, prioridade, tipo, projeto, origem{nota,linha,data}, criado, atualizado, idade_dias, parado, bloqueado_por, relacionadas, etiquetas, modo, responsavel, prazo, orfao, status_origem, ordem`.

**Propagação (8f):** o quadro deixou de ser um ponto isolado. Mover para Feito grava `[x]` na caixa de origem, Descartado grava `[-]` (o índice trata como fechado), e sair de Feito reabre `[ ]`. A linha é conferida pelo texto (se a nota mudou, acha pelo texto; se sumiu, não toca em nada e avisa), com backup da nota fora do vault. `ESTADO.md` e prioridade que citam o item (70% das palavras) ganham `revisar:` no frontmatter, que o hook de sessão mostra à IA até o próximo `/devtrack` reescrever; o índice é refeito na hora. `plan`, `prazo` e `revisao` mexem só em prazo e semana e não propagam.

Segurança: backup do `quadro.md` anterior fora do vault; escrita atômica; vault sensível ou versionado exige `--confirmo`; `quadro: false` no manifesto desliga; descarte em lote exige `--sim`; descartar é mover para `Descartado` (a nota de origem nunca é alterada); privacidade de leitura igual à do hook. Ordem manual dentro da coluna vem da ordem do `quadro.md`. Comandos: `board show|summary|proposals|move|add|discard`.

## 8d. Pendências vivas, ocultas e conciliadas (decisão 011, `scripts/pend.py` e `scripts/reconcile.py`)

Devtrack é retrato de fim de sessão: toda caixa `- [ ]` fica aberta para sempre, a menos que uma sessão posterior a reescreva. Em projetos reais, **a grande maioria dos itens abertos nunca reaparece** numa sessão seguinte. A causa é o processo, e por isso o histórico não é reescrito.

**Regras (`pend.py`, sem modelo, determinístico).** O `board.derive` marca cada cartão com `oculto` e `evidencia`:

| Motivo | Regra |
|---|---|
| `pergunta` | item de **devtrack** terminado em `?` (em CHECKLIST, feature e prioridade, pergunta é verificação real) |
| `narrativo` | item de devtrack que é frase de estado ("nenhum commit feito", "não testado") |
| `repetido` | uma sessão posterior reescreveu o item (semelhança ≥ 0,50, IDF por projeto) e ele segue aberto |
| `superado` | o projeto teve devtrack 14+ dias depois, o item nunca reapareceu **e o `ESTADO.md` e a `prioridade/atual.md` não o citam** (contenção ≥ 0,60 do peso do item) |
| feito por outra redação | uma sessão posterior marcou `[x]` um item com semelhança ≥ 0,50: o cartão vira Feito (`status_origem: evidencia`) |

`build(ocultos=False)` esconde os ocultos; `ocultos=True` traz tudo. **Uma decisão no `quadro.md` sempre vence** o ocultar. Projeto dormido não gera superado (a condição é medida contra o último devtrack, não contra a data de hoje). `xmem.open_items` (hook, digest, insights) lê do quadro, então respeita o que foi fechado ou descartado.

**Conciliação (`xmem.py reconcile <projeto>`).** Confronta as pendências abertas com o git dos repositórios `ativo` do manifesto (`repos:`; `referencia` só com `--incluir-referencias`): **A** hash citado existe, ou commit posterior com o mesmo assunto (≥ 0,50 e 3+ termos); **B** parece tratar do assunto (≥ 0,35, 2+ termos); **C** arquivo citado foi alterado depois (commits com mais de 150 arquivos são ignorados). Só `--aplicar A --sim` grava, com as etiquetas `#ja-feito #reconciliado`. Também lista hashes citados nas notas que não existem em nenhum repositório e avisa de `.git` que o git não reconhece.

**Limite medido num projeto real:** o texto do commit e o arquivo citado confirmam só uma pequena parte do que foi feito. Commit não é o mecanismo principal; é evidência para você decidir. O guarda do estado vivo existe porque 28 superados de 20 a 27/10 ainda estavam vivos em prosa no `prioridade/atual.md`.

## 8e. Semana, prazo e janelas (decisão 012, `scripts/semana.py`)

Funções puras com `hoje` injetável. Semana ISO; `surgiu` só de devtrack (documento vivo carrega a data da migração e vai para o backlog); `semana` explícita ou `surgiu`; `prazo`; `feito-em` (carimbado ao concluir; a conciliação grava a data do commit; fechamento de limpeza, etiqueta `limpeza-*`, fica fora do calendário). Flags por cartão aberto: `sem-prazo`, `no-prazo`, `chegando` (até `quadro-alerta` dias, padrão 3), `hoje`, `atrasado`; sem prazo nunca atrasa. `anotar()` no `build` acrescenta `semana_ef`, `planejado`, `backlog`, `feito_semana`, `flag`, `flag_texto`, `janela`. A revisão semanal propõe por critério (prazo futuro, em andamento, bloqueado, prazo vencido, sem prazo) e só os dois primeiros são mecânicos. Capacidade por semana (`quadro-capacidade`, padrão 7) é aviso, nunca bloqueio, e conta só o que foi planejado explicitamente. Interface: Calendário (abre na última semana com registro), Agenda, Quadro e Lista; visão global com filtro de projeto. `insights --json` traz `prazos`.

## 8c. Grafo, foco e Insights

- **Foco em projeto:** clique no casco ou no nome do projeto aproxima e isola as notas dele (inclui as sem relação); `Esc` ou "← Todos os projetos" restaura câmera e filtros.
- **Clusters** (`xmem.graph_clusters`): componentes de notas de conhecimento do mesmo projeto ligadas por link ou semelhança ≥ 0,30, com ≥ 4 notas; rótulo = termo mais frequente nos títulos. Aparecem com zoom ≥ 1 ou em foco.
- **Tarefas** em Fazendo, Bloqueado e Revisão aparecem como losangos ligados à nota de origem (`graph --json --tarefas` entrega a mesma lista).
- **Busca no corpo:** a interface pergunta ao índice (`hybrid`) e o grafo só mostra notas cujo trecho contém todos os termos digitados.
- **Insights** (`xmem.py insights --json`, `schema_version` 1): atividade, parados, projetos sem devtrack, contradições e saúde do quadro (órfãos, parados em andamento).
- `graph --json`: `{schema_version, nodes, edges[, layout][, tarefas]}`; aresta = `src, dst, type, score, origin, cross`; tipos: `links_to, related_to, supersedes, extends, contradicts, implements, references`.

## 9. Mapa Memora → SecondBrain (verificado no código do Memora, commit 442ca1b)

| Memora (fonte) | Aqui | Decisão |
|---|---|---|
| `hybrid_search_scored` (RRF k=60, 0,6/0,4) | `xmem.hybrid` | adotado |
| `_classify_fact_against_matches`, limiares 0,85/0,35 | `absorb-check` + regra impressa | adotado, recalibrado |
| `_verify_absorb_supersede_llm` (3 sim, piso 0,55, falha segura) | regra dos 3 "sim" nas skills | adotado (o Claude é o verificador) |
| supersessão/linhagem e `follow=active` | `status` + aresta `supersedes`, `--all` | adotado |
| `_update_crossrefs_for_memory` (5 vizinhos, `related_to`) | `rebuild_edges` | adotado |
| `memory_digest` (hits + linhagem + ≤3 saltos + todos) | `xmem.py digest` | adotado |
| `generate_insights` (parado 14 d; fechado 30 d) | `insights`, `/audit` | adotado |
| chunking de documentos (fragmentos buscáveis) | trechos por seção | adotado |
| hook SessionStart (5 hits, ≤1500 caracteres) | `hook-context` | adotado, opt-in |
| `SECRET_PATTERNS` | `absorb-check`, `/audit` | adotado |
| sem tipo automático (130 rotulagens erradas) | tipo só por papel/frontmatter | adotado |
| `memory_create_todo` / `memory_create_issue` (status, prioridade, categoria) | `board` (7 colunas, P0 a P3, etiquetas, bloqueio) | adotado, derivado das caixas; kanban não existe no Memora |
| `memory_clusters` | `graph_clusters` | adotado por projeto, com rótulo |
| `memory_export_graph` (HTML estático) | `graph --json` (dados) | JSON em vez de HTML: serve a IA e integrações |
| perfis de ferramentas (12.700 tokens de esquema) | skills por demanda, sem servidor MCP | desnecessário aqui |
| hook PostToolUse de auto-captura | — | **não adotado**: `/devtrack` já lê o `git log`; captura sem contexto vira ruído (o próprio Memora ressalva isso) |
| `calculate_importance`/`boost` (meia-vida 30 d) | — | **não adotado**: sem contador de acesso nos arquivos; o Memora não usa essa pontuação na busca |
| D1/S3, multi-banco HTTP, API v1, contêineres, gate de escrita, replicador | — | **não adotado**: existem porque o banco é a fonte da verdade; aqui são arquivos |
| chamadas de LLM dentro da ferramenta | — | o Claude da sessão classifica |

## 10. Operação

```bash
scripts/install-tools.sh                         # copia ferramentas e cria o atalho do app
python3 -I "$SB/xmem.py" index [--full]          # (re)indexa; os comandos já sincronizam sozinhos
python3 -I -m unittest discover -s tests         # testes (xmem, interface, integridade)
python3 -I tests/eval_xmem.py                    # qualidade da busca
```

O índice sincroniza por data e tamanho do arquivo; `index --full` reconstrói do zero (~10 s para ~930 notas). Backup: `backup.sh` já inclui `~/GlobalSecondBrain`.

## 11. Limites conhecidos

1. Busca lexical (seção 5).
2. "Itens em aberto" é derivado de caixas `- [ ]` de devtrack, então inclui tarefas antigas nunca marcadas (ruído real; o `/audit` já tratava isso).
3. A atividade das memórias do Claude usa a data de modificação do arquivo (não há data de criação).
4. A interface foi verificada por inicialização e testes de lógica, **não visualmente**; a validação visual é sua.
5. O motor roda em Python 3 com FTS5 do SQLite (presentes no seu sistema).
