# Modelos do /analyze

Texto longo tirado de `skills/secondbrain-analyze/SKILL.md` para economizar contexto: a skill aponta para cada modelo e você o abre só quando for gerar o arquivo correspondente.


## Modelo 1 — Passo 3 — Gerar o relatório de análise

```markdown
# Análise Completa do Projeto: {Nome do Projeto}

**Data:** {data de hoje}
**Stack detectada:** {tecnologias principais}
**Maturidade estimada:** {MVP / Alpha / Beta / Produção / Legado}
**Escopo da análise:** {o que foi avaliado e o que ficou fora}

---

## 1. Visão Geral do Projeto

**Objetivo principal:** {o que o projeto faz em uma frase}

**Problema que resolve:** {dor ou necessidade que justifica a existência do projeto}

**Público-alvo:** {quem usa ou deveria usar}

**Proposta de valor:** {o que diferencia ou torna o projeto útil}

**Maturidade do produto:** {avaliação honesta do estágio atual, com evidências do código}

---

## 2. Arquitetura do Sistema

{Descreva a arquitetura geral: monolito, microserviços, serverless, JAMstack, etc.}

**Padrões detectados:** {MVC, CQRS, event-driven, layered, etc.}

**Separação de responsabilidades:** {como está distribuída e onde há mistura indevida}

**Escalabilidade:** {horizontal, vertical, gargalos estruturais}

**Manutenibilidade:** {facilidade de entender, modificar e testar}

**Problemas arquiteturais:**
- {problema específico com localização no código}
- {problema específico}

**Sugestões de melhoria:**
- {sugestão concreta e acionável}

---

## 3. Backend

{Avalie organização do código, estrutura de serviços, qualidade das APIs, controllers, middlewares,
autenticação, autorização, segurança, performance, tratamento de erros, logs, cache, filas,
concorrência e escalabilidade horizontal.}

*Omitir ou abreviar se não houver backend.*

---

## 4. Banco de Dados e Dados

{Avalie modelagem de dados, relacionamentos, normalização, performance das consultas, índices,
integridade dos dados, estratégia de armazenamento, escalabilidade e consistência.}

*Omitir ou abreviar se não houver banco de dados.*

---

## 5. Frontend

{Avalie estrutura da aplicação, organização de componentes, reutilização, estado global, performance,
responsividade, qualidade do código, experiência do usuário e fluxos de navegação.}

*Omitir ou abreviar se não houver frontend.*

---

## 6. UX/UI e Design

{Avalie qualidade visual, hierarquia, consistência, design system, acessibilidade, tipografia,
espaçamento, cores, usabilidade, microinterações e experiência geral do usuário.}

*Para projetos CLI ou de biblioteca: avalie ergonomia da API e experiência de uso da ferramenta.*

---

## 7. Funcionalidades

**Funcionalidades existentes:**
{Liste o que existe e funciona}

**Coerência entre funcionalidades:**
{As features fazem sentido juntas? Há sobreposição ou lacuna?}

**Funcionalidades ausentes:**
{O que seria óbvio ter mas está faltando, dado o objetivo do projeto}

**Prioridades de evolução:**
{O que deveria ser implementado primeiro}

---

## 8. Segurança

{Avalie vulnerabilidades potenciais (OWASP Top 10 relevantes), proteção de dados, segurança da
autenticação, exposição de informações sensíveis, riscos críticos e boas práticas ausentes.}

**Riscos críticos identificados:**
- {risco com nível de severidade: Crítico / Alto / Médio / Baixo}

---

## 9. Performance

{Avalie gargalos detectados, performance de renderização, queries lentas, latência de API,
estratégias de otimização presentes ou ausentes: caching, lazy loading, compressão, CDN.}

---

## 10. DevOps e Infraestrutura

{Avalie deploy, CI/CD, containers, monitoramento, logs, observabilidade, escalabilidade,
gestão de ambientes, secrets e recuperação de falhas.}

---

## 11. Qualidade de Código

{Avalie legibilidade, organização, Clean Code, SOLID, padrões de projeto, dívida técnica,
complexidade ciclomática, reutilização e padronização.}

---

## 12. Testes

{Avalie cobertura estimada, presença de testes unitários, de integração e E2E, estratégia
de testes adotada e confiabilidade do suite de testes.}

---

## 13. Produto e Negócio

{Avalie potencial de mercado, diferenciais, possibilidades de monetização, mecanismos de
retenção, escalabilidade do negócio e vantagem competitiva.}

---

## 14. SEO e Acessibilidade

{Avalie SEO técnico, estrutura semântica, Core Web Vitals, acessibilidade WCAG, compatibilidade mobile.}

*Para projetos não-web: avalie discoverabilidade, qualidade da documentação, CLI UX.*

---

## 15. Análise Estratégica

**Principais riscos (priorizados):**
| Risco | Severidade | Probabilidade | Área |
|-------|------------|---------------|------|
| {risco} | Crítico/Alto/Médio/Baixo | Alta/Média/Baixa | {área} |

**Principais oportunidades:**
| Oportunidade | Impacto | Esforço |
|--------------|---------|---------|
| {oportunidade} | Alto/Médio/Baixo | Alto/Médio/Baixo |

**Quick wins (< 1 semana):**
- {ação concreta de alto impacto, baixo esforço}

**Melhorias de alto impacto (1-3 meses):**
- {melhoria estrutural significativa}

---

## 16. Resultado Final

### Nota Geral: {X}/10

{Justificativa da nota em 2-3 frases honestas, baseadas nas evidências encontradas.}

---

### Os 10 Maiores Problemas

| # | Problema | Severidade | Área |
|---|----------|------------|------|
| 1 | {problema específico, com referência ao código se possível} | Crítico | {área} |
| 2 | ... | Alto | ... |
| 3 | ... | Alto | ... |
| 4 | ... | Médio | ... |
| 5 | ... | Médio | ... |
| 6 | ... | Médio | ... |
| 7 | ... | Baixo | ... |
| 8 | ... | Baixo | ... |
| 9 | ... | Baixo | ... |
| 10 | ... | Baixo | ... |

---

### Os 10 Maiores Pontos Fortes

| # | Ponto Forte | Área |
|---|-------------|------|
| 1 | {ponto forte específico, com evidência do código} | {área} |
...

---

### Plano de Evolução Técnica e de Produto

**Curto prazo — 0 a 4 semanas (Quick Wins)**
- [ ] {ação concreta e acionável}
- [ ] ...

**Médio prazo — 1 a 3 meses (Alto Impacto)**
- [ ] {melhoria estrutural}
- [ ] ...

**Longo prazo — 3 a 12 meses (Transformacional)**
- [ ] {mudança arquitetural ou de produto de grande impacto}
- [ ] ...

---

*Análise gerada por Claude Code via SecondBrain — revisão humana recomendada antes de priorização.*
```


