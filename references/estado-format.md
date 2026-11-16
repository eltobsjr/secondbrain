# ESTADO.md — retrato curto do projeto

Uma página, **reescrita** (não acumulada) pelo `/devtrack` e pelo `/priority`. É o que `/context` e o início de sessão leem primeiro; o devtrack completo só é aberto sob demanda. Caminho: papel `estado` do manifesto (padrão `{vault}/ESTADO.md`).

Limite: ~40 linhas. Se passar, comprima — detalhe pertence ao devtrack.

```markdown
---
tipo: estado
atualizado: AAAA-MM-DD
ultimo-devtrack: "AAAA-MM-DD - Título"
---

# Estado — {Projeto}

## Agora
{1-3 linhas: em que ponto o trabalho está.}

## Próximo passo
{Uma ação específica, com arquivo/componente.}

## Bloqueios e dependências
- {o que impede avanço, quem precisa agir; ou "nenhum"}

## Fatos voláteis
- {fato que muda} (em AAAA-MM) — fonte: {arquivo/comando/URL}
```

Regras:
- Sempre sobrescrever o arquivo inteiro; o histórico fica nos devtracks e no git.
- Cada fato volátil tem data ou aponta para a fonte viva.
- Não duplique pendências: aponte para `{prioridade}`.
