# CLAUDE.md — SecondBrain

## Contexto do projeto

Se existir um arquivo `PROJECT_CONTEXT.md` na raiz deste projeto, leia-o **imediatamente e completamente** antes de qualquer outra ação ou resposta.

Esse arquivo contém o mapa de contexto gerado pela skill `/analyze` — stack, arquitetura, convenções, estado atual e prioridades. Ele existe para que você opere com autonomia sem precisar re-explorar o projeto do zero a cada sessão.

```bash
cat PROJECT_CONTEXT.md 2>/dev/null
```

Se o arquivo não existir, o usuário ainda não rodou `/analyze`. Nesse caso, você pode sugerir:
> "Não encontrei um `PROJECT_CONTEXT.md`. Quer que eu rode `/analyze` para mapear o projeto e criar esse contexto?"

## Idioma

Responda sempre em **português (Brasil)**, exceto para termos técnicos sem tradução natural (ex: `useState`, `middleware`, `endpoint`).

## Skills disponíveis

Este projeto usa o **SecondBrain** — um conjunto de skills para memória persistente de projetos.
As skills ficam em `skills/` e são ativadas pelo usuário com `/nome-da-skill`.

Principais skills:
- `/analyze` — análise completa e estratégica do projeto (gera/atualiza `PROJECT_CONTEXT.md`)
- `/feature` — cria spec de funcionalidade com critérios de aceitação
- `/devtrack` — registra sessão de trabalho
- `/decision` — documenta decisões técnicas
- `/audit` — audita a saúde do SecondBrain
- `/context` — resume o estado atual do projeto para o Claude
- `/readme` — gera ou atualiza o README

## Commits

Não adicione `Co-Authored-By: Claude` nas mensagens de commit.