## Modelo 2 — Sempre gere este arquivo após o relatório — sem precisar perguntar ao usuário.

```markdown
# PROJECT_CONTEXT.md
<!-- Gerado por /analyze em {data}. Não edite manualmente — rode /analyze para atualizar. -->

## O que é este projeto

{1-2 frases diretas: o que faz, para quem, em que estágio está.}

## Stack

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| {Frontend/Backend/DB/Infra} | {tech} | {versão se conhecida} |

## Arquitetura

{2-4 frases sobre a estrutura geral: padrão arquitetural, separação de camadas,
como os módulos se relacionam. Cite os diretórios-chave.}

## Convenções estabelecidas

{Liste as convenções que o Claude deve seguir ao editar este projeto:
 linguagem dos commits, idioma do código, padrão de nomenclatura, estilo de componentes,
 onde ficam os testes, como se faz autenticação, etc.
 Seja específico — não genérico.}

- {convenção concreta}
- {convenção concreta}

## Estado atual (em {data})

**Maturidade:** {MVP / Alpha / Beta / Produção / Legado}
**Nota geral:** {X}/10

**O que está funcionando bem:**
- {ponto forte 1}
- {ponto forte 2}

**Principais débitos/riscos:**
- {problema crítico ou de alta prioridade}
- {problema crítico ou de alta prioridade}

## Próximas prioridades

{O que está na fila de trabalho, baseado no plano de evolução da análise.
 Use formato de checklist para que o Claude possa acompanhar progresso.}

- [ ] {prioridade de curto prazo}
- [ ] {prioridade de curto prazo}
- [ ] {prioridade de médio prazo}

## Onde encontrar o quê

| O quê | Onde |
|-------|------|
| Entry point principal | `{caminho}` |
| Configuração de ambiente | `{caminho}` |
| Testes | `{caminho}` |
| Documentação de features | `{caminho no vault}` |
| Análise completa | `{vault}/{analise}/Análise Completa — {data}.md` |
```
