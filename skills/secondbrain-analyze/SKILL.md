---
name: secondbrain-analyze
description: |
  Realiza uma análise completa, profunda e estratégica do projeto — técnica, arquitetural,
  funcional, visual e de produto. Identifica pontos fortes, gargalos, riscos, inconsistências
  e oportunidades de melhoria. Produz um relatório estruturado em 16 dimensões com nota geral,
  top 10 problemas, top 10 pontos fortes e plano de evolução técnica e de produto.
  
  Use esta skill sempre que o usuário pedir para:
  - "/analyze"
  - "/analyse"
  - "analisa o projeto"
  - "faz uma análise completa"
  - "revisão técnica do projeto"
  - "auditoria do produto"
  - "avalia a arquitetura"
  - "quais são os problemas do projeto"
  - "o que pode melhorar no projeto"
  - "análise estratégica"
  - "pontos fortes e fracos do projeto"
  - "nota para o projeto"
  - "o que está bom e o que está ruim"
  - quando o usuário quiser uma visão global e crítica do estado atual do projeto
---

> **Mascote:** execute `references/mascot.md` — rode o script `scripts/mascot.py analyze` antes de qualquer outra resposta. Se Python não estiver disponível, use o fallback estático do mascot.md.


# SecondBrain — Analyze

Análise completa, profunda e estratégica do projeto — técnica, arquitetural, funcional, visual e de produto.

---

## Passo 1 — Coletar contexto do projeto

Execute em paralelo para explorar o ecossistema completo:

```bash
# Estrutura do projeto
find . -maxdepth 3 -not -path '*/.git/*' -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' -not -path '*/.next/*' -not -path '*/dist/*' \
  | sort

# Stack e dependências
cat package.json 2>/dev/null
cat pyproject.toml 2>/dev/null
cat requirements.txt 2>/dev/null
cat Cargo.toml 2>/dev/null
cat go.mod 2>/dev/null
cat pom.xml 2>/dev/null
cat Gemfile 2>/dev/null

# Infraestrutura
cat docker-compose.yml 2>/dev/null
cat Dockerfile 2>/dev/null
ls .github/workflows/ 2>/dev/null
cat vercel.json 2>/dev/null
cat fly.toml 2>/dev/null

# Git history
git log --oneline -30 2>/dev/null
git log --stat --since="90 days ago" --oneline 2>/dev/null | head -50

# Testes
find . -name "*.test.*" -o -name "*.spec.*" -o -name "*_test.*" \
  -not -path '*/node_modules/*' 2>/dev/null | head -20
ls tests/ 2>/dev/null
ls __tests__/ 2>/dev/null

# README e docs
cat README.md 2>/dev/null | head -80
ls docs/ 2>/dev/null
```

Leia também:
1. Memória do projeto em `~/.claude/projects/.../memory/` — especialmente `project_overview.md`
2. Vault SecondBrain — `*SecondBrain/*Visão Geral*.md` se existir
3. Os arquivos mais importantes de cada camada (entry points, controllers, componentes principais)

Não leia tudo — leia o suficiente para entender cada dimensão. Vá a fundo nos arquivos que parecerem problemáticos.

---

## Passo 2 — Explorar cada camada

Com base na stack detectada no Passo 1, explore as camadas relevantes:

**Backend (se houver):** entry points, rotas, controllers, serviços, middlewares, autenticação, validação, tratamento de erros.

**Frontend (se houver):** estrutura de componentes, estado global, roteamento, chamadas de API, performance, responsividade.

**Banco de dados (se houver):** schema, migrations, queries, índices, relacionamentos.

**Infraestrutura:** CI/CD, deploy, variáveis de ambiente, secrets, monitoramento.

**Segurança:** exposição de dados sensíveis, validação de entrada, autenticação, dependências vulneráveis.

Adapte ao que o projeto tem. Um projeto CLI não tem frontend; um script Python não tem banco de dados. Seja honesto sobre o que consegue avaliar pelo código.

---

## Passo 3 — Gerar o relatório de análise

Escreva o relatório completo seguindo esta estrutura exata:

---

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

---

## Passo 4 — Padrões de qualidade da análise

Antes de escrever, verifique mentalmente:

- **Seja específico:** cite nomes de arquivo, função ou linha quando apontar um problema. "O arquivo `src/auth/middleware.js` não valida o token de expiração" é útil. "A autenticação tem problemas" não é.
- **Seja calibrado:** separe riscos críticos de problemas de estilo. Não trate tudo como urgente.
- **Seja honesto sobre incerteza:** se não conseguiu avaliar uma dimensão pelo código, diga explicitamente o que ficou fora do escopo.
- **Seja acionável:** cada problema deve ter uma direção de solução. Crítica sem sugestão não ajuda.
- **Seja justo:** reconheça o que está funcionando bem antes de criticar. Projetos sempre têm pontos fortes reais.
- **Evite o genérico:** observações que se aplicariam a qualquer projeto são ruído. Cada achado deve ser fundamentado em algo que você realmente encontrou.

---

## Passo 5 — Gerar o arquivo de contexto geral (obrigatório)

**Sempre gere este arquivo após o relatório — sem precisar perguntar ao usuário.**

Salve em `PROJECT_CONTEXT.md` na raiz do projeto. Este arquivo é lido pelo Claude no início de cada sessão para recuperar contexto sem re-analisar o projeto inteiro.

O arquivo deve ser **denso e conciso** — não é um resumo do relatório, é um mapa de contexto para o Claude operar com autonomia. Escreva pensando em alguém que vai ler isso em 30 segundos e sair codando.

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
| Análise completa | `{NomeProjeto}SecondBrain/análise/Análise Completa — {data}.md` |
```

Confirme após salvar:
```
✓ PROJECT_CONTEXT.md criado/atualizado na raiz do projeto.
  Claude lerá este arquivo automaticamente no início das próximas sessões.
```

---

## Passo 6 — Salvar análise completa no vault (opcional)

Pergunte ao usuário:
> "Quer salvar a análise completa no vault do SecondBrain também?"

Se sim:

```bash
ls *SecondBrain/ 2>/dev/null
```

Salve em:
- `{NomeProjeto}SecondBrain/análise/Análise Completa — {data}.md`
- Se a pasta `análise/` não existir, crie-a.

Confirme:
```
✓ Análise completa salva em: {caminho completo}
```

Se o usuário quiser usar como base para o documento de **Visão Geral do Produto**, ofereça:
> "Posso usar esta análise para gerar ou atualizar o documento de Visão Geral do projeto (`{NomeProjeto} — Visão Geral.md`). Quer que eu faça isso?"
