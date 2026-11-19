# Onde cada fato vive (uma fonte por fato)

O estado de um projeto aparecia em sete lugares. Esta tabela diz qual é a **fonte** de cada fato e o que é **derivado** (pode ser regerado e nunca é editado para "corrigir" a fonte). Quando duas skills respondem a mesma pergunta, ambas leem a fonte.

| Fato | Fonte (única) | Derivado ou visão |
|---|---|---|
| O que está aberto, em andamento, bloqueado, com prazo | o quadro: caixas `- [ ]` das notas + decisões em `quadro.md` (`xmem.py board show`) | `prioridade/atual.md` (visão sem caixas), `/resume`, `/standup`, `/context` |
| O que foi feito numa sessão | o devtrack do dia (nunca reescrito) | `ESTADO.md` ("Agora") |
| Onde o projeto está e o próximo passo | `ESTADO.md` (reescrito a cada `/devtrack`) | o hook de sessão |
| Por que uma escolha foi feita | a decisão em `decisions/` | índice, grafo |
| Regras e convenções do repositório | `CLAUDE.md` | memória do Claude (só o que o `CLAUDE.md` não diz) |
| Mapa de arquitetura e stack | `PROJECT_CONTEXT.md` (gerado por `/analyze`) | |
| Preferências e correções do usuário | memória do Claude (`memory/`) | |
| Prazo e semana de um cartão | campos `prazo::` e `semana::` no `quadro.md` | calendário e agenda |

Regras:
- **Pergunta "o que está aberto?"**: responda sempre pelo quadro (`board show --project <p>`). Sem o motor, use os `[ ]` do último devtrack e do CHECKLIST, avisando que podem estar velhos.
- **Nunca escreva caixa `- [ ]` numa visão** (prioridade, resumo, estado): o quadro a leria de volta como pendência nova.
- **O estado vivo que protege item de virar "sem-sinal"** é `ESTADO.md`, `prioridade/atual.md`, a memória do Claude e o `CLAUDE.md`. Se um item ainda vale, cite-o num deles.
- Em conflito entre uma visão e a fonte, a fonte vence e a visão é regerada.
