---
name: secondbrain-devtrack
description: |
  Gera o log de sessão (devtrack) do projeto atual e salva no vault SecondBrain.
  
  Use esta skill sempre que o usuário pedir para:
  - "/devtrack"
  - "gerar o devtrack"
  - "criar o log da sessão"
  - "registrar o que foi feito"
  - "documentar a sessão"
  - ao final de uma sessão de implementação
  
  Também PROPOR (perguntando antes de gravar) quando o usuário disser "terminamos", "por hoje é isso",
  "pode encerrar" ou qualquer sinal de encerramento de sessão sem ter gerado o devtrack.
---

# SecondBrain — Devtrack

> **Vault:** antes de ler ou gravar, resolva o vault e os caminhos conforme `references/vault-resolve.md` (manifesto `_secondbrain.md`; se faltar, migração assistida sem mover nada). Neste arquivo, `{vault}` é o vault e `{devtrack}`, `{estado}` etc. são os caminhos que o manifesto dá a cada papel.

Gera o log de sessão no vault do projeto. O devtrack é um retrato de fim de sessão e **nunca é reescrito depois**. A parte mecânica fica no motor; aqui entra só o julgamento.

## Passo 1 — Rodar o fechamento (mecânico, somente leitura)

```bash
python3 -I "${SB:-$HOME/.local/share/secondbrain/bin}/xmem.py" session-close <projeto>
```

Entrega de uma vez: data, último devtrack e lacuna, aviso se já existe devtrack de hoje, git da sessão, quadro (abertos), conciliação com o git, revisão semanal e agenda. Sem o motor, use `date`, `ls {vault}/{devtrack}/ | sort | tail -1`, `git status --short` e `git log --since="10 hours ago"`.

- **Lacuna maior que 3 dias:** avise ("o último devtrack foi em {data}") e ofereça um devtrack do período, com o git log como fonte.
- **Já existe devtrack de hoje:** acrescente a ele em vez de criar outro.
- **Pendências da sessão anterior:** pergunte **uma vez, em lote**, o destino de cada uma: feito, segue ou descartado (com o motivo). O que o git confirma (nível A do `reconcile`) pode ser proposto como feito; B e C só se o usuário concordar. Registre com `board move <projeto> <id> feito|descartado|bloqueado --bloqueado-por "<motivo>"`; o que segue e tem data recebe `board plan <projeto> <id> --semana esta|proxima --prazo +3d`. Em vault sensível ou versionado o comando pede `--confirmo`: pergunte antes.

## Passo 2 — Título e arquivo

Infira o título pelo que foi feito (a feature ou o sintoma principal; "análise" se não houve código). Não pergunte. Evite "Sessão de trabalho", "Fixes". Arquivo: `{vault}/{devtrack}/YYYY-MM-DD - {Título}.md`. Se não achar o vault, procure no diretório pai ou pergunte.

## Passo 3 — Escrever

Formato completo e seções opcionais (Bugs corrigidos, Decisões técnicas, Próximos passos) em `references/devtrack-format.md`. Mínimo:

```markdown
---
tipo: devtrack
data: YYYY-MM-DD
commits: [hashes curtos da sessão]
---

# YYYY-MM-DD — {Título}

## O que foi feito
{narrativa com o "por quê"; o git diff já tem o "o quê"}

## Arquivos modificados
| Arquivo | Mudança |
|---|---|

## Status
- [x] concluído
- [ ] pendência em aberto
```

**Modo curto** (poucos arquivos, nenhuma decisão, nenhum bug): só `O que foi feito`, `Status` e, se houver, `Próximos passos`. Sessão sem código: `> Sessão de análise e planejamento. Sem implementação de código.` Respeite `nomes.devtrack` e `campos-extra.devtrack` do manifesto.

**Onde vai a pendência.** Caixa `- [ ]` só para o que ainda vai ser feito. Pergunta (`...?`), frase de estado ("nenhum commit feito", "não testado") e etapa de procedimento vão em texto, não em caixa. Tarefa nova que você assume ganha prazo (`board plan` ou `board prazo`); sem prazo aparece como "sem prazo", nunca como atrasada. O que segue vivo vai também no `ESTADO.md`: se o estado vivo cita o item ele continua aberto; se não cita e ele não reaparece em 14 dias de projeto, o quadro o oculta como sem-sinal (`references/fontes-de-verdade.md`).

## Passo 4 — Atualizar o que deriva do devtrack

1. **Quadro:** os `- [ ]` do devtrack já aparecem como cartões. O concluído nesta sessão vai para Feito (`board move`) ou vira `- [x]` no devtrack seguinte; o bloqueado vai para `bloqueado`. Projeto sem `quadro.md` e sem uso do quadro: pule.
2. **`ESTADO.md`** (papel `estado`, ou módulo `estado` ligado): **reescreva inteiro** conforme `references/estado-format.md` (Agora, Próximo passo, Bloqueios, Fatos voláteis com data). Projeto sem o módulo: pule sem perguntar.
3. **Índices** (falham em silêncio se os scripts faltarem; o `/audit` avisa índice velho):

```bash
python3 -I "${SB:-$HOME/.local/share/secondbrain/bin}/build_index.py" {vault}     # se o vault tem o papel `indice`
python3 -I "${SB:-$HOME/.local/share/secondbrain/bin}/xmem.py" index 2>/dev/null || true
```

## Passo 5 — Confirmar

```
✓ Devtrack salvo: {vault}/{devtrack}/YYYY-MM-DD - {Título}.md
✓ ESTADO.md atualizado            (se atualizou)
Pendências registradas: - {as caixas abertas}
```

Não mostre o conteúdo completo; o usuário abre no Obsidian.
