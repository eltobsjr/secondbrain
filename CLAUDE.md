# CLAUDE.md — SecondBrain

## Contexto do projeto

Se existir um arquivo `PROJECT_CONTEXT.md` na raiz deste projeto, leia-o **imediatamente e completamente** antes de qualquer outra ação ou resposta.

Esse arquivo contém o mapa de contexto gerado pela skill `/analyze` — stack, arquitetura, convenções, estado atual e prioridades. Ele existe para que você opere com autonomia sem precisar re-explorar o projeto do zero a cada sessão.

```bash
cat PROJECT_CONTEXT.md 2>/dev/null
```

Se o arquivo não existir, o usuário ainda não rodou `/analyze`. Nesse caso, você pode sugerir:
> "Não encontrei um `PROJECT_CONTEXT.md`. Quer que eu rode `/analyze` para mapear o projeto e criar esse contexto?"

## Começar

Se existir `SecondBrainSecondBrain/` (vault pessoal do plugin, fora do git), leia o `ESTADO.md` dele antes de trabalhar; o devtrack e as decisões (`decisions/001` a `013`) explicam o porquê das escolhas.

## Idioma

Responda sempre em **português (Brasil)**, exceto para termos técnicos sem tradução natural (ex: `useState`, `middleware`, `endpoint`).

## Skills disponíveis

Este projeto usa o **SecondBrain** — um conjunto de 21 skills para memória persistente de projetos.
As skills ficam em `skills/` e são ativadas pelo usuário com `/nome-da-skill`. A lista completa e o que cada uma faz estão no `README.md`.

Principais skills:
- `/analyze` — análise completa e estratégica do projeto (gera/atualiza `PROJECT_CONTEXT.md`)
- `/feature` — cria spec de funcionalidade com critérios de aceitação
- `/devtrack` — registra sessão de trabalho (também reescreve o `ESTADO.md` e reindexa)
- `/decision` — documenta decisões técnicas (formato MADR)
- `/recall` — procura nos outros projetos uma solução para o problema atual (memória cruzada)
- `/patterns` — consolida padrões que se repetem entre projetos
- `/board` — quadro kanban das pendências (cartões derivados das caixas + `quadro.md` por projeto)
- `/audit` — audita a saúde do SecondBrain
- `/context` — resume o estado atual do projeto para o Claude
- `/readme` — gera ou atualiza o README

## Trabalhando neste repositório

- As ferramentas ficam em `scripts/` (motor `xmem.py`, instalador `install-tools.sh`) e a interface em `gui/`.
- Antes de propor commit, rode `python3 -I -m unittest discover -s tests`.
- Detalhes de arquitetura em `docs/ARQUITETURA-MEMORIA-CRUZADA.md`.
- O logo é gerado por `assets/logo/build_logo.py`; não edite os SVGs à mão.
- **Este repositório é público e só tem a ferramenta.** Nada dos projetos do dono pode entrar nele: nome de projeto, de pessoa ou de empresa, caso de teste real, número de uso, caminho da pasta pessoal. Use exemplos fictícios (`app-loja`, `projeto-exemplo`). O que é pessoal fica só no computador dele (`~/.local/share/secondbrain/`, os vaults e `SecondBrainSecondBrain/`). A guarda `scripts/guard_publico.py` barra commit e push; se ela reclamar, troque o texto por um exemplo fictício em vez de contorná-la.

## Commits

Não adicione `Co-Authored-By: Claude` nas mensagens de commit.
