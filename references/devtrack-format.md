# Formato padrão de devtrack

Arquivo de referência para a skill `secondbrain:devtrack`.

## Nome do arquivo

```
YYYY-MM-DD - Título descritivo.md
```

O título deve descrever o que foi feito, não o que estava planejado.  
Exemplos: `2026-05-20 - Implementação DocumentMoreResults.md`  
Não: `2026-05-20 - Sessão de trabalho.md`

---

## Estrutura base (sempre presente)

```markdown
# YYYY-MM-DD — Título descritivo

## O que foi feito

{Narrativa do que foi implementado, investigado ou decidido nesta sessão.
 Pode ser organizado em tópicos numerados se houver múltiplas iniciativas.}

---

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `caminho/do/arquivo.ts` | Descrição da mudança |
| `caminho/do/outro.html` | Descrição da mudança |

## Status

- [x] Tarefa concluída
- [x] Outra tarefa concluída
- [ ] Pendência em aberto
- [ ] Outra pendência
```

---

## Seções opcionais (adicionar quando aplicável)

### Bugs corrigidos (quando a sessão corrigiu bugs)

```markdown
## Bugs corrigidos

### Bug 1 — nome curto do bug

**Problema:** descrição clara do sintoma observado.

**Causa:** explicação técnica do porquê acontecia.

**Correção:**
`caminho/do/arquivo` — o que foi mudado e por quê.
```

### Decisões técnicas (quando foram feitas escolhas não óbvias)

```markdown
## Decisões técnicas

### Nome da decisão

**Contexto:** por que precisou decidir algo aqui.

**Alternativas consideradas:**
- Opção A — por que foi descartada
- Opção B — por que foi descartada

**Decisão:** o que foi escolhido e por quê.
```

### Pendências específicas (quando há ações claras para a próxima sessão)

```markdown
## Próximos passos

1. Ação específica com contexto suficiente para retomar sem reler tudo
2. Outra ação com o arquivo ou componente que precisa ser tocado
```

---

## Regras de ouro

- **Seja específico sobre arquivos.** Um devtrack sem caminhos de arquivo é inútil.
- **Capture o "por quê".** O "o quê" está no git diff. O "por quê" só existe se for escrito agora.
- **Status com checkboxes.** Permite que `/resume` e `/context` extraiam pendências automaticamente.
- **Não resumir demais.** Um devtrack longo e detalhado vale muito mais do que um parágrafo vago.
- **Sessões de análise/planejamento** (sem código) também merecem devtrack — marque com `> Sessão de análise. Sem implementação de código.` no topo.
