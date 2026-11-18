# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões seguem o `plugin.json`. A fonte é o `git log` e os devtracks do vault do plugin.

## [0.8.0] - 2026-11-18

### Adicionado
- CI no GitHub Actions (`.github/workflows/tests.yml`): suíte do motor em Python 3.11 e 3.13; job da interface com GTK do sistema, informativo até passar no runner.
- `tests/eval_xmem.py --auto [N]`: consultas de item conhecido geradas do índice real (sem gravar conteúdo no git, sem imprimir texto de vault sensível), `--save` para linha de base com diferença nas execuções seguintes, e `--local` para casos escritos à mão fora do repositório.
- Aviso no hook de sessão quando a sessão carregou uma versão do plugin mais antiga que a instalada (`xmem.plugin_version_notice`).
- README: guia "Qual usar quando" para `/context`, `/resume`, `/standup`, `/board` e `/priority`.
- **Pendências vivas (decisão 011).** `scripts/pend.py` e o `board` passam a ocultar por padrão, sem apagar, o que não é pendência viva: `pergunta` e `narrativo` (só em devtrack), `repetido` e `superado` (o projeto seguiu 14+ dias e nem o `ESTADO.md` nem a `prioridade/atual.md` citam o item). Item que uma sessão posterior marcou `[x]` com outra redação vira Feito (`status_origem: evidencia`). `board show --ocultos`, `board summary` com a contagem de ocultos, `build(ocultos=True)`, e `ocultos_por_projeto` no `insights --json`. Uma decisão no `quadro.md` sempre vence.
- **`xmem.py reconcile <projeto>`** (`scripts/reconcile.py`): confronta as pendências com o git em três níveis de evidência; só o A fecha (`--aplicar A --sim`, etiquetas `#ja-feito #reconciliado`). Lista hashes citados nas notas que não existem em nenhum repositório e avisa de `.git` que o git não reconhece. Commits com mais de 150 arquivos não valem como evidência de arquivo.
- **`repos:` no manifesto** (e `_vault.read_repos`/`detectar_repos`): repositórios `ativo` ou `referencia`; repositório antigo só entra sob pedido. `infer_manifest.py` sugere o bloco.
- `/devtrack` ganha o Passo 0 (concilia a sessão anterior ao abrir) e a regra de onde vai a pendência; `/audit`, `/context`, `/priority` e `/board` passam a usar o quadro filtrado.
- Testes: `tests/test_pend.py` (20, com repositórios git temporários).
- **Calendário por semana, prazo e janelas (decisão 012).** `scripts/semana.py` (semana ISO, flags `sem-prazo`, `no-prazo`, `chegando`, `hoje`, `atrasado`, janelas, revisão semanal, capacidade) e campos `semana::`, `prazo::` e `feito-em::` no `quadro.md`. Dentro do prazo nunca é atrasado, e sem prazo nunca atrasa. Comandos `board semana` (abre na última semana com registro), `board agenda`, `board plan`, `board prazo` e `board revisao`. Concluir carimba `feito-em`; a conciliação grava a data do commit. Manifesto: `quadro-alerta:` (dias, padrão 3) e `quadro-capacidade:` (por semana, padrão 7, 0 desliga; só avisa).
- Interface: a página Quadro abre no **Calendário** (faixa de semanas, cabeçalho do sprint, arrastar para uma semana planeja), com **Agenda**, Quadro, Lista e Projetos, filtros por situação e projeto, e visão global. Detalhe do cartão com prazo (data), semana e situação. Insights ganha o cartão **Prazos**. O hook de sessão e `insights --json` informam atrasados, vencendo hoje e chegando.
- Testes: `tests/test_semana.py` (23, com data fixa), incluindo a sintaxe do JS das páginas.

### Alterado
- "Parado" passa a valer só para item que veio de **devtrack** (retrato de sessão) e que não tem prazo. Para item de CHECKLIST, feature ou prioridade a idade é a do documento, não de esquecimento, e com prazo quem avisa é a flag. Vale no quadro, nos insights, no hook e no `digest`.
- `xmem.open_items` (hook de sessão, `digest`, `insights`) passa a ler do quadro: o que foi fechado ou descartado no `quadro.md` e o que o motor oculta não conta mais como pendência aberta.

### Corrigido
- O número de linha que o cartão mostra ("Origem: nota, linha N") contava a partir do corpo da nota, sem o frontmatter, e não batia com o arquivo. Agora é a linha do arquivo (esquema do índice v5, reconstrução automática).
- O instalador (`install-tools.sh`) não copiava `semana.py`, e a cópia instalada, que a interface e o hook usam, quebrava no import. Agora um teste exige que todo script do repositório esteja na lista.
- Privacidade: `/patterns` mostrava "Termos em comum" derivados do conteúdo de notas de vaults com `crossmem: titulos`. Agora os termos saem só de notas com política `completo`, e só quando há ao menos duas. Lógica extraída para `xmem.patterns_data`, com teste.
- README: contagem de testes defasada.

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
