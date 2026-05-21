---
name: secondbrain-postmortem
description: |
  Gera um documento de post-mortem de incidente com linha do tempo, causa raiz,
  impacto e plano de ação. Salva no vault do projeto.
  
  Use esta skill sempre que o usuário pedir para:
  - "/postmortem"
  - "documenta o incidente"
  - "cria o post-mortem"
  - "análise do que deu errado"
  - "relatório de incidente"
  - após um bug em produção, outage, deploy problemático ou falha crítica
---

> **Mascote:** imprima o cérebro de `references/mascot.md` com `/postmortem` antes de qualquer outra resposta.


# SecondBrain — Postmortem

Documenta um incidente com a estrutura padrão de post-mortem: o que aconteceu,
por que aconteceu, impacto e o que faremos para não acontecer de novo.

O objetivo não é apontar culpados — é entender o sistema e melhorá-lo.

---

## Passo 1 — Capturar o incidente

**A) O usuário passou contexto junto com o comando:**
Use como ponto de partida.

**B) O usuário só digitou `/postmortem`:**

Pergunte, uma de cada vez:
1. "O que aconteceu? Descreva o incidente em uma frase."
2. "Quando começou e quando foi resolvido?"
3. "Qual foi o impacto? (usuários afetados, funcionalidades indisponíveis, dados perdidos...)"

---

## Passo 2 — Gerar número sequencial

```bash
ls *SecondBrain/postmortems/ 2>/dev/null | wc -l
```

Se a pasta não existir, crie e comece do 001.

---

## Passo 3 — Gerar o documento

Nome do arquivo: `{NNN} - {data-de-hoje} - {Título do incidente}.md`

```markdown
---
data: {data-de-hoje}
status: rascunho
severidade: {P1 / P2 / P3}
---

# Post-mortem {NNN} — {Título do incidente}

> **Status:** Rascunho — preencher após análise completa.

---

## Resumo

{1-2 frases descrevendo o incidente, impacto e resolução. Deve ser legível por quem
 não acompanhou o incidente.}

---

## Linha do tempo

| Horário | Evento |
|---|---|
| {HH:MM} | {O que aconteceu} |
| {HH:MM} | {Quando foi detectado e por quem} |
| {HH:MM} | {Quando a investigação começou} |
| {HH:MM} | {Ações tomadas durante a mitigação} |
| {HH:MM} | {Quando foi resolvido} |

---

## Impacto

- **Duração:** {tempo entre início e resolução}
- **Usuários afetados:** {estimativa ou "desconhecido"}
- **Funcionalidades afetadas:** {lista}
- **Dados afetados:** {sim/não — detalhar se sim}

---

## Causa raiz

{Explicação técnica de por que o incidente aconteceu. Seja específico.
 "Erro humano" não é causa raiz — é sintoma. Vá fundo: por que foi possível
 esse erro humano acontecer?}

### Causas contribuintes

{Outros fatores que tornaram o incidente mais grave ou mais difícil de detectar.}

---

## O que foi bem

{O que funcionou durante a resposta ao incidente — monitoramento que alertou a tempo,
 rollback rápido, comunicação eficiente. Honesto, não forçado.}

---

## O que pode melhorar

{O que tornou o incidente mais longo ou mais grave do que precisava ser.}

---

## Plano de ação

| Ação | Responsável | Prazo | Status |
|---|---|---|---|
| {Ação preventiva específica} | {pessoa ou time} | {data} | 🔲 Pendente |
| {Ação de detecção — alertas, logs} | {pessoa ou time} | {data} | 🔲 Pendente |
| {Ação de processo} | {pessoa ou time} | {data} | 🔲 Pendente |

---

## Lições aprendidas

{O que este incidente ensinou sobre o sistema, o processo ou a equipe.
 Escrever em positivo: "aprendemos que X" não "erramos em Y".}
```

---

## Regras

- **Sem culpados.** Post-mortem é análise de sistema, não julgamento de pessoas.
- **Causa raiz real.** "Esqueci de testar" → "não havia cobertura de teste para esse caso" → "nosso processo de review não inclui X".
- **Plano de ação com dono e prazo.** Ação sem responsável não é ação.
- **Use o idioma do projeto** conforme `feedback_language.md`.

---

## Passo 4 — Confirmar e salvar

Mostre o documento gerado.
Aguarde aprovação do usuário — post-mortems devem ser revisados antes de salvar.

```
✓ Post-mortem salvo: {NomeProjeto}SecondBrain/postmortems/{NNN} - {data} - {Título}.md
```
