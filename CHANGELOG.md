# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões seguem o `plugin.json`. A fonte é o `git log` e os devtracks do vault do plugin.

## [0.7.0] - 2026-11-18

### Adicionado
- Página **Insights** na interface (atividade por projeto, itens parados, projetos sem devtrack, contradições, saúde do quadro) e `xmem.py insights --json`.
- Grafo: **linha do tempo**, filtro de **etiquetas**, **busca no corpo das notas** (precisa: o trecho contém todos os termos) e **clusters temáticos** por projeto (`xmem.graph_clusters`).
- Quadro: **criar cartão** pela interface, **reordenar** arrastando (a ordem fica no `quadro.md`), modo **Lista**, filtro de **etiqueta**, atalhos (`n`, `/`, `l`, `Esc`) e estados vazios.
- `/learn`, `/decision` e `/devtrack` passam a orientar arestas tipadas (`estende`, `contradiz`, `implementa`, `referencia`) e a atualização do quadro ao fechar a sessão.
- Capturas de tela no README, feitas sobre um vault fictício.

### Corrigido
- Reindexar uma nota alterada podia quebrar o índice (`IntegrityError`) quando era a última indexada: os trechos eram apagados da tabela `chunks` mas não do FTS. Esquema do índice passou a v4 (reconstrução automática; o índice é derivado).

## [0.6.0] - 2026-11-18

### Adicionado
- Skill **`/board`** (21ª) e `scripts/board.py`: quadro kanban com cartões derivados das caixas `- [ ]` e decisões em `quadro.md` por projeto (formato do Obsidian Kanban), backup fora do vault, confirmação para vault sensível ou versionado, descarte em lote com `--sim`.
- Página **Quadro** na interface (arrastar e soltar, detalhe do cartão, visão geral por projeto, triagem em lote) no lugar de "Pendências".
- **Foco em projeto** no grafo: clicar no casco ou no nome do projeto aproxima e isola as notas dele; `Esc` volta.
- Tarefas em andamento como losangos no grafo; `graph --json` com `schema_version` e `--tarefas`; hook de sessão e `insights` com o quadro.
- Interface redesenhada: tokens únicos (`gui/theme.py`, claro e escuro), barra lateral de navegação, busca com escopo, cartões de resultado, leitor com coluna Contexto, grafo com filtros e detalhe encaixados, arestas tipadas com cor e traço.

### Corrigido
- Animação de câmera do grafo (`fit`, ir até a nota) só avançava quando o mouse mexia.
- "Ajustar à tela" deixava o mapa pequeno por causa de nós isolados na periferia (passou a enquadrar pelos percentis 3–97%).

## [0.5.0] - 2026-11-16

### Adicionado
- Motor de **memória cruzada** (`scripts/xmem.py`): índice derivado SQLite + FTS5, busca híbrida (RRF), linhagem, arestas tipadas, `recall`, `digest`, `absorb-check`, `patterns`, `insights`, `dups`.
- Skills `/recall` e `/patterns`; `absorb-check` em `/learn` e `/decision`.
- Interface nativa GTK4 + libadwaita + WebKitGTK (busca, leitor seguro, grafo, pendências).
- Grafo com layout pré-calculado em Python (ilhas por projeto, cache por hash), arestas automáticas sem duplicata.
- Vault global `~/GlobalSecondBrain/`, backup em HD externo (`/backup`, só copia), hook de início de sessão (opt-in), `check_vault.py`.
- Manifesto `_secondbrain.md` (esquema 2), migração assistida e aditiva de vaults existentes, `ESTADO.md`, decisões em MADR.
- Logo: cérebro cuja rede neural é o S do nome.

## [0.1.0 – 0.2.0] - 2026-05-21 a 2026-05-22

### Adicionado
- Suite inicial de skills: `setup`, `devtrack`, `resume`, `learn`, `decision`, `context`, `priority`, `feature`, `audit`, as skills de documentação (`changelog`, `onboarding`, `readme`, `release`, `rfc`, `postmortem`, `standup`) e `/analyze`; `--import-history` no setup.
